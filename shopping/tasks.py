"""
This module contains Celery tasks for the shopping app.
In development, these can be called directly, but in production
they should be called asynchronously using Celery.
"""
import time
import random
import json
import logging
from typing import List, Dict, Any, Optional

from fake_useragent import UserAgent
from requests_html import HTMLSession
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

# Create a session for making HTTP requests
session = HTMLSession()
ua = UserAgent()

def get_random_delay():
    """Return a random delay between requests to avoid rate limiting"""
    return random.uniform(1, 3)

def get_headers() -> Dict[str, str]:
    """Generate random headers for requests"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
    }

def extract_product_info(product_div) -> Optional[Dict[str, Any]]:
    """Extract product information from a product div"""
    try:
        # Extract product name
        name_elem = product_div.find('h3', first=True)
        name = name_elem.text.strip() if name_elem else ""
        
        # Extract price
        price_elem = product_div.find('span[class*="price"]', first=True)
        price_text = price_elem.text.strip() if price_elem else ""
        
        # Try to extract numeric price
        price = None
        currency = 'USD'
        if price_text:
            # Simple price extraction - in a real app, you'd want more robust parsing
            import re
            price_match = re.search(r'\$?([\d,.]+)', price_text.replace(',', ''))
            if price_match:
                price = float(price_match.group(1))
                currency = 'USD'  # Default, could be extracted from price_text
        
        # Extract store
        store_elem = product_div.find('div:contains("by")', first=True)
        store = store_elem.text.replace('by', '').strip() if store_elem else None
        
        # Extract URL
        url_elem = product_div.find('a[href]', first=True)
        url = url_elem.attrs.get('href', '') if url_elem else ''
        if url and not url.startswith('http'):
            url = f'https://www.google.com{url}'
        
        # Extract image URL
        img_elem = product_div.find('img', first=True)
        image_url = img_elem.attrs.get('src', '') if img_elem else ''
        
        # Generate a unique product ID (in a real app, this would come from the source)
        product_id = f"{hash(name + str(price) + (store or '')) & 0xffffffff}"
        
        return {
            'product_id': product_id,
            'name': name,
            'price': price,
            'price_text': price_text,
            'currency': currency,
            'store': store,
            'url': url,
            'image_url': image_url,
            'weight': None,  # This would be extracted from the product name or details
            'brand': None,   # This would be extracted from the product name or details
            'rating': None,  # This would be extracted if available
            'review_count': 0,  # This would be extracted if available
        }
    except Exception as e:
        logger.error(f"Error extracting product info: {e}")
        return None

def fetch_products_from_google_shopping(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch products from Google Shopping search results.
    
    Note: In a production environment, you would want to use the official Google Shopping API
    or a third-party service. This is a basic implementation that returns mock data.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of product dictionaries
    """
    # For demonstration purposes, we'll return mock data
    # In a real implementation, you would make HTTP requests to Google Shopping API
    # and parse the response
    
    mock_products = []
    brands = ["365 Whole Foods", "Kirkland", "Great Value", "365 by Whole Foods Market", "Organic"]
    stores = ["Walmart", "Amazon", "Target", "Whole Foods", "Costco"]
    
    for i in range(min(max_results, 10)):  # Return up to 10 mock products
        brand = random.choice(brands)
        store = random.choice(stores)
        price = round(random.uniform(2.99, 19.99), 2)
        weight = f"{random.choice([8, 12, 16, 24, 32])} oz"
        
        product = {
            'product_id': f"mock_{hash(query) % 1000000}_{i}",
            'name': f"{brand} {query}",
            'price': price,
            'price_text': f"${price}",
            'currency': 'USD',
            'store': store,
            'url': f"https://example.com/product/{hash(query) % 1000000}_{i}",
            'image_url': f"https://via.placeholder.com/150?text={query.replace(' ', '+')}",
            'weight': weight,
            'brand': brand,
            'rating': round(random.uniform(3.0, 5.0), 1),
            'review_count': random.randint(10, 1000),
        }
        mock_products.append(product)
    
    return mock_products
