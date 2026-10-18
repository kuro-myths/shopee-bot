/**
 * PriceDrop Tracker — settings page logic.
 */
'use strict';

const DEFAULTS = {
  backendUrl: 'http://localhost:8000',
  apiKey: '',
  alertThreshold: 5,
  openProduct: true,
};

function loadSettings() {
  return new Promise((resolve) => {
    chrome.storage.local.get(DEFAULTS, resolve);
  });
}

async function init() {
  const s = await loadSettings();
  document.getElementById('backend-url').value = s.backendUrl;
  document.getElementById('api-key').value = s.apiKey;
  document.getElementById('alert-threshold').value = s.alertThreshold;
  document.getElementById('open-product').checked = s.openProduct;
}

document.getElementById('save').addEventListener('click', async () => {
  const settings = {
    backendUrl: document.getElementById('backend-url').value.trim() || DEFAULTS.backendUrl,
    apiKey: document.getElementById('api-key').value.trim(),
    alertThreshold: Number(document.getElementById('alert-threshold').value) || 5,
    openProduct: document.getElementById('open-product').checked,
  };
  await chrome.storage.local.set(settings);
  const status = document.getElementById('status');
  status.textContent = 'Pengaturan disimpan.';
  setTimeout(() => { status.textContent = ''; }, 2000);
});

document.getElementById('test-conn').addEventListener('click', async () => {
  const url = document.getElementById('backend-url').value.trim() || DEFAULTS.backendUrl;
  const apiKey = document.getElementById('api-key').value.trim();
  const btn = document.getElementById('test-conn');
  const status = document.getElementById('status');
  btn.disabled = true;
  status.textContent = 'Menghubungkan…';
  try {
    const headers = {};
    if (apiKey) headers['X-API-Key'] = apiKey;
    const res = await fetch(url.replace(/\/$/, '') + '/health', { headers });
    if (res.ok) {
      const body = await res.json().catch(() => ({}));
      status.textContent = `Terhubung! (${body.status || 'ok'}, db ${body.database || '?'})`;
    } else {
      status.textContent = `Gagal: HTTP ${res.status}. Cek URL dan API key.`;
    }
  } catch (_e) {
    status.textContent = 'Tidak bisa terhubung ke backend.';
  } finally {
    btn.disabled = false;
  }
});

init();
