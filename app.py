from flask import Flask, request, jsonify, abort
import requests
from bs4 import BeautifulSoup
import time
import json
import aiofiles
import asyncio
import jwt
from flask_caching import Cache
from functools import wraps
import scrapper

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

cache = Cache(app)

# Static token for authentication
API_TOKEN = "Navdeep"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token or token != API_TOKEN:
            abort(401, 'Token is missing or invalid')
        return f(*args, **kwargs)
    return decorated

BASE_URL = "https://dentalstall.com/shop/"  # Example URL

class Scraper:
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def fetch_page(self, url, proxy=None):
        for attempt in range(self.max_retries):
            try:
                if proxy:
                    response = requests.get(url, proxies={"http": proxy, "https": proxy})
                else:
                    response = requests.get(url)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise e

    def scrape_product_data(self, page_number, proxy=None):
        url = f"{BASE_URL}"
        page_content = self.fetch_page(url, proxy)
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # Debug: Print the fetched HTML content
        print(soup.prettify())

        products = []
        product_containers = soup.select('li.product')
        
        # Debug: Print the number of product containers found
        print(f"Found {len(product_containers)} products on the page.")

        for product in product_containers:

            title_elem = product.select_one('.woo-loop-product__title a')
            price_elem = product.select_one('.price')
            image_elem = product.select_one('.mf-product-thumbnail img')
            
            # Debug: Print product details if found
            if title_elem:
                print(f"Title: {title_elem.text.strip()}")
            if price_elem:
                print(f"Price: {price_elem.text.strip()}")
            
            image_url = None
            if image_elem:
                image_url = image_elem.get('data-lazy-src') or image_elem.get('src')
                print(f"Image URL: {image_url}")
            image_path=scrapper.Scraper.download_image(image_url)

            if title_elem and price_elem and image_url:
                title = title_elem.text.strip()
                price = price_elem.text.strip()
                if "Starting at:" in price:
                    price=price.split(' ')[2][1:]
                else:
                    price=price.split('.')[0][1:]
                
                product_data = {
                    "product_title": title,
                    "product_price": price,
                    "image_url": image_path
                }

                # Debug: Print the product data to be added
                print(f"Adding product: {product_data}")
                
                products.append(product_data)
        
        # Debug: Print the number of products scraped
        print(f"Scraped {len(products)} products.")
        
        return products




class Storage:
    def __init__(self, filepath='products.json'):
        self.filepath = filepath

    async def save_data(self, data):
        try:
            async with aiofiles.open(self.filepath, 'w') as file:
                await file.write(json.dumps(data, indent=4))
            print(f"Data saved to {self.filepath}")
        except Exception as e:
            print(f"Failed to save data: {e}")

# Initialize storage and notifier
storage = Storage()


@app.route('/scrape', methods=['POST'])
@token_required
def scrape():
    data = request.get_json()
    pages_limit = data.get('pages_limit', 1)
    proxy = data.get('proxy')

    all_products = []
    for page in range(1, pages_limit + 1):
        try:
            scraper = Scraper()
            products = scraper.scrape_product_data(page, proxy)
            all_products.extend(products)
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    # Save data to local storage
    asyncio.run(storage.save_data(all_products))

    # Notify about the scraping status
    print(f"Scraped and saved {len(all_products)} products")
    
    return jsonify({"response":all_products ,"message": f"Scraped and saved {len(all_products)} products"}), 200

if __name__ == '__main__':
    app.run(debug=True)
