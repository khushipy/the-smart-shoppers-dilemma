import pytest
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from shopping.models import Product, SearchHistory, CachedSearchResult


class ProductModelTest(TestCase):
    def setUp(self):
        self.product_data = {
            'search_query': 'organic peanut butter',
            'name': 'Organic Peanut Butter',
            'brand': '365',
            'price': 4.99,
            'currency': 'USD',
            'price_text': '$4.99',
            'product_id': 'test123',
            'url': 'http://example.com/product/123',
            'image_url': 'http://example.com/images/123.jpg',
            'weight': '16 oz',
            'store': 'Whole Foods',
            'rating': 4.5,
            'review_count': 128
        }
        self.product = Product.objects.create(**self.product_data)

    def test_product_creation(self):
        """Test that a product can be created"""
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.name, 'Organic Peanut Butter')
        self.assertEqual(self.product.brand, '365')
        self.assertEqual(float(self.product.price), 4.99)
        self.assertEqual(self.product.currency, 'USD')
        self.assertEqual(self.product.weight, '16 oz')

    def test_product_str_representation(self):
        """Test the string representation of a product"""
        self.assertEqual(str(self.product), 'Organic Peanut Butter - $4.99')

    def test_product_to_dict(self):
        """Test the to_dict method"""
        product_dict = self.product.to_dict()
        self.assertEqual(product_dict['name'], 'Organic Peanut Butter')
        self.assertEqual(product_dict['brand'], '365')
        self.assertEqual(product_dict['price'], 4.99)
        self.assertEqual(product_dict['weight'], '16 oz')
        self.assertIn('searched_at', product_dict)


class SearchHistoryModelTest(TestCase):
    def setUp(self):
        self.search = SearchHistory.objects.create(
            query='organic peanut butter',
            results_count=10
        )

    def test_search_history_creation(self):
        """Test that a search history entry can be created"""
        self.assertEqual(SearchHistory.objects.count(), 1)
        self.assertEqual(self.search.query, 'organic peanut butter')
        self.assertEqual(self.search.status, 'pending')
        self.assertEqual(self.search.results_count, 10)

    def test_mark_completed(self):
        """Test marking a search as completed"""
        self.search.mark_completed(15)
        self.assertEqual(self.search.status, 'completed')
        self.assertEqual(self.search.results_count, 15)
        self.assertIsNotNone(self.search.completed_at)

    def test_mark_failed(self):
        """Test marking a search as failed"""
        error_message = 'Connection timeout'
        self.search.mark_failed(error_message)
        self.assertEqual(self.search.status, 'failed')
        self.assertEqual(self.search.error_message, error_message)
        self.assertIsNotNone(self.search.completed_at)


class CachedSearchResultModelTest(TestCase):
    def setUp(self):
        self.cached_data = {
            'query': 'organic peanut butter',
            'results': [{'id': 1, 'name': 'Test Product'}],
            'expires_at': timezone.now() + timedelta(hours=24)
        }
        self.cached_result = CachedSearchResult.objects.create(
            query=self.cached_data['query'],
            results=self.cached_data['results'],
            expires_at=self.cached_data['expires_at']
        )

    def test_cached_result_creation(self):
        """Test that a cached result can be created"""
        self.assertEqual(CachedSearchResult.objects.count(), 1)
        self.assertEqual(self.cached_result.query, 'organic peanut butter')
        self.assertEqual(len(self.cached_result.results), 1)

    def test_get_cached_results(self):
        """Test retrieving cached results"""
        results = CachedSearchResult.get_cached_results('organic peanut butter')
        self.assertEqual(results, self.cached_data['results'])

    def test_cache_results(self):
        """Test caching new results"""
        new_results = [{'id': 2, 'name': 'New Product'}]
        cached = CachedSearchResult.cache_results(
            'new query',
            new_results,
            ttl_hours=1
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached.query, 'new query')
        self.assertEqual(cached.results, new_results)
