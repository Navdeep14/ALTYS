import requests
from bs4 import BeautifulSoup
import os
import json
import time
from typing import List, Optional
from pydantic import BaseModel
import redis

# Configuration for the cache
CACHE_EXPIRY = 60 * 60  # 1 hour

class Scraper:
    def __init__(self, base_url: str, proxy: Optional[str] = None):
        self.base_url = base_url
        self.proxy = proxy
        self.cache = redis.StrictRedis(host='localhost', port=6379, db=0)

    def fetch_page(self, url: str) -> Optional[str]:
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            response = requests.get(url, proxies=proxies, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_page(self, html: str) -> List[dict]:
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        for product in soup.select('.product'):  # Update selector according to the website structure
            title = product.select_one('.product-title').text.strip()
            price = float(product.select_one('.product-price').text.strip().replace('$', ''))
            img_url = product.select_one('.product-image')['src']
            img_path = self.download_image(img_url)
            products.append({
                "product_title": title,
                "product_price": price,
                "path_to_image": img_path
            })
        return products

    def download_image(url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            img_name = os.path.basename(url)
            img_path = os.path.join('images', img_name)
            os.makedirs('images', exist_ok=True)
            with open(img_path, 'wb') as f:
                f.write(response.content)
            return img_path
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return ""
        except OSError as e:
            print(f"OS error: {e}")
            return ""

    def scrape(self, limit: int = 5) -> List[dict]:
        scraped_products = []
        for page_num in range(1, limit + 1):
            page_url = f"{self.base_url}/page/{page_num}"
            html = self.fetch_page(page_url)
            if html:
                products = self.parse_page(html)
                scraped_products.extend(products)
            time.sleep(2)  # Be respectful to the server
        return scraped_products
