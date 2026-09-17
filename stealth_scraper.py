import re
import json
from bs4 import BeautifulSoup
from curl_cffi import requests

def fetch_amazon_product(asin_or_url: str):
    """
    Fetches Amazon product details in real-time bypassing bot detection
    using Chrome TLS impersonation.
    """
    # Extract ASIN if URL is provided
    match = re.search(r'(?:/dp/|/gp/product/|/asin/|^)([A-Z0-9]{10})(?:[/?]|$)', asin_or_url.strip())
    asin = match.group(1) if match else asin_or_url.strip()

    url = f"https://www.amazon.com/dp/{asin}"
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # Impersonate real Chrome browser at TLS level
    response = requests.get(
        url,
        headers=headers,
        impersonate="chrome124",
        timeout=15
    )

    if response.status_code != 200:
        return {
            "success": False,
            "error": f"Amazon responded with status code {response.status_code}",
            "status_code": response.status_code,
            "asin": asin
        }

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check if captcha triggered
    if "Type the characters you see in this image" in response.text or soup.find("input", {"id": "captchacharacters"}):
        return {
            "success": False,
            "error": "Captcha encountered",
            "asin": asin
        }

    # 1. Product Title
    title_elem = soup.find("span", {"id": "productTitle"})
    title = title_elem.get_text(strip=True) if title_elem else None

    # 2. Price extraction
    price = None
    price_whole = soup.find("span", class_="a-price-whole")
    price_fraction = soup.find("span", class_="a-price-fraction")
    if price_whole:
        frac = price_fraction.get_text(strip=True) if price_fraction else "00"
        whole = price_whole.get_text(strip=True).replace(".", "").replace(",", "")
        price = f"{whole}.{frac}"
    else:
        # Fallback price selector
        offscreen_price = soup.find("span", class_="a-offscreen")
        if offscreen_price:
            price = offscreen_price.get_text(strip=True)

    # 3. Availability / Stock
    avail_elem = soup.find("div", {"id": "availability"})
    availability = avail_elem.get_text(strip=True) if avail_elem else "Unknown"

    # 4. Ratings & Review count
    rating_elem = soup.find("span", {"id": "acrPopover"})
    rating = rating_elem.get("title") if rating_elem else None
    
    review_count_elem = soup.find("span", {"id": "acrCustomerReviewText"})
    reviews_count = review_count_elem.get_text(strip=True) if review_count_elem else None

    # 5. Primary Image
    img_elem = soup.find("img", {"id": "landingImage"})
    image_url = img_elem.get("src") if img_elem else None

    # 6. Buybox Merchant / Ships from
    merchant_elem = soup.find("div", class_="tabular-buybox-container")
    ships_from = None
    sold_by = None
    if merchant_elem:
        text = merchant_elem.get_text(separator=" ", strip=True)
        ships_match = re.search(r'Ships from\s+([^\s]+)', text)
        sold_match = re.search(r'Sold by\s+([^\s]+)', text)
        if ships_match:
            ships_from = ships_match.group(1)
        if sold_match:
            sold_by = sold_match.group(1)

    return {
        "success": True,
        "asin": asin,
        "url": url,
        "title": title,
        "price": price,
        "availability": availability,
        "rating": rating,
        "reviews_count": reviews_count,
        "ships_from": ships_from,
        "sold_by": sold_by,
        "image_url": image_url
    }

if __name__ == "__main__":
    import sys
    test_asin = sys.argv[1] if len(sys.argv) > 1 else "B08N5WRWNW"  # Default AirPods or test ASIN
    print(f"[*] Querying Amazon for ASIN: {test_asin} with Stealth Engine...")
    result = fetch_amazon_product(test_asin)
    print(json.dumps(result, indent=2, ensure_ascii=False))
