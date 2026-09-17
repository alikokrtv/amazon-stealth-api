from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from engine import AmazonStealthEngine

app = FastAPI(
    title="Amazon Stealth Live Product & Price API",
    description="High-speed real-time Amazon product and price extraction bypassing bot protections via Chrome TLS impersonation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = AmazonStealthEngine(zip_code="10001")

@app.get("/health")
def health():
    return {"status": "ok", "service": "amazon-stealth-api"}

@app.get("/api/product/{asin_or_url:path}")
def get_product(asin_or_url: str, zip_code: str = Query("10001", description="US delivery zip code")):
    try:
        if zip_code != engine.zip_code:
            engine.zip_code = zip_code
            engine._zip_initialized = False
        data = engine.get_product(asin_or_url)
        if not data.get("success"):
            raise HTTPException(status_code=400, detail=data.get("error", "Failed to fetch product"))
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def playground():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Amazon Stealth API - Live Playground</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: #0b0f19;
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            width: 100%;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 6px 14px;
            border-radius: 9999px;
            margin-bottom: 12px;
        }
        h1 {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        p.subtitle {
            color: #94a3b8;
            font-size: 15px;
        }
        .search-box {
            background: #1e293b;
            padding: 10px;
            border-radius: 16px;
            display: flex;
            gap: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #334155;
            margin-bottom: 30px;
        }
        input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: white;
            font-size: 16px;
            padding: 10px 16px;
            font-family: inherit;
        }
        input::placeholder { color: #64748b; }
        button {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #0b0f19;
            border: none;
            padding: 12px 28px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover {
            transform: scale(1.02);
            filter: brightness(1.1);
        }
        .quick-tags {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-bottom: 25px;
            font-size: 13px;
        }
        .quick-tag {
            background: #1e293b;
            color: #38bdf8;
            padding: 5px 12px;
            border-radius: 8px;
            cursor: pointer;
            border: 1px solid #334155;
        }
        .card {
            display: none;
            background: #1e293b;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid #334155;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        .card-inner {
            display: flex;
            gap: 24px;
            align-items: center;
        }
        .product-img {
            width: 140px;
            height: 140px;
            object-fit: contain;
            background: white;
            border-radius: 14px;
            padding: 8px;
        }
        .details { flex: 1; }
        .product-brand {
            color: #38bdf8;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .product-title {
            font-size: 18px;
            font-weight: 700;
            line-height: 1.4;
            margin-bottom: 12px;
            color: #f1f5f9;
        }
        .price-badge {
            font-size: 26px;
            font-weight: 800;
            color: #10b981;
            margin-bottom: 8px;
        }
        .meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #94a3b8;
        }
        .json-preview {
            margin-top: 20px;
            background: #0f172a;
            padding: 16px;
            border-radius: 12px;
            font-family: monospace;
            font-size: 13px;
            color: #38bdf8;
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #1e293b;
        }
        .loader {
            display: none;
            text-align: center;
            font-size: 15px;
            color: #f59e0b;
            margin: 20px 0;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Chrome TLS Stealth Bypass Active</span>
            <h1>Amazon Real-Time Price & Data Engine</h1>
            <p class="subtitle">Bypasses Amazon Akamai/Cloudflare bot defenses without proxies. Returns live buybox price & stock.</p>
        </div>

        <div class="search-box">
            <input type="text" id="asinInput" placeholder="Enter Amazon ASIN or URL (e.g. B09B8V1LZ3)..." value="B09B8V1LZ3">
            <button onclick="fetchProduct()">Fetch Live Data</button>
        </div>

        <div class="quick-tags">
            <span style="color:#64748b; padding:5px 0;">Try these:</span>
            <span class="quick-tag" onclick="setAsin('B09B8V1LZ3')">Echo Dot (B09B8V1LZ3)</span>
            <span class="quick-tag" onclick="setAsin('B0D1XD1ZV3')">AirPods Pro 2 (B0D1XD1ZV3)</span>
            <span class="quick-tag" onclick="setAsin('B07ZPC9QD4')">AirPods Pro (B07ZPC9QD4)</span>
        </div>

        <div class="loader" id="loader">⚡ Impersonating Chrome & Fetching Live Amazon Buybox...</div>

        <div class="card" id="productCard">
            <div class="card-inner">
                <img id="pImg" class="product-img" src="" alt="Product">
                <div class="details">
                    <div class="product-brand" id="pBrand">BRAND</div>
                    <div class="product-title" id="pTitle">Product Title</div>
                    <div class="price-badge" id="pPrice">$0.00</div>
                    <div class="meta">
                        <span id="pRating">⭐ 0.0</span>
                        <span id="pReviews">💬 0 reviews</span>
                        <span id="pAvail" style="color: #38bdf8;">📦 In Stock</span>
                    </div>
                </div>
            </div>
            <pre class="json-preview" id="jsonView"></pre>
        </div>
    </div>

    <script>
        function setAsin(asin) {
            document.getElementById('asinInput').value = asin;
            fetchProduct();
        }

        async function fetchProduct() {
            const asin = document.getElementById('asinInput').value.trim();
            if(!asin) return;

            document.getElementById('loader').style.display = 'block';
            document.getElementById('productCard').style.display = 'none';

            try {
                const res = await fetch('/api/product/' + encodeURIComponent(asin));
                const data = await res.json();
                
                document.getElementById('loader').style.display = 'none';

                if(data.success) {
                    document.getElementById('productCard').style.display = 'block';
                    document.getElementById('pTitle').innerText = data.title || 'No title';
                    document.getElementById('pBrand').innerText = data.brand || 'AMAZON';
                    document.getElementById('pPrice').innerText = data.price ? '$' + data.price : data.availability;
                    document.getElementById('pImg').src = data.image_url || '';
                    document.getElementById('pRating').innerText = data.rating ? '⭐ ' + data.rating : '';
                    document.getElementById('pReviews').innerText = data.reviews_count ? '💬 ' + data.reviews_count.toLocaleString() + ' reviews' : '';
                    document.getElementById('pAvail').innerText = '📦 ' + (data.availability || 'In Stock');
                    document.getElementById('jsonView').innerText = JSON.stringify(data, null, 2);
                } else {
                    alert('Error: ' + (data.error || 'Failed to fetch'));
                }
            } catch(e) {
                document.getElementById('loader').style.display = 'none';
                alert('Request failed: ' + e);
            }
        }
    </script>
</body>
</html>
    """
