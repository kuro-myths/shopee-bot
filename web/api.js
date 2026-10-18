/**
 * PriceDrop Tracker — API client for the dashboard.
 */
'use strict';

const API = {
  // Dashboard disajikan oleh backend yang sama (/dashboard), jadi pakai origin yang sama.
  // Jika file dibuka langsung dari disk (file://), fallback ke localhost.
  base: window.location.protocol.startsWith('http') ? window.location.origin : 'http://localhost:8000',

  getKey() {
    try { return localStorage.getItem('pdt-api-key') || ''; } catch (_e) { return ''; }
  },

  setKey(key) {
    try {
      if (key) localStorage.setItem('pdt-api-key', key);
      else localStorage.removeItem('pdt-api-key');
    } catch (_e) { /* storage diblokir: abaikan */ }
  },

  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const key = this.getKey();
    if (key) headers['X-API-Key'] = key;
    let res;
    try {
      res = await fetch(`${this.base}${path}`, { ...options, headers });
    } catch (e) {
      const err = new Error('Tidak bisa terhubung ke server');
      err.kind = 'network';
      throw err;
    }
    if (!res.ok) {
      const err = new Error(`HTTP ${res.status}`);
      err.kind = res.status === 401 ? 'auth' : res.status === 429 ? 'rate' : 'http';
      err.status = res.status;
      throw err;
    }
    return res.json();
  },

  diagnostics() { return this.request('/api/diagnostics'); },

  promos(q, sources) {
    const p = new URLSearchParams({ q: q || '', sources: (sources || []).join(',') });
    return this.request(`/api/promos?${p}`);
  },

  promoStatus(usage) { return this.request(`/api/promos/status${usage ? '?usage=true' : ''}`); },

  health() { return this.request('/health'); },

  products(params = {}) {
    const qs = new URLSearchParams();
    if (params.search) qs.set('search', params.search);
    if (params.marketplace) qs.set('marketplace', params.marketplace);
    if (params.page) qs.set('page', String(params.page));
    if (params.page_size) qs.set('page_size', String(params.page_size));
    const q = qs.toString();
    return this.request(`/api/products${q ? `?${q}` : ''}`);
  },

  product(id) { return this.request(`/api/products/${id}`); },

  history(id) { return this.request(`/api/products/${id}/history`); },

  exportCsv() {
    const key = this.getKey();
    const q = key ? `?token=${encodeURIComponent(key)}` : '';
    window.open(`${this.base}/api/products/export/csv${q}`, '_blank');
  },
};
