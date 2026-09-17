import re
import time
from bs4 import BeautifulSoup
from curl_cffi import requests

class AmazonStealthEngine:
    def __init__(self, zip_code: str = "10001"):
        self.zip_code = zip_code
        self.session = requests.Session(impersonate="chrome124")
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.session.cookies.set("i18n-prefs", "USD", domain=".amazon.com")
        self.session.cookies.set("lc-main", "en_US", domain=".amazon.com")
        self._zip_initialized = False

    def _initialize_zip(self, initial_html: str):
        """Sets the Amazon delivery zip code to ensure US Buybox prices are returned."""
        csrf_matches = re.findall(r'anti-csrftoken-a2z["&quot;:\s=]+([^"&;>\s]{20,})', initial_html)
        csrf_token = csrf_matches[0] if csrf_matches else ""

        glow_headers = {
            **self.headers,
            "anti-csrftoken-a2z": csrf_token,
            "Accept": "text/html,*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
        }
        data = {
            "locationType": "LOCATION_INPUT",
            "zipCode": self.zip_code,
            "storeContext": "generic",
            "deviceType": "web",
            "pageType": "Gateway",
            "actionSource": "glow"
        }
        try:
            self.session.post(
                "https://www.amazon.com/portal-migration/hz/glow/address-change?actionSource=glow",
                data=data,
                headers=glow_headers,
                timeout=10
            )
            self._zip_initialized = True
        except Exception:
            pass

    def get_product(self, asin_or_url: str) -> dict:
        # Extract 10-char ASIN
        match = re.search(r'(?:/dp/|/gp/product/|/asin/|^)([A-Z0-9]{10})(?:[/?]|$)', asin_or_url.strip())
        asin = match.group(1) if match else asin_or_url.strip()

        url = f"https://www.amazon.com/dp/{asin}"
        
        response = self.session.get(url, headers=self.headers, timeout=15)
        
        # Check if zip needs initializing
        if not self._zip_initialized:
            self._initialize_zip(response.text)
            # Re-fetch with active US address
            response = self.session.get(url, headers=self.headers, timeout=15)

        if response.status_code == 404:
            return {
                "success": False,
                "error": "Product not found (404)",
                "asin": asin
            }

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Amazon status code {response.status_code}",
                "asin": asin
            }

        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Title
        title_elem = soup.find("span", {"id": "productTitle"})
        title = title_elem.get_text(strip=True) if title_elem else None

        # 2. Price extraction
        price = None
        price_whole = soup.find("span", class_="a-price-whole")
        price_fraction = soup.find("span", class_="a-price-fraction")
        if price_whole:
            whole = price_whole.get_text(strip=True).replace(".", "").replace(",", "")
            frac = price_fraction.get_text(strip=True) if price_fraction else "00"
            price = float(f"{whole}.{frac}")
        else:
            # Fallback to offscreen price
            offscreen = soup.find("span", class_="a-offscreen")
            if offscreen:
                price_match = re.search(r'[\$]?([0-9,]+\.[0-9]{2})', offscreen.get_text(strip=True))
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

        # 3. Availability
        avail_elem = soup.find("div", {"id": "availability"})
        availability = "In Stock"
        if avail_elem:
            avail_text = avail_elem.get_text(strip=True)
            if avail_text:
                availability = avail_text
        
        if price is None and "See All Buying Options" in response.text:
            availability = "Available from other sellers"

        # 4. Rating & Reviews
        rating = None
        rating_elem = soup.find("span", {"id": "acrPopover"})
        if rating_elem:
            r_match = re.search(r'([0-9.]+)\s+out of', rating_elem.get("title", ""))
            if r_match:
                rating = float(r_match.group(1))

        reviews_count = None
        reviews_elem = soup.find("span", {"id": "acrCustomerReviewText"})
        if reviews_elem:
            c_match = re.search(r'([0-9,]+)', reviews_elem.get_text(strip=True))
            if c_match:
                reviews_count = int(c_match.group(1).replace(",", ""))

        # 5. Image URL
        img_elem = soup.find("img", {"id": "landingImage"})
        image_url = img_elem.get("src") if img_elem else None

        # 6. Brand
        brand_elem = soup.find("a", {"id": "bylineInfo"})
        brand = brand_elem.get_text(strip=True).replace("Brand: ", "").replace("Visit the ", "") if brand_elem else None

        return {
            "success": True,
            "asin": asin,
            "title": title,
            "price": price,
            "currency": "USD",
            "availability": availability,
            "rating": rating,
            "reviews_count": reviews_count,
            "brand": brand,
            "image_url": image_url,
            "product_url": url,
            "zip_code": self.zip_code,
            "timestamp": int(time.time())
        }
