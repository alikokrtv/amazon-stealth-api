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

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Title
        title_elem = soup.find("span", {"id": "productTitle"})
        title = title_elem.get_text(strip=True) if title_elem else None

        # 2. Price extraction (Current price)
        price = None
        price_whole = soup.find("span", class_="a-price-whole")
        price_fraction = soup.find("span", class_="a-price-fraction")
        if price_whole:
            whole = price_whole.get_text(strip=True).replace(".", "").replace(",", "")
            frac = price_fraction.get_text(strip=True) if price_fraction else "00"
            price = float(f"{whole}.{frac}")
        else:
            offscreen = soup.find("span", class_="a-offscreen")
            if offscreen:
                price_match = re.search(r'[\$]?([0-9,]+\.[0-9]{2})', offscreen.get_text(strip=True))
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

        # 3. Original / List Price & Discount
        original_price = None
        list_price_elem = soup.find("span", class_="basisPrice") or soup.find("span", class_="a-price a-text-price")
        if list_price_elem:
            off_span = list_price_elem.find("span", class_="a-offscreen")
            if off_span:
                lp_match = re.search(r'[\$]?([0-9,]+\.[0-9]{2})', off_span.get_text(strip=True))
                if lp_match:
                    original_price = float(lp_match.group(1).replace(",", ""))

        # 4. Availability
        avail_elem = soup.find("div", {"id": "availability"})
        availability = "In Stock"
        if avail_elem:
            avail_text = avail_elem.get_text(strip=True)
            if avail_text:
                availability = avail_text
        
        if price is None and "See All Buying Options" in html:
            availability = "Available from other sellers"

        # 5. Rating & Reviews Count
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

        # 6. Sales Volume (e.g. "1K+ bought in past month")
        sales_volume = None
        bought_match = re.search(r'([0-9Kk\+]+ bought in past month)', html)
        if bought_match:
            sales_volume = bought_match.group(1)

        # 7. Brand
        brand_elem = soup.find("a", {"id": "bylineInfo"})
        brand = brand_elem.get_text(strip=True).replace("Brand: ", "").replace("Visit the ", "") if brand_elem else None

        # 8. Primary Image & Full Photo Gallery
        img_elem = soup.find("img", {"id": "landingImage"})
        image_url = img_elem.get("src") if img_elem else None

        # Extract all high-res photos from scripts and attributes
        hires_matches = re.findall(r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
        large_matches = re.findall(r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
        photos_found = hires_matches if hires_matches else large_matches
        product_photos = list(dict.fromkeys(photos_found)) if photos_found else ([image_url] if image_url else [])

        # 9. Bullet Points (About Product)
        about_product = [
            li.get_text(strip=True)
            for li in soup.select("#feature-bullets ul li span.a-list-item")
            if li.get_text(strip=True) and not li.get_text(strip=True).startswith("Make sure this fits")
        ]

        # 10. Product Description
        desc_elem = soup.find("div", {"id": "productDescription"})
        product_description = desc_elem.get_text(strip=True) if desc_elem else None

        # 11. Specifications & Technical Details
        product_information = {}
        for tr in soup.select("#productDetails_techSpec_section_1 tr, #prodDetails tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td:
                k = th.get_text(strip=True).replace("\n", "").replace("\u200e", "").strip()
                v = td.get_text(strip=True).replace("\n", "").replace("\u200e", "").strip()
                if k and v:
                    product_information[k] = v

        for li in soup.select("#detailBullets_feature_div ul li"):
            text = li.get_text(strip=True).replace("\u200e", "")
            if ":" in text:
                parts = text.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                if k and v:
                    product_information[k] = v

        # 12. Best Sellers Rank (BSR)
        best_sellers_rank = product_information.get("Best Sellers Rank")

        # 13. Badges
        is_best_seller = bool(soup.find(class_=re.compile(r'badge-wrapper|best-seller')) or "Best Seller" in html[:15000])
        is_amazon_choice = bool(soup.find(class_=re.compile(r'amazons-choice|ac-badge-wrapper')) or "Amazon's Choice" in html[:15000])
        is_prime = bool(soup.find("i", class_=re.compile(r'a-icon-prime')) or "a-icon-prime" in html)

        return {
            "success": True,
            "asin": asin,
            "title": title,
            "price": price,
            "original_price": original_price,
            "currency": "USD",
            "availability": availability,
            "rating": rating,
            "reviews_count": reviews_count,
            "sales_volume": sales_volume,
            "brand": brand,
            "image_url": image_url,
            "product_photos": product_photos,
            "about_product": about_product,
            "product_description": product_description,
            "product_information": product_information,
            "best_sellers_rank": best_sellers_rank,
            "is_prime": is_prime,
            "is_best_seller": is_best_seller,
            "is_amazon_choice": is_amazon_choice,
            "product_url": url,
            "zip_code": self.zip_code,
            "timestamp": int(time.time())
        }
