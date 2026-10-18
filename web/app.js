/**
 * PriceDrop Tracker — dashboard logic.
 */
'use strict';

const $ = (sel) => document.querySelector(sel);

const state = { products: [], selected: null };

function fmtRp(n) {
  return n == null ? '—' : 'Rp ' + Math.round(n).toLocaleString('id-ID');
}

function esc(t) {
  return String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function setStatus(ok, label) {
  const el = $('#status');
  el.textContent = label || (ok ? 'Online' : 'Offline');
  el.className = 'status ' + (ok ? 'ok' : 'err');
}

function showBanner(msg, level) {
  const el = $('#banner');
  if (!msg) { el.hidden = true; return; }
  el.textContent = msg;
  el.className = 'banner' + (level === 'warn' ? ' warn' : '');
  el.hidden = false;
}

// Terjemahkan error API menjadi pesan yang bisa ditindaklanjuti.
function explainError(e) {
  if (e && e.kind === 'auth') return ['Server meminta API key. Buka Pengaturan, masukkan API key yang sama dengan variable API_KEY di Railway.', 'Perlu API key'];
  if (e && e.kind === 'rate') return ['Terlalu banyak permintaan (rate limit). Tunggu sebentar lalu klik Refresh.', 'Dibatasi'];
  if (e && e.kind === 'network') return ['Tidak bisa terhubung ke server. Cek status deployment di Railway (Deployments -> View logs) dan pastikan domain benar.', 'Offline'];
  return [`Server mengembalikan error (${e && e.message ? e.message : 'tidak diketahui'}). Lihat panel Diagnostik di Pengaturan atau log Railway.`, 'Error'];
}

function handleApiError(e) {
  const [msg, label] = explainError(e);
  setStatus(false, label);
  showBanner(msg);
}

async function loadHealth() {
  try {
    await API.health();
    setStatus(true);
    // /health publik; cek akses API sebenarnya (mendeteksi API key salah).
    await API.products({ page_size: 1 });
    showBanner('');
  } catch (e) {
    handleApiError(e);
  }
}

async function loadProducts() {
  const params = {
    search: $('#search').value.trim(),
    marketplace: $('#filter-market').value,
    include_archived: $('#show-archived').checked,
    page_size: 200,
  };
  try {
    const data = await API.products(params);
    state.products = data.products || [];
    renderOverview();
    renderTable();
  } catch (e) {
    handleApiError(e);
    state.products = [];
    renderOverview();
    renderTable();
  }
}

function renderOverview() {
  const grid = $('#stats-grid');
  const products = state.products;
  const total = products.length;
  const withTarget = products.filter((p) => p.target_price != null).length;
  const belowMin = products.filter(
    (p) => p.min_price != null && p.current_price != null && p.current_price < p.min_price
  ).length;
  const avgDrop = products.length
    ? products.reduce((acc, p) => {
        if (p.min_price == null || p.current_price == null || p.min_price === 0) return acc;
        return acc + ((p.min_price - p.current_price) / p.min_price) * 100;
      }, 0) / products.length
    : 0;

  const cards = [
    { label: 'Produk dipantau', value: total, sub: 'total produk' },
    { label: 'Dengan target', value: withTarget, sub: 'target harga aktif' },
    { label: 'Di bawah minimum', value: belowMin, sub: 'butuh perhatian' },
    { label: 'Rata-rata diskon', value: avgDrop.toFixed(1) + '%', sub: 'vs harga minimum' },
  ];

  grid.innerHTML = cards.map((c) => `
    <div class="stat-card">
      <div class="label">${c.label}</div>
      <div class="value">${c.value}</div>
      <div class="sub">${c.sub}</div>
    </div>
  `).join('');
}

function renderTable() {
  const body = $('#products-body');
  const products = state.products;
  if (!products.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted" style="text-align:center;padding:24px">Tidak ada produk.</td></tr>';
    return;
  }

  body.innerHTML = products.map((p) => `
    <tr data-id="${p.id}" class="${p.archived ? 'archived-row' : ''}">
      <td class="name-cell" title="${escapeHtml(p.name)}">${escapeHtml(p.name)}${p.archived ? ' <span class="arch-badge">arsip</span>' : ''}</td>
      <td><span class="mark-badge ${p.marketplace}">${escapeHtml(p.marketplace)}</span></td>
      <td class="price">${fmtRp(p.current_price)}</td>
      <td class="muted">${fmtRp(p.min_price)}</td>
      <td class="muted">${p.target_price != null ? fmtRp(p.target_price) : '—'}</td>
      <td class="muted">${(p.updated_at || '').slice(0, 16)}</td>
    </tr>
  `).join('');

  body.querySelectorAll('tr').forEach((tr) => {
    tr.addEventListener('click', () => showHistory(Number(tr.dataset.id)));
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s == null ? '' : String(s);
  return div.innerHTML;
}

async function showHistory(id) {
  state.selected = id;
  const history = await API.history(id);
  drawChart(history);
  const product = state.products.find((p) => p.id === id);
  $('#chart-empty').textContent = product ? `Riwayat harga: ${product.name}` : 'Riwayat harga';
  $('#view-history').classList.add('active');
  switchView('history');
}

function drawChart(history) {
  const chart = $('#chart');
  chart.innerHTML = '<canvas></canvas>';
  const canvas = chart.querySelector('canvas');
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 600, h = 280;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const prices = history.map((h) => h.price);
  if (prices.length < 2) {
    ctx.fillStyle = '#64748b';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Belum cukup data (minimal 2 titik harga)', w / 2, h / 2);
    return;
  }

  const min = Math.min(...prices), max = Math.max(...prices);
  const range = max - min || 1;
  const pad = 34;

  // grid lines
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad + (i / 4) * (h - pad * 2);
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(w - pad, y);
    ctx.stroke();
  }

  // area
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, 'rgba(16,185,129,.35)');
  grad.addColorStop(1, 'rgba(16,185,129,0)');
  ctx.beginPath();
  prices.forEach((p, i) => {
    const x = pad + (i / (prices.length - 1)) * (w - pad * 2);
    const y = h - pad - ((p - min) / range) * (h - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(w - pad, h - pad);
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
  ctx.lineWidth = 2;
  ctx.stroke();

  // labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(fmtRp(max), pad, pad - 8);
  ctx.fillText(fmtRp(min), pad, h - pad + 16);

  const first = history[0].date || '';
  const last = history[history.length - 1].date || '';
  ctx.fillText(first.slice(5, 16), pad, h - 6);
  ctx.fillText(last.slice(5, 16), w - pad, h - 6);
}

async function loadServerInfo() {
  try {
    const h = await API.health();
    const data = await API.products({ page_size: 1 });
    $('#server-info').innerHTML = `
      <dt>Status</dt><dd>${h.status}</dd>
      <dt>Database</dt><dd>${h.database}</dd>
      <dt>Versi API</dt><dd>${h.version || '—'}</dd>
      <dt>Uptime</dt><dd>${Math.round(h.uptime_seconds / 60)} menit</dd>
      <dt>Total produk</dt><dd>${data.total}</dd>
    `;
  } catch (e) {
    $('#server-info').innerHTML = `<dt>Status</dt><dd class="muted">${esc(explainError(e)[1])}</dd>`;
  }
}

const SRC_LABEL = { tracked: 'Dipantau', affiliate: 'Affiliate', web: 'Web' };

function safeUrl(u) {
  // hanya http(s): cegah javascript:/data: dari hasil web
  return /^https?:\/\//i.test(u || '') ? u : '';
}

function renderPromos(data) {
  const st = Object.entries(data.sources || {}).map(([k, v]) => {
    const label = SRC_LABEL[k] || k;
    if (v.status === 'ok') return `${label}: ${v.count} hasil${v.cached ? ' (cache)' : ''}`;
    return `${label}: ${v.status === 'skipped' ? 'dilewati' : 'error'} - ${v.message}`;
  });
  $('#promo-sources').innerHTML = st.map(esc).join('<br>');
  const box = $('#promo-results');
  if (!data.results.length) {
    box.innerHTML = '<div class="settings-card muted">Belum ada promo yang cocok. Coba kata kunci lain, atau pantau lebih banyak produk lewat ekstensi.</div>';
    return;
  }
  box.innerHTML = data.results.map((d) => {
    const url = safeUrl(d.url);
    const img = safeUrl(d.image);
    return `<div class="promo-card">
      ${img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}
      <div class="promo-body">
        <div class="promo-title">${esc(d.title)}</div>
        <div class="promo-meta">
          <span class="promo-src-badge">${esc(SRC_LABEL[d.source] || d.source)}</span>
          ${d.price ? `<span class="promo-price">${esc(fmtRp(d.price))}</span>` : ''}
          ${d.original_price ? `<s>${esc(fmtRp(d.original_price))}</s>` : ''}
          ${d.discount_pct != null ? `<span class="promo-off">-${esc(Math.round(d.discount_pct))}%</span>` : ''}
          ${d.commission_pct != null ? `<span>komisi ${esc(d.commission_pct)}%</span>` : ''}
          ${d.shop ? `<span>${esc(d.shop)}</span>` : ''}
        </div>
        ${d.note ? `<div class="promo-note">${esc(d.note)}</div>` : ''}
      </div>
      ${url ? `<a class="btn promo-open" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Buka</a>` : ''}
    </div>`;
  }).join('');
}

async function loadPromos() {
  const sources = [...document.querySelectorAll('.promo-src:checked')].map((c) => c.value);
  $('#promo-results').innerHTML = '<div class="settings-card muted">Mencari...</div>';
  try {
    renderPromos(await API.promos($('#promo-q').value.trim(), sources));
  } catch (e) {
    $('#promo-results').innerHTML = '';
    handleApiError(e);
  }
}

$('#promo-go').addEventListener('click', loadPromos);
$('#promo-q').addEventListener('keydown', (e) => { if (e.key === 'Enter') loadPromos(); });
$('#promo-credit').addEventListener('click', async () => {
  const out = $('#promo-credit-out');
  out.textContent = 'Memeriksa...';
  try {
    const s = await API.promoStatus(true);
    const w = s.web;
    if (!w.configured) { out.textContent = 'PILOTERR_API_KEY belum diisi di server.'; return; }
    out.textContent = w.usage_error
      ? w.usage_error
      : `Pemakaian hari ini: ${w.spent_today}/${w.daily_limit}. Akun: ${JSON.stringify(w.usage).slice(0, 160)}`;
  } catch (e) { out.textContent = explainError(e)[0]; }
});

const ICON = { ok: 'OK', info: 'INFO', warn: 'PERHATIAN', error: 'ERROR' };

async function loadDiagnostics() {
  const list = $('#diag-list');
  try {
    const d = await API.diagnostics();
    const ov = $('#diag-overall');
    ov.textContent = d.overall === 'ok' ? 'Sehat' : d.overall === 'warn' ? 'Ada peringatan' : 'Ada error';
    ov.className = 'status ' + (d.overall === 'ok' ? 'ok' : 'err');
    list.innerHTML = d.checks.map((c) => `
      <div class="diag-item">
        <div class="diag-title"><span class="diag-badge ${esc(c.status)}">${ICON[c.status] || esc(c.status)}</span>${esc(c.title)}</div>
        <div class="muted">${esc(c.detail)}</div>
        ${c.fix && (c.status === 'warn' || c.status === 'error') ? `<div class="diag-fix">Perbaikan: ${esc(c.fix)}</div>` : ''}
      </div>`).join('');
    $('#diag-errors').innerHTML = d.recent_errors.length
      ? d.recent_errors.map((e) => `<div>${esc(e.ts)} — ${esc(e.message)}</div>`).join('')
      : 'Tidak ada.';
  } catch (e) {
    list.innerHTML = `<div class="diag-item"><div class="muted">${esc(explainError(e)[0])}</div></div>`;
  }
}

function switchView(name) {
  document.querySelectorAll('.nav-btn').forEach((b) => {
    b.classList.toggle('active', b.dataset.view === name);
  });
  document.querySelectorAll('.view').forEach((v) => {
    v.classList.toggle('active', v.id === `view-${name}`);
  });
  if (name === 'settings') { loadServerInfo(); loadDiagnostics(); }
  if (name === 'promo' && !$('#promo-results').children.length) loadPromos();
  if (name === 'history' && !state.selected) {
    // auto-show first product history
    if (state.products.length) showHistory(state.products[0].id);
  }
}

document.querySelectorAll('.nav-btn').forEach((btn) => {
  btn.addEventListener('click', () => switchView(btn.dataset.view));
});

$('#refresh').addEventListener('click', () => {
  loadHealth();
  loadProducts();
  if (state.selected) showHistory(state.selected);
});

$('#export-btn').addEventListener('click', () => API.exportCsv());

$('#api-key').value = API.getKey();
$('#save-key').addEventListener('click', () => {
  API.setKey($('#api-key').value.trim());
  loadHealth();
  loadProducts();
  loadServerInfo();
  loadDiagnostics();
});
$('#diag-refresh').addEventListener('click', loadDiagnostics);

$('#theme-toggle').addEventListener('click', () => {
  document.body.classList.toggle('light');
  localStorage.setItem('pdt-theme', document.body.classList.contains('light') ? 'light' : 'dark');
});
if (localStorage.getItem('pdt-theme') === 'light') {
  document.body.classList.add('light');
}

let searchTimer = null;
$('#search').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadProducts, 250);
});
$('#filter-market').addEventListener('change', loadProducts);
$('#show-archived').addEventListener('change', loadProducts);

// init
loadHealth();
loadProducts();
