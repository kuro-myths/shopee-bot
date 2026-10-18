#!/usr/bin/env python3
"""Smoke test + deteksi error untuk deployment (dipakai GitHub Actions).

1. Menunggu /health menjawab status "ok" (maks --timeout detik).
2. Memanggil /api/diagnostics dan menampilkan hasil + saran perbaikan.
3. Exit code 1 jika server tidak sehat atau ada pemeriksaan berstatus "error"
   (atau "warn" bila --fail-on-warn). Hanya library standar Python.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ICON = {"ok": "OK   ", "info": "INFO ", "warn": "WARN ", "error": "ERROR"}


def get(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def wait_healthy(base, timeout):
    deadline = time.time() + timeout
    last = "belum ada respons"
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            _, body = get(f"{base}/health", timeout=10)
            if body.get("status") == "ok":
                return True, body
            last = f"status={body.get('status')} database={body.get('database')}"
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
        except Exception as exc:  # DNS belum siap, koneksi ditolak, timeout...
            last = f"{type(exc).__name__}: {exc}"
        print(f"[{attempt}] menunggu server sehat... ({last})", flush=True)
        time.sleep(10)
    return False, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--api-key", default="")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--fail-on-warn", action="store_true")
    a = ap.parse_args()
    base = a.url.strip().rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base

    ok, info = wait_healthy(base, a.timeout)
    if not ok:
        msg = f"Server {base} tidak sehat setelah {a.timeout}s: {info}"
        print(f"::error::{msg}")
        summary(["## Deploy GAGAL", msg, "", "Cek Railway -> Deployments -> View logs."])
        return 1
    print(f"/health OK: {info}")

    # Dashboard harus bisa dibuka (HTML), bukan 404 JSON.
    try:
        req = urllib.request.Request(f"{base}/dashboard/", headers={"Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read(4096).decode("utf-8", "ignore")
        if "<html" not in html.lower():
            raise ValueError("respons bukan HTML")
        print("/dashboard/ OK")
    except Exception as exc:
        msg = f"/dashboard/ tidak bisa dibuka ({exc}). Pastikan Dockerfile menyalin folder web/."
        print(f"::error title=Dashboard::{msg}")
        summary(["## Deploy bermasalah", msg])
        return 1

    headers = {"X-API-Key": a.api_key} if a.api_key else {}
    try:
        _, diag = get(f"{base}/api/diagnostics", headers)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            msg = ("Server menolak API key (401). Samakan secret APP_API_KEY di GitHub "
                   "dengan variable API_KEY di Railway.")
        else:
            msg = f"/api/diagnostics mengembalikan HTTP {exc.code}"
        print(f"::error::{msg}")
        summary(["## Deploy bermasalah", msg])
        return 1
    except Exception as exc:
        print(f"::error::Gagal memanggil /api/diagnostics: {exc}")
        return 1

    rows = ["## Hasil diagnostik deploy", f"Platform: **{diag['platform']}** - status keseluruhan: **{diag['overall']}**", "",
            "| Status | Pemeriksaan | Detail |", "|---|---|---|"]
    errors = warns = 0
    for c in diag["checks"]:
        print(f"{ICON.get(c['status'], c['status'])} {c['title']}: {c['detail']}")
        rows.append(f"| {c['status']} | {c['title']} | {c['detail']} |")
        if c["status"] in ("warn", "error") and c.get("fix"):
            print(f"      Perbaikan: {c['fix']}")
            rows.append(f"| | _Perbaikan_ | {c['fix']} |")
        if c["status"] == "error":
            errors += 1
            print(f"::error title={c['title']}::{c['detail']} Perbaikan: {c.get('fix', '')}")
        elif c["status"] == "warn":
            warns += 1
            print(f"::warning title={c['title']}::{c['detail']} Perbaikan: {c.get('fix', '')}")
    for e in diag.get("recent_errors", []):
        print(f"::error title=Error server::{e['ts']} {e['message']}")
        rows.append(f"| error | Error server | {e['ts']} {e['message']} |")
    summary(rows)

    if errors or (a.fail_on_warn and warns):
        print(f"\nGAGAL: {errors} error, {warns} peringatan.")
        return 1
    print(f"\nSUKSES: 0 error, {warns} peringatan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
