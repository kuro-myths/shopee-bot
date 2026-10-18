/**
 * PriceDrop Tracker — content script for Shopee (shopee.co.id)
 *
 * Runs on product detail pages. Extracts product metadata (name, price,
 * image) directly from the page the user is already viewing, then offers
 * a "Track price" widget. Working client-side keeps the extension safe
 * from Shopee's anti-bot protections.
 */
(function () {
  'use strict';

  // Product detail URLs look like: https://shopee.co.id/<slug>-i.<shopid>.<itemid>
  const isProductPage = /^https:\/\/shopee\.co\.id\/.*-i\.\d+\.\d+/.test(location.href);
  if (!isProductPage) return;

  function metaContent(prop) {
    const el = document.querySelector(`meta[property="${prop}"], meta[name="${prop}"]`);
    return el ? (el.getAttribute('content') || '').trim() : '';
  }

  function extractTitle() {
    const og = metaContent('og:title');
    if (og && !og.includes('Shopee')) return og;
    const h1 = document.querySelector('h1');
    if (h1 && h1.textContent.trim()) return h1.textContent.trim();
    // Shopee often keeps the name in a script state; fall back to og
    return og;
  }

  function parsePrice(text) {
    if (!text) return null;
    // Handles "Rp1.234.567", "Rp 1.234.567", "1,234,567", "1234567"
    const m = String(text).replace(/\./g, '').replace(/,/g, '.').match(/(\d+(?:\.\d+)?)/);
    if (!m) return null;
    const n = parseFloat(m[1]);
    return Number.isFinite(n) && n > 0 ? n : null;
  }

  function extractPrice() {
    // Prefer structured meta when present
    const amount = metaContent('og:price:amount') || metaContent('product:price:amount');
    const parsed = parsePrice(amount);
    if (parsed) return parsed;

    // Scan elements whose class suggests a price node
    const candidates = document.querySelectorAll(
      'span[class*="price"], div[class*="price"], [class*="product-price"], [class*="ProductPrice"]'
    );
    for (const el of candidates) {
      const p = parsePrice(el.textContent);
      if (p) return p;
    }

    // Last resort: first Rp-looking number in the visible page text
    const bodyMatch = document.body.innerText.match(/Rp\s?([\d.,]+)/);
    return bodyMatch ? parsePrice(bodyMatch[1]) : null;
  }

  function extractImage() {
    return metaContent('og:image');
  }

  function extractProduct() {
    return {
      url: location.href.split('?')[0],
      name: extractTitle(),
      marketplace: 'shopee',
      image: extractImage(),
      current_price: extractPrice(),
    };
  }

  function sendToBackground(msg) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(msg, (res) => {
        void chrome.runtime.lastError; // swallow "receiving end does not exist"
        resolve(res);
      });
    });
  }

  // ---------- Widget UI ----------
  let widget = null;

  function formatPrice(n) {
    if (n == null) return 'Rp —';
    return 'Rp ' + n.toLocaleString('id-ID');
  }

  function createWidget() {
    const root = document.createElement('div');
    root.id = 'pdt-root';
    root.style.cssText = [
      'position:fixed', 'right:16px', 'bottom:16px', 'z-index:2147483647',
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif',
    ].join(';');

    const btn = document.createElement('button');
    btn.textContent = '📉 Track price';
    btn.style.cssText = [
      'background:#1a73e8', 'color:#fff', 'border:none', 'border-radius:999px',
      'padding:10px 16px', 'font-size:14px', 'font-weight:600', 'cursor:pointer',
      'box-shadow:0 4px 14px rgba(26,115,232,.35)', 'transition:transform .15s, background .15s',
    ].join(';');
    btn.addEventListener('mouseenter', () => { btn.style.transform = 'scale(1.04)'; });
    btn.addEventListener('mouseleave', () => { btn.style.transform = 'scale(1)'; });

    const card = document.createElement('div');
    card.style.cssText = [
      'position:absolute', 'right:0', 'bottom:52px', 'width:300px', 'background:#fff',
      'border:1px solid #e2e8f0', 'border-radius:12px', 'box-shadow:0 12px 32px rgba(0,0,0,.16)',
      'padding:16px', 'display:none', 'color:#0f172a', 'font-size:13px', 'line-height:1.5',
    ].join(';');

    const title = document.createElement('div');
    title.style.cssText = 'font-weight:700;font-size:14px;margin-bottom:6px;';
    title.textContent = 'PriceDrop Tracker';

    const name = document.createElement('div');
    name.style.cssText = 'color:#334155;margin-bottom:10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;';

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;';
    const price = document.createElement('div');
    price.style.cssText = 'font-size:18px;font-weight:800;color:#059669;';
    const badge = document.createElement('div');
    badge.style.cssText = 'font-size:11px;font-weight:700;padding:3px 8px;border-radius:999px;background:#f1f5f9;color:#475569;';

    const trackBtn = document.createElement('button');
    trackBtn.textContent = 'Track this product';
    trackBtn.style.cssText = [
      'width:100%', 'padding:9px 0', 'border:none', 'border-radius:8px', 'cursor:pointer',
      'background:#1a73e8', 'color:#fff', 'font-weight:700', 'font-size:13px',
      'transition:background .15s',
    ].join(';');

    const status = document.createElement('div');
    status.style.cssText = 'margin-top:10px;font-size:12px;color:#64748b;text-align:center;min-height:16px;';

    trackBtn.addEventListener('click', async () => {
      trackBtn.disabled = true;
      trackBtn.textContent = 'Tracking…';
      const product = extractProduct();
      const res = await sendToBackground({ type: 'TRACK_PRODUCT', payload: product });
      if (res && res.ok) {
        trackBtn.textContent = '✓ Tracking';
        trackBtn.style.background = '#059669';
        status.textContent = `Tracked — alert if price drops below ${formatPrice(res.min_price)}`;
      } else {
        trackBtn.textContent = 'Track this product';
        trackBtn.disabled = false;
        status.textContent = 'Failed — is the backend running on :8000?';
      }
    });

    card.append(title, name, row, trackBtn, status);
    row.append(price, badge);

    btn.addEventListener('click', () => {
      const willShow = card.style.display === 'none';
      card.style.display = willShow ? 'block' : 'none';
      if (willShow) refreshCard();
    });

    root.append(btn, card);
    return { root, name, price, badge, trackBtn, status };
  }

  async function refreshCard() {
    const product = extractProduct();
    widget.name.textContent = product.name || 'Produk (nama tidak terbaca)';
    widget.price.textContent = formatPrice(product.current_price);
    widget.badge.textContent = product.current_price ? 'Harga terdeteksi' : 'Harga tidak terbaca';

    // Ask background whether this product is already tracked (cheap, best-effort)
    const res = await sendToBackground({ type: 'IS_TRACKED', payload: { url: product.url } });
    if (res && res.tracked) {
      widget.trackBtn.textContent = '✓ Tracking';
      widget.trackBtn.style.background = '#059669';
      widget.trackBtn.disabled = true;
      widget.status.textContent = 'Produk ini sudah dipantau.';
    } else if (res && res.error) {
      widget.status.textContent = 'Backend tidak merespons — cek localhost:8000';
    }
  }

  // Wait a moment for the SPA to render price data
  setTimeout(() => {
    widget = createWidget();
    document.body.appendChild(widget.root);
  }, 1200);

  // Re-read price on SPA navigation (Shopee updates DOM without full reload)
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl && widget) {
      lastUrl = location.href;
      if (widget.root && widget.root.isConnected) refreshCard();
    }
  }).observe(document.body, { childList: true, subtree: true });
})();
