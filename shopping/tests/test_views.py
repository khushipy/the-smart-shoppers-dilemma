import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from shopping.models import Product, SearchHistory


class ProductSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.search_url = reverse('shopping:product-search')
        
        # Create test data
        self.test_product = Product.objects.create(
            search_query='test product',
            name='Test Product',
            brand='Test Brand',
            price=9.99,
            currency='USD',
            price_text='$9.99',
            product_id='test123',
            url='http://example.com/product/123',
            image_url='http://example.com/images/123.jpg',
            weight='16 oz',
            store='Test Store',
            rating=4.5,
            review_count=100
        )

    def test_search_with_cached_results(self):
        """Test search with cached results"""
        # First search (not in cache)
        response = self.client.post(
            self.search_url,
            data={'query': 'test product', 'max_results': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
        
        # Second search (should be cached)
        response = self.client.post(
            self.search_url,
            data={'query': 'test product', 'max_results': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['cached'])

    def test_search_with_invalid_data(self):
        """Test search with invalid data"""
        # Missing query
        response = self.client.post(
            self.search_url,
            data={'max_results': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid max_results
        response = self.client.post(
            self.search_url,
            data={'query': 'test', 'max_results': 0},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_product = Product.objects.create(
            search_query='test product',
            name='Test Product',
            product_id='test123',
            url='http://example.com/product/123'
        )

    def test_get_existing_product(self):
        """Test getting an existing product"""
        url = reverse('shopping:product-detail', kwargs={'product_id': 'test123'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product']['name'], 'Test Product')

    def test_get_nonexistent_product(self):
        """Test getting a non-existent product"""
        url = reverse('shopping:product-detail', kwargs={'product_id': 'nonexistent'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SearchHistoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.history_url = reverse('shopping:search-history')
        
        # Create test search history
        SearchHistory.objects.create(
            query='test query',
            status='completed',
            results_count=5,
            response_time=1.5
        )

    def test_get_search_history(self):
        """Test getting search history"""
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], 'test query')


class HealthCheckViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.health_url = reverse('shopping:health-check')

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['service'], 'smart-shopping-api')
