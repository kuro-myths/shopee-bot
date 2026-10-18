# PriceDrop Tracker — Chrome Extension

Manifest V3 extension that reads product prices directly from the page
you are viewing and reports them to the PriceDrop Tracker backend.

## Install (development)

1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" and select this folder

## What it does

- Injects a floating "Track price" widget on Shopee and TikTok Shop
  product pages.
- Reads the product name, image and current price from the DOM.
- Reports the price to the backend (upsert by URL), which records it
  into the price history and runs drop/target detection.
- Popup: list tracked products, sparkline history, target price, note,
  affiliate link, search, marketplace filter, sorting, CSV export,
  archive/delete, light/dark theme.
- Background: action badge with tracked count, browser notifications on
  price drops (cooldown once per product per day), periodic polling
  every 15 minutes via `chrome.alarms`.

## Files

| Path | Purpose |
| --- | --- |
| `manifest.json` | Extension manifest (v1.1.0) |
| `background.js` | Service worker: API bridge, badge, notifications, alarms |
| `content/shopee.js` | Shopee product page integration |
| `content/tiktok.js` | TikTok Shop product page integration |
| `popup/popup.html|css|js` | Popup UI |
| `popup/settings.html|js` | Options page (backend URL, API key, threshold) |

## Settings

Open the extension options (right-click the icon → Options) to configure:

- **Backend URL** — default `http://localhost:8000`
- **API key** — sent as `X-API-Key` when the backend protects its API
- **Alert threshold (%)** — drop percentage that triggers a notification
- **Open product on card click** — toggle

Use "Tes koneksi" to verify the backend is reachable before saving.

## Permissions

- `storage` — settings, notification cooldown, onboarding state
- `notifications` — price drop alerts
- `alarms` — periodic background polling
- `host_permissions` — Shopee, TikTok Shop, and the local backend
