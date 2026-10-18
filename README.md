# PriceDrop Tracker

> [Bahasa Indonesia](README-id.md)

Track product prices on Shopee and TikTok Shop, get notified when the price drops, and generate affiliate links — all from a Chrome extension backed by a small API.

## Why

Marketplace prices move constantly, especially during flash sales. Instead of refreshing product pages every day, let a browser extension record the price every time you open a product page, then get a Telegram alert the moment it falls below the lowest price you have seen.

## Features

- Chrome extension (Manifest V3) that reads the current price directly from the page you are viewing — no server-side scraping, which keeps it safe from anti-bot protections
- Works on Shopee product pages and TikTok Shop product pages
- One-click tracking with a floating widget on every product page
- Price history stored per product, with a sparkline chart in the popup and a web dashboard
- Price drop detection: alert when the price falls more than a configurable threshold below the all-time minimum
- Price targets per product with reached-target notifications
- Telegram bot with `/track`, `/list`, `/search`, `/target`, `/stats`, `/price`, `/history`, `/note`, `/archive`, `/restore`, `/prune`, and `/untrack` commands, plus inline menu and Indonesian aliases
- Affiliate link generation through the official Shopee AMS Open API and TikTok Shop Partner API (falls back to the original URL when credentials are not configured)
- Product search, marketplace filters, sorting, price targets, notes, archive (soft delete), CSV/JSON export, and a web dashboard at `/dashboard` with price charts
- Background price re-checker, optional API-key auth, rate limiting with response headers, and structured logging
- Per-product notification cooldown and retry-with-backoff for Telegram alerts
- Bilingual docs: [English](README.md) and [Bahasa Indonesia](README-id.md)

## Architecture

```
Chrome extension  ──►  FastAPI backend  ──►  SQLite
 (reads price)          (history, drops)     (products + price history)
        │                       │
        │                       └──► Telegram bot (drop alerts)
        └──► popup: list, sparkline, affiliate link
```

## Project layout

```
price-drop-tracker/
├── extension/          Chrome extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js   API bridge + message handling
│   ├── content/        content scripts (shopee.js, tiktok.js)
│   └── popup/          extension popup UI
├── backend/            FastAPI application
│   ├── app/
│   │   ├── main.py     app entrypoint
│   │   ├── routers/    product & price endpoints
│   │   └── services/   drop detector, notifier, affiliate clients
│   └── requirements.txt
└── bot/                Telegram bot
    ├── bot.py
    └── requirements.txt
```

## Getting started

### 1. Run the backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # optional: add Telegram + affiliate credentials
uvicorn app.main:app --port 8000
```

The API is now available at `http://localhost:8000` with interactive docs at `/docs`.

### 2. Load the extension

1. Open `chrome://extensions`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked" and select the `extension/` folder

Open any product page on Shopee or TikTok Shop. A "Track price" button appears bottom-right — click it to start tracking.

### 3. Set up Telegram alerts (optional)

Create a bot with [@BotFather](https://t.me/BotFather), then in `backend/.env`:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

When a tracked price drops below the previous minimum by more than `DROP_THRESHOLD_PCT` (default 5), the bot sends an alert.

To run the interactive bot:

```bash
cd bot
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=your_bot_token python bot.py
```

### 4. Enable affiliate links (optional)

**Shopee:** register at the [Shopee Affiliate Program](https://affiliate.shopee.co.id), apply for Open Platform access, then set in `backend/.env`:

```
SHOPEE_APP_ID=...
SHOPEE_APP_SECRET=...
SHOPEE_PARTNER_ID=...
```

**TikTok Shop:** register as an affiliate app developer at the [TikTok Shop Partner Center](https://partner.tiktokshop.com), then set:

```
TIKTOK_APP_KEY=...
TIKTOK_APP_SECRET=...
TIKTOK_SHOP_ID=...
```

Without credentials, the "Link affiliate" button returns the original product URL.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/products` | Create/update a product, record a price point, detect drops |
| GET | `/api/products` | List tracked products (search, filter, pagination) |
| GET | `/api/products/{id}` | Get one product |
| GET | `/api/products/{id}/history` | Price history (with limit) |
| GET | `/api/products/{id}/summary` | Min/max/avg/count of history |
| PUT | `/api/products/{id}/target` | Set target price |
| DELETE | `/api/products/{id}/target` | Clear target price |
| PUT | `/api/products/{id}/note` | Attach a note to a product |
| POST | `/api/products/{id}/affiliate` | Generate an affiliate link |
| POST | `/api/products/{id}/archive` | Archive a product (soft delete) |
| POST | `/api/products/{id}/restore` | Restore an archived product |
| POST | `/api/products/prune` | Prune old price history |
| GET | `/api/stats` | Aggregate tracking statistics |
| GET | `/api/products/export/{fmt}` | Export active products (CSV/JSON) |
| DELETE | `/api/products/{id}` | Permanently delete a product |
| GET | `/health` | Health check with version and uptime |

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full plan — PostgreSQL migration, velocity alerts, multi-marketplace support, PWA dashboard, and more.

## License

MIT
