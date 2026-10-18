/**
 * PriceDrop Tracker — API client for the dashboard.
 */
'use strict';

const API = {
  // Dashboard disajikan oleh backend yang sama (/dashboard), jadi pakai origin yang sama.
  // Jika file dibuka langsung dari disk (file://), fallback ke localhost.
  base: window.location.protocol.startsWith('http') ? window.location.origin : 'http://localhost:8000',

  async request(path, options = {}) {
    const res = await fetch(`${this.base}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

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
    window.open(`${this.base}/api/products/export/csv`, '_blank');
  },
};
