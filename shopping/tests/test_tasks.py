import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from shopping.tasks import (
    fetch_products_from_google_shopping,
    extract_product_info,
    get_headers,
    get_random_delay
)


class TestShoppingTasks(TestCase):
    def test_get_headers(self):
        """Test that get_headers returns a dictionary with expected keys"""
        headers = get_headers()
        self.assertIsInstance(headers, dict)
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Accept-Language', headers)
        self.assertIn('Connection', headers)

    def test_get_random_delay(self):
        """Test that get_random_delay returns a float within expected range"""
        delay = get_random_delay()
        self.assertIsInstance(delay, float)
        self.assertGreaterEqual(delay, 1.0)
        self.assertLessEqual(delay, 3.0)

    @patch('shopping.tasks.HTMLSession')
    def test_extract_product_info(self, mock_session):
        """Test product info extraction from HTML"""
        # Mock HTML element
        mock_div = MagicMock()
        
        # Mock find method to return elements
        mock_h3 = MagicMock()
        mock_h3.text = 'Test Product'
        
        mock_price = MagicMock()
        mock_price.text = '$9.99'
        
        mock_store = MagicMock()
        mock_store.text = 'by Test Store'
        
        mock_a = MagicMock()
        mock_a.attrs = {'href': '/test-product'}
        
        mock_img = MagicMock()
        mock_img.attrs = {'src': 'test.jpg'}
        
        # Configure the mock to return different values on subsequent calls
        mock_div.find.side_effect = [
            [mock_h3],  # h3 element
            [mock_price],  # price element
            [mock_store],  # store element
            [mock_a],  # a element
            [mock_img]  # img element
        ]
        
        # Call the function
        result = extract_product_info(mock_div)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Test Product')
        self.assertEqual(result['price_text'], '$9.99')
        self.assertEqual(result['store'], 'Test Store')
        self.assertTrue(result['url'].startswith('https://www.google.com'))
        self.assertIn('test.jpg', result['image_url'])

    def test_fetch_products_from_google_shopping(self):
        """Test the main product fetching function"""
        # Call the function with a test query
        products = fetch_products_from_google_shopping('test query', max_results=5)
        
        # Assertions
        self.assertIsInstance(products, list)
        self.assertLessEqual(len(products), 5)  # Should not exceed max_results
        
        if products:  # Only run these assertions if we got products
            product = products[0]
            self.assertIn('product_id', product)
            self.assertIn('name', product)
            self.assertIn('price', product)
            self.assertIn('store', product)
            self.assertIn('url', product)
            self.assertIn('image_url', product)
            
            # Test that the product name contains the query (case-insensitive)
            self.assertIn('test query'.lower(), product['name'].lower())

    def test_fetch_products_with_mock(self):
        """Test product fetching with a mock response"""
        # Mock the HTMLSession
        with patch('shopping.tasks.HTMLSession') as mock_session:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
                <html>
                    <div class="sh-dgr__grid-result">
                        <h3>Test Product</h3>
                        <span class="price">$9.99</span>
                        <div>by Test Store</div>
                        <a href="/test-product">Link</a>
                        <img src="test.jpg">
                    </div>
                </html>
            """
            
            # Configure the mock session to return our mock response
            mock_session.return_value.get.return_value = mock_response
            
            # Call the function
            products = fetch_products_from_google_shopping('test query', max_results=5)
            
            # Assertions
            self.assertIsInstance(products, list)
            self.assertGreater(len(products), 0)
            self.assertEqual(products[0]['name'], 'Test Product')
            self.assertEqual(products[0]['price_text'], '$9.99')
            self.assertEqual(products[0]['store'], 'Test Store')
            self.assertIn('test-product', products[0]['url'])
            self.assertIn('test.jpg', products[0]['image_url'])
