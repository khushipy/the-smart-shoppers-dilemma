import time
import json
from typing import List, Dict, Any, Optional

from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Product, SearchHistory, CachedSearchResult
from .serializers import ProductSerializer, SearchHistorySerializer, ProductSearchSerializer
from .tasks import fetch_products_from_google_shopping


class ProductSearchView(APIView):
    """API endpoint to search for products"""
    
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Validate input
        serializer = ProductSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query'].strip()
        max_results = serializer.validated_data['max_results']
        
        # Check cache first
        cache_key = f'product_search_{query.lower()}_{max_results}'
        cached_results = cache.get(cache_key)
        
        if cached_results is not None:
            return Response({
                'status': 'success',
                'cached': True,
                'query': query,
                'results': cached_results,
                'timestamp': timezone.now().isoformat()
            })
        
        # Check database for recent results
        products = Product.objects.get_products_for_query(query, max_results)
        
        if products.exists():
            # Cache the results
            product_data = ProductSerializer(products, many=True).data
            cache.set(cache_key, product_data, timeout=3600)  # Cache for 1 hour
            
            return Response({
                'status': 'success',
                'cached': False,
                'query': query,
                'results': product_data,
                'timestamp': timezone.now().isoformat()
            })
        
        # If no cached results, initiate async task
        search = SearchHistory.objects.create(query=query)
        
        # In production, we would use Celery here
        # For now, we'll call it synchronously
        try:
            start_time = time.time()
            products_data = fetch_products_from_google_shopping(query, max_results)
            response_time = time.time() - start_time
            
            # Save products to database
            with transaction.atomic():
                for product_data in products_data:
                    Product.objects.update_or_create(
                        product_id=product_data['product_id'],
                        defaults={
                            'search_query': query,
                            'name': product_data['name'],
                            'brand': product_data.get('brand'),
                            'price': product_data.get('price'),
                            'currency': product_data.get('currency', 'USD'),
                            'price_text': product_data.get('price_text'),
                            'weight': product_data.get('weight'),
                            'store': product_data.get('store'),
                            'rating': product_data.get('rating'),
                            'review_count': product_data.get('review_count', 0),
                            'url': product_data['url'],
                            'image_url': product_data.get('image_url'),
                        }
                    )
            
            # Update search history
            search.status = SearchHistory.SearchStatus.COMPLETED
            search.results_count = len(products_data)
            search.response_time = response_time
            search.completed_at = timezone.now()
            search.save()
            
            # Cache the results
            products = Product.objects.get_products_for_query(query, max_results)
            product_data = ProductSerializer(products, many=True).data
            cache.set(cache_key, product_data, timeout=3600)  # Cache for 1 hour
            
            return Response({
                'status': 'success',
                'cached': False,
                'query': query,
                'results': product_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            # Log the error
            search.status = SearchHistory.SearchStatus.FAILED
            search.error_message = str(e)
            search.completed_at = timezone.now()
            search.save()
            
            return Response(
                {'status': 'error', 'message': 'Failed to fetch product data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchHistoryView(APIView):
    """API endpoint to view search history"""
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        searches = SearchHistory.objects.all().order_by('-created_at')[:50]  # Last 50 searches
        serializer = SearchHistorySerializer(searches, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'results': serializer.data
        })


class ProductDetailView(APIView):
    """API endpoint to get product details"""
    
    permission_classes = [AllowAny]
    
    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(product_id=product_id)
            serializer = ProductSerializer(product)
            return Response({
                'status': 'success',
                'product': serializer.data
            })
        except Product.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'service': 'smart-shopping-api',
        'timestamp': timezone.now().isoformat()
    })


def api_root(request):
    """Root endpoint with API documentation"""
    base_url = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse({
        'message': 'Welcome to Smart Shopping API',
        'endpoints': {
            'search': {
                'url': f'{base_url}/api/search/',
                'method': 'POST',
                'description': 'Search for products',
                'example_request': {
                    'query': 'organic peanut butter',
                    'max_results': 5
                }
            },
            'product_detail': {
                'url': f'{base_url}/api/products/{{product_id}}/',
                'method': 'GET',
                'description': 'Get product details by ID'
            },
            'search_history': {
                'url': f'{base_url}/api/search/history/',
                'method': 'GET',
                'description': 'View search history'
            },
            'health_check': {
                'url': f'{base_url}/health/',
                'method': 'GET',
                'description': 'Check API health status'
            },
            'admin': {
                'url': f'{base_url}/admin/',
                'description': 'Admin interface (login required)'
            }
        },
        'documentation': 'For more details, please refer to the API documentation.'
    })
