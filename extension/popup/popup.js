/**
 * PriceDrop Tracker — popup logic
 */
'use strict';

const $ = (sel) => document.querySelector(sel);
const listEl = $('#list');
const emptyEl = $('#empty');
const errorEl = $('#error');
const errorText = $('#error-text');
const statusEl = $('#backend-status');

function send(msg) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(msg, (res) => {
      void chrome.runtime.lastError;
      resolve(res);
    });
  });
}

function fmtRp(n) {
  if (n == null) return 'Rp —';
  return 'Rp ' + Math.round(n).toLocaleString('id-ID');
}

function esc(s) {
  const div = document.createElement('div');
  div.textContent = s == null ? '' : String(s);
  return div.innerHTML;
}

function drawSparkline(canvas, history) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);

  const prices = history.map((p) => p.price).filter((p) => p != null);
  if (prices.length < 2) {
    ctx.fillStyle = '#64748b';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Belum cukup data', w / 2, h / 2 + 3);
    return;
  }

  const min = Math.min(...prices), max = Math.max(...prices);
  const range = max - min || 1;
  const pad = 6;

  // area gradient
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, 'rgba(16,185,129,.35)');
  grad.addColorStop(1, 'rgba(16,185,129,0)');

  ctx.beginPath();
  prices.forEach((p, i) => {
    const x = pad + (i / (prices.length - 1)) * (w - pad * 2);
    const y = h - pad - ((p - min) / range) * (h - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  const lastX = pad + (w - pad * 2), lastY = h - pad - ((prices[prices.length - 1] - min) / range) * (h - pad * 2);
  ctx.lineTo(lastX, h - pad);
  ctx.lineTo(pad, h - pad);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // line
  ctx.beginPath();
  prices.forEach((p, i) => {
    const x = pad + (i / (prices.length - 1)) * (w - pad * 2);
    const y = h - pad - ((p - min) / range) * (h - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 1.8;
  ctx.lineJoin = 'round';
  ctx.stroke();
}

function productCard(p) {
  const card = document.createElement('div');
  card.className = 'card';

  const dropPct = p.min_price != null && p.current_price != null && p.min_price > 0
    ? Math.round(((p.current_price - p.min_price) / p.min_price) * 100)
    : 0;
  const isDrop = dropPct < 0;
  const dropLabel = isDrop ? `▼ ${Math.abs(dropPct)}% dari min` : `▲ ${dropPct}% dari min`;

  const targetBadge = p.target_price != null
    ? `<span class="target-badge ${p.target_reached ? 'reached' : ''}">🎯 ${p.target_reached ? 'tercapai' : fmtRp(p.target_price)}</span>`
    : '';

  const updated = p.updated_at ? new Date(p.updated_at.replace(' ', 'T')) : null;
  const updatedLabel = updated && !isNaN(updated)
    ? 'Update terakhir: ' + updated.toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' })
    : '';

  card.innerHTML = `
    <div class="card-top">
      ${p.image ? `<img class="thumb" src="${esc(p.image)}" alt="" />` : `<div class="thumb"></div>`}
      <div class="card-body">
        <span class="market ${esc(p.marketplace)}">${esc(p.marketplace)}</span>
        <div class="card-name">${esc(p.name)}</div>
        <div class="prices">
          <span class="now-price">${fmtRp(p.current_price)}</span>
          <span class="min-price">min ${fmtRp(p.min_price)}</span>
          <span class="drop-badge ${isDrop ? 'drop' : ''}">${dropLabel}</span>
        </div>
      </div>
    </div>
    <div class="card-actions">
      <button class="mini-btn" data-action="history" data-id="${p.id}">Riwayat harga</button>
      <button class="mini-btn" data-action="target" data-id="${p.id}">${p.target_price != null ? 'Ubah target' : 'Set target'}</button>
      <button class="mini-btn primary" data-action="affiliate" data-id="${p.id}">Link affiliate</button>
    </div>
    <div class="card-actions">
      <button class="mini-btn" data-action="copy-url" data-id="${p.id}">Salin URL</button>
      ${updatedLabel ? `<span class="updated-at">${esc(updatedLabel)}</span>` : ''}
    </div>
    <div class="card-actions danger-row">
      <button class="mini-btn danger" data-action="archive" data-id="${p.id}">Arsipkan</button>
      <button class="mini-btn danger" data-action="delete" data-id="${p.id}">Hapus</button>
    </div>
    <div class="history" id="history-${p.id}">
      <canvas></canvas>
      <div class="history-caption"></div>
    </div>
  `;

  if (p.target_price != null) {
    const nameEl = card.querySelector('.card-name');
    nameEl.insertAdjacentHTML('beforeend', targetBadge);
  }

  card.querySelector('[data-action="history"]').addEventListener('click', async (e) => {
    const box = card.querySelector('.history');
    box.classList.toggle('open');
    if (box.classList.contains('open')) {
      e.target.textContent = 'Memuat…';
      const res = await send({ type: 'PRODUCT_HISTORY', payload: { id: p.id } });
      e.target.textContent = 'Riwayat harga';
      if (res && res.history && res.history.length) {
        drawSparkline(box.querySelector('canvas'), res.history);
        const last = res.history[res.history.length - 1];
        const first = res.history[0];
        box.querySelector('.history-caption').textContent =
          `${first.date} → ${last.date} · ${res.history.length} titik harga`;
      } else {
        box.querySelector('.history-caption').textContent = 'Belum ada data riwayat';
      }
    }
  });

  card.querySelector('.card-name').addEventListener('click', async () => {
    const s = await send({ type: 'GET_SETTINGS' });
    if (s && s.settings && s.settings.openProduct !== false) {
      chrome.tabs.create({ url: p.url });
    }
  });

  card.querySelector('[data-action="target"]').addEventListener('click', () => {
    openTargetDialog(p);
  });

  card.querySelector('[data-action="archive"]').addEventListener('click', async (e) => {
    if (!confirm('Arsipkan produk ini? Produk tidak akan muncul di daftar.')) return;
    e.target.textContent = '…';
    const res = await send({ type: 'ARCHIVE_PRODUCT', payload: { id: p.id } });
    if (res && res.ok) loadProducts($('#search-input').value, $('#market-filter').value);
    else e.target.textContent = 'Gagal';
  });

  card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
    if (!confirm('Hapus produk ini PERMANEN beserta riwayat harganya?')) return;
    e.target.textContent = '…';
    const res = await send({ type: 'DELETE_PRODUCT', payload: { id: p.id } });
    if (res && res.ok) loadProducts($('#search-input').value, $('#market-filter').value);
    else e.target.textContent = 'Gagal';
  });

  card.querySelector('[data-action="copy-url"]').addEventListener('click', async (e) => {
    await navigator.clipboard.writeText(p.url);
    const old = e.target.textContent;
    e.target.textContent = '✓ Disalin!';
    setTimeout(() => { e.target.textContent = old; }, 1200);
  });

  card.querySelector('[data-action="affiliate"]').addEventListener('click', async (e) => {
    e.target.textContent = 'Membuat…';
    const res = await send({ type: 'GET_AFFILIATE', payload: { id: p.id } });
    e.target.textContent = 'Link affiliate';
    if (res && res.link && res.link.url) {
      await navigator.clipboard.writeText(res.link.url);
      const old = e.target.textContent;
      e.target.textContent = '✓ Disalin!';
      setTimeout(() => { e.target.textContent = old; }, 1500);
    } else {
      const old = e.target.textContent;
      e.target.textContent = 'Gagal';
      setTimeout(() => { e.target.textContent = old; }, 1500);
    }
  });

  return card;
}

async function loadProducts(query, marketplace) {
  listEl.innerHTML = '<div class="spinner"></div>';
  errorEl.classList.add('hidden');
  emptyEl.classList.add('hidden');

  const q = (query || '').trim();
  const res = await send({
    type: 'LIST_PRODUCTS',
    payload: { search: q, marketplace: marketplace || '' },
  });
  if (!res || res.error) {
    listEl.innerHTML = '';
    errorText.textContent = res && res.error
      ? `Backend tidak merespons: ${res.error.slice(0, 120)}`
      : 'Gagal terhubung ke backend. Pastikan sudah dijalankan di localhost:8000.';
    errorEl.classList.remove('hidden');
    statusEl.textContent = 'offline';
    statusEl.className = 'status-chip offline';
    return;
  }

  statusEl.textContent = 'online';
  statusEl.className = 'status-chip online';

  let products = res.products || [];
  if (!products.length) {
    emptyEl.classList.remove('hidden');
    const sub = document.querySelector('.empty-sub');
    if (sub) {
      sub.textContent = q || ($('#market-filter').value)
        ? 'Tidak ada produk yang cocok dengan filter ini. Coba kata kunci lain.'
        : 'Buka halaman produk di Shopee atau TikTok Shop, lalu klik tombol "Track price".';
    }
    listEl.innerHTML = '';
    return;
  }
  emptyEl.classList.add('hidden');
  listEl.innerHTML = '';
  products = sortProducts(products, $('#sort-select').value);
  products.forEach((p) => listEl.appendChild(productCard(p)));
}

function sortProducts(products, mode) {
  const arr = [...products];
  switch (mode) {
    case 'price':
      return arr.sort((a, b) => (b.current_price || 0) - (a.current_price || 0));
    case 'price_asc':
      return arr.sort((a, b) => (a.current_price || 0) - (b.current_price || 0));
    case 'drop': {
      const dropOf = (p) => p.min_price && p.min_price > 0
        ? ((p.min_price - (p.current_price || p.min_price)) / p.min_price)
        : 0;
      return arr.sort((a, b) => dropOf(b) - dropOf(a));
    }
    default:
      return arr.sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')));
  }
}

// ---- Target price dialog ----
const targetDialog = $('#target-dialog');
const targetInput = $('#target-input');
const targetProductId = $('#target-product-id');

function openTargetDialog(product) {
  targetProductId.value = product.id;
  targetInput.value = product.target_price != null ? product.target_price : '';
  targetDialog.showModal();
  targetInput.focus();
  targetInput.select();
}

$('#target-save').addEventListener('click', async () => {
  const id = Number(targetProductId.value);
  const value = Number(targetInput.value);
  if (!value || value <= 0) {
    targetInput.style.borderColor = 'var(--red)';
    return;
  }
  targetInput.style.borderColor = '';
  const res = await send({ type: 'SET_TARGET', payload: { id, target_price: value } });
  if (res && res.product) {
    targetDialog.close();
    loadProducts($('#search-input').value, $('#market-filter').value);
  }
});

// ---- Theme ----
$('#theme-btn').addEventListener('click', () => {
  const isLight = document.body.classList.toggle('light');
  chrome.storage.local.set({ lightTheme: isLight });
  $('#theme-btn').textContent = isLight ? '☀' : '☾';
});
chrome.storage.local.get({ lightTheme: false }, (items) => {
  if (items.lightTheme) {
    document.body.classList.add('light');
    $('#theme-btn').textContent = '☀';
  }
});

// ---- Export ----
$('#export-btn').addEventListener('click', async () => {
  const s = await send({ type: 'GET_SETTINGS' });
  const url = (s && s.settings && s.settings.backendUrl) || 'http://localhost:8000';
  chrome.tabs.create({ url: url + '/api/products/export/csv' });
});

// ---- Search & filter ----
let searchTimer = null;
$('#search-input').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  searchTimer = setTimeout(() => loadProducts(q, $('#market-filter').value), 250);
});
$('#market-filter').addEventListener('change', () => {
  loadProducts($('#search-input').value, $('#market-filter').value);
});
$('#sort-select').addEventListener('change', () => {
  loadProducts($('#search-input').value, $('#market-filter').value);
});

$('#settings-btn').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// Keyboard shortcut: '/' focuses search
document.addEventListener('keydown', (e) => {
  if (e.key === '/' && document.activeElement !== $('#search-input')) {
    e.preventDefault();
    $('#search-input').focus();
  }
});

// First-run onboarding
chrome.storage.local.get({ seenOnboarding: false }, (items) => {
  if (!items.seenOnboarding) {
    $('#onboarding').classList.remove('hidden');
  }
});
$('#onboarding-ok').addEventListener('click', () => {
  chrome.storage.local.set({ seenOnboarding: true });
  $('#onboarding').classList.add('hidden');
});

$('#refresh-btn').addEventListener('click', () => loadProducts($('#search-input').value, $('#market-filter').value));
$('#retry-btn').addEventListener('click', () => loadProducts($('#search-input').value, $('#market-filter').value));
$('#open-backend').addEventListener('click', async () => {
  const res = await send({ type: 'GET_SETTINGS' });
  const url = (res && res.settings && res.settings.backendUrl) || 'http://localhost:8000';
  chrome.tabs.create({ url: url + '/docs' });
});

loadProducts('', $('#market-filter').value);
