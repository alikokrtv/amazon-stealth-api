# ⚡ Amazon Stealth Live Product & Price Engine (API)

A high-speed, zero-proxy real-time Amazon product intelligence API built with **FastAPI** and **curl_cffi**. 

Bypasses Amazon's Akamai/Cloudflare bot protections using **Chrome TLS fingerprint impersonation**, locks in a US Delivery Zip Code (`10001` New York by default), and extracts live buybox prices, stock availability, ratings, and primary product assets in clean JSON.

---

## 🚀 Key Features

- **🛡️ Anti-Bot Stealth Engine:** Simulates authentic browser TLS handshakes (JA3/JA4) to eliminate 403 Forbidden / CAPTCHA walls without expensive residential proxy pools.
- **📍 US Buybox Lock:** Automatically sets Amazon's internal delivery zip code to `10001` (or custom), preventing "Cannot ship to your location" restrictions and showing real US domestic prices.
- **⚡ Blazing Fast:** Typically delivers results in ~1-2 seconds.
- **📊 RapidAPI / OpenAPI Ready:** Pre-configured with Swagger docs and `rapidapi_spec.json` for 1-click import.
- **🎨 Interactive Playground:** Built-in dark mode dashboard at `/` for live testing.

---

## 📦 API Response Schema

`GET /api/product/{asin_or_url}`

```json
{
  "success": true,
  "asin": "B0F8WFQFBY",
  "title": "Nautica 3 in 1 Charging Cable CB640 (12W) (A to/C-L-C) (Navy)",
  "price": 9.99,
  "currency": "USD",
  "availability": "In Stock",
  "rating": 4.6,
  "reviews_count": 1420,
  "brand": "Nautica Store",
  "image_url": "https://m.media-amazon.com/images/I/41KeC1qwnLL._SY445_SX342_QL70_FMwebp_.jpg",
  "product_url": "https://www.amazon.com/dp/B0F8WFQFBY",
  "zip_code": "10001",
  "timestamp": 1789648285
}
```

---

## 🛠️ Quickstart

### Local Setup
```bash
# Clone the repository
git clone https://github.com/alikokrtv/amazon-stealth-api.git
cd amazon-stealth-api

# Create and activate virtualenv
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) for the live playground, or [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger UI.

---

## 🚢 Deployment

### 1-Click Render / Railway
Deploy directly from this GitHub repo using the included `Procfile` or `Dockerfile`.
Port will bind automatically to the environment `$PORT`.

### RapidAPI Setup
1. Log in to [RapidAPI Provider Studio](https://rapidapi.com/studio).
2. Click **Add New API** ➡️ **Import OpenAPI Spec**.
3. Upload `rapidapi_spec.json`.
4. Point the base target URL to your deployed cloud URL.
5. Set your subscription pricing tiers (Free, $29/mo, $99/mo).
