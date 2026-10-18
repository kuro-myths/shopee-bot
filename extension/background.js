/**
 * PriceDrop Tracker — background service worker (Manifest V3)
 *
 * Bridges content scripts <-> backend API, tracks settings, shows an
 * action badge with the tracked product count, and fires browser
 * notifications when the backend reports a price drop.
 */
'use strict';

const DEFAULT_BACKEND = 'http://localhost:8000';
const DEFAULT_SETTINGS = {
  backendUrl: DEFAULT_BACKEND,
  apiKey: '',
  alertThreshold: 5,
  openProduct: true,
};

let cachedSettings = null;

function getSettings() {
  if (cachedSettings) return Promise.resolve(cachedSettings);
  return new Promise((resolve) => {
    chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
      cachedSettings = { ...DEFAULT_SETTINGS, ...items };
      resolve(cachedSettings);
    });
  });
}

function invalidateSettings() {
  cachedSettings = null;
}

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && Object.keys(changes).some((k) => k in DEFAULT_SETTINGS)) {
    invalidateSettings();
  }
});

async function api(path, options = {}) {
  const settings = await getSettings();
  const headers = { 'Content-Type': 'application/json' };
  if (settings.apiKey) headers['X-API-Key'] = settings.apiKey;

  const res = await fetch(`${settings.backendUrl}${path}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

function setBadge(count, reachedTargets = 0) {
  const text = count > 0 ? String(count) : '';
  const color = reachedTargets > 0 ? '#f59e0b' : (count > 0 ? '#10b981' : '#334155');
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
}

async function refreshBadge() {
  try {
    const data = await api('/api/products?page_size=200');
    const products = data.products || [];
    const reached = products.filter((p) => p.target_price != null && p.target_reached).length;
    setBadge(data.total || 0, reached);
  } catch (_err) {
    setBadge(0);
  }
}

const NOTIFY_COOLDOWN_MS = 24 * 60 * 60 * 1000; // once per product per day

async function notifyDrop(product) {
  if (!('notifications' in chrome)) return;

  // Cooldown: do not spam the same product every poll cycle
  const key = `last-notify-${product.id}`;
  const items = await new Promise((resolve) => chrome.storage.local.get(key, resolve));
  const last = items[key] || 0;
  if (Date.now() - last < NOTIFY_COOLDOWN_MS) return;
  await new Promise((resolve) => chrome.storage.local.set({ [key]: Date.now() }, resolve));

  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Harga turun!',
    message: `${product.name} — sekarang Rp ${Math.round(product.current_price).toLocaleString('id-ID')}`,
    priority: 2,
  });
}

async function pollAlerts() {
  try {
    const settings = await getSettings();
    const data = await api('/api/products?page_size=200');
    const products = data.products || [];
    for (const p of products) {
      if (p.min_price != null && p.current_price != null
          && p.current_price < p.min_price * (1 - settings.alertThreshold / 100)) {
        notifyDrop(p);
      }
    }
    setBadge(products.length);
  } catch (_err) {
    // backend offline; keep badge quiet
  }
}

// Periodic background polling (every 15 minutes) while Chrome runs
chrome.alarms.create('pricedrop-poll', { periodInMinutes: 15 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'pricedrop-poll') pollAlerts();
});

// Check drops from the backend by listing products with targets/drops
async function pollAlerts() {
  try {
    const settings = await getSettings();
    const data = await api('/api/products?page_size=200');
    const products = data.products || [];
    for (const p of products) {
      if (p.min_price != null && p.current_price != null
          && p.current_price < p.min_price * (1 - settings.alertThreshold / 100)) {
        notifyDrop(p);
      }
    }
    setBadge(products.length);
  } catch (_err) {
    // backend offline; keep badge quiet
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    switch (msg.type) {
      case 'TRACK_PRODUCT': {
        const p = msg.payload || {};
        const product = await api('/api/products', {
          method: 'POST',
          body: JSON.stringify({
            url: p.url,
            name: p.name || 'Untitled product',
            marketplace: p.marketplace || 'unknown',
            image: p.image || '',
            current_price: p.current_price,
          }),
        });
        refreshBadge();
        return { ok: true, id: product.id, min_price: product.min_price ?? product.current_price };
      }
      case 'IS_TRACKED': {
        const data = await api('/api/products?page_size=200');
        const products = data.products || [];
        const found = products.find((it) => it.url === msg.payload.url);
        return { tracked: Boolean(found) };
      }
      case 'LIST_PRODUCTS': {
        const payload = msg.payload || {};
        const params = new URLSearchParams({ page_size: '200' });
        if (payload.search) params.set('search', payload.search);
        if (payload.marketplace) params.set('marketplace', payload.marketplace);
        const data = await api(`/api/products?${params.toString()}`);
        return { products: data.products || [] };
      }
      case 'PRODUCT_HISTORY': {
        const history = await api(`/api/products/${msg.payload.id}/history`);
        return { history };
      }
      case 'GET_AFFILIATE': {
        const link = await api(`/api/products/${msg.payload.id}/affiliate`, { method: 'POST' });
        return { link };
      }
      case 'SET_TARGET': {
        const product = await api(`/api/products/${msg.payload.id}/target`, {
          method: 'PUT',
          body: JSON.stringify({ target_price: msg.payload.target_price }),
        });
        return { product };
      }
      case 'CLEAR_TARGET': {
        const product = await api(`/api/products/${msg.payload.id}/target`, { method: 'DELETE' });
        return { product };
      }
      case 'SET_BACKEND': {
        const url = msg.payload && msg.payload.url ? msg.payload.url : DEFAULT_BACKEND;
        await chrome.storage.local.set({ backendUrl: url });
        invalidateSettings();
        return { ok: true };
      }
      case 'DELETE_PRODUCT': {
        const res = await api(`/api/products/${msg.payload.id}`, { method: 'DELETE' });
        refreshBadge();
        return { ok: true, deleted: res.deleted };
      }
      case 'ARCHIVE_PRODUCT': {
        const res = await api(`/api/products/${msg.payload.id}/archive`, { method: 'POST' });
        refreshBadge();
        return { ok: true, archived: res.archived };
      }
      case 'GET_SETTINGS': {
        return { settings: await getSettings() };
      }
      case 'UPDATE_NOTE': {
        const product = await api(`/api/products/${msg.payload.id}/note`, {
          method: 'PUT',
          body: JSON.stringify({ note: msg.payload.note || '' }),
        });
        return { ok: true, product };
      }
      default:
        return { error: 'Unknown message type' };
    }
  })()
    .then(sendResponse)
    .catch((err) => sendResponse({ error: String(err.message || err) }));
  return true; // keep the message channel open for async response
});

// Poll alerts whenever the browser starts / extension installs
chrome.runtime.onInstalled.addListener(() => { pollAlerts(); });
chrome.runtime.onStartup.addListener(() => { pollAlerts(); });
