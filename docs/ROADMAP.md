# Roadmap

Status: version 0.3.0 (2026-08-12)

## v0.4 — Reliability & data

- [ ] Migrate from SQLite to PostgreSQL (Supabase/Railway-compatible) for
      multi-instance deployments and larger datasets.
- [ ] Store price snapshots with timezone-aware timestamps and UTC
      normalization.
- [ ] Configurable retention policies per product (instead of one global
      prune window).
- [ ] Export with date-range filter and scheduled exports (cron/webhook).

## v0.5 — Smarter alerts

- [ ] Price prediction: linear regression on recent history to flag
      "likely to drop" products before the drop happens.
- [ ] Velocity alerts: notify when a product drops X% within Y hours.
- [ ] Per-product alert rules (threshold + cooldown) instead of global
      settings.
- [ ] Digest mode: one daily Telegram message summarizing all changes
      instead of individual notifications.

## v0.6 — Ecosystem

- [ ] Official Chrome Web Store release of the extension (CI-signed CRX).
- [ ] Multi-marketplace support: Tokopedia, Blibli, Lazada via the same
      fetcher/plugin interface.
- [ ] Plugin architecture for new marketplaces (contributor-friendly).
- [ ] Public REST API with scoped API keys and usage quotas.

## v0.7 — Mobile & UX

- [ ] PWA frontend for the dashboard (offline-ready, installable).
- [ ] Push notifications via Web Push in addition to Telegram.
- [ ] Product "watchlist" folders/collections.
- [ ] i18n: full English and Indonesian UI.

## Ideas backlog

- Browser extension tracking history sync across devices.
- CSV import of wishlist products (bulk tracking).
- Shareable drop alerts (public links per product).
- Affiliate earnings dashboard with click attribution.
