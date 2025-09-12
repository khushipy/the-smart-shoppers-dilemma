from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
import json
from datetime import timedelta


class ProductQuerySet(models.QuerySet):
    """Custom QuerySet for Product model with caching support"""
    
    def get_products_for_query(self, query: str, max_results: int = 10):
        """Get products for a search query, using cache if available"""
        cache_key = f'product_search_{query.lower().strip()}_{max_results}'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
            
        # If not in cache, perform the query
        products = self.filter(search_query__iexact=query)[:max_results]
        
        # Cache the results for 1 hour
        if products:
            cache.set(cache_key, products, timeout=3600)
            
        return products


class Product(models.Model):
    """Model to store product information from Google Shopping"""
    
    # Search information
    search_query = models.CharField(max_length=255, db_index=True)
    search_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Product details
    name = models.CharField(max_length=500)
    brand = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    price_text = models.CharField(max_length=100, blank=True, null=True)
    
    # Product identification
    product_id = models.CharField(max_length=255, unique=True, db_index=True)
    url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    # Additional details
    weight = models.CharField(max_length=100, blank=True, null=True)
    store = models.CharField(max_length=255, blank=True, null=True)
    rating = models.FloatField(null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductQuerySet.as_manager()
    
    class Meta:
        ordering = ['-search_timestamp', 'price']
        indexes = [
            models.Index(fields=['search_query', 'search_timestamp']),
            models.Index(fields=['brand']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price_text or 'Price N/A'}"
    
    def to_dict(self):
        """Convert product to dictionary for API response"""
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'price_text': self.price_text,
            'weight': self.weight,
            'store': self.store,
            'rating': self.rating,
            'review_count': self.review_count,
            'url': self.url,
            'image_url': self.image_url,
            'search_query': self.search_query,
            'searched_at': self.search_timestamp.isoformat(),
        }


class SearchHistory(models.Model):
    """Track user search history and performance"""
    
    class SearchStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    query = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=SearchStatus.choices,
        default=SearchStatus.PENDING
    )
    results_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    # Performance metrics
    response_time = models.FloatField(null=True, blank=True)  # in seconds
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Search Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query} - {self.status} ({self.created_at})"
    
    def mark_completed(self, results_count=0):
        """Mark search as completed successfully"""
        self.status = self.SearchStatus.COMPLETED
        self.results_count = results_count
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark search as failed"""
        self.status = self.SearchStatus.FAILED
        self.error_message = str(error_message)[:1000]  # Truncate long errors
        self.completed_at = timezone.now()
        self.save()


class CachedSearchResult(models.Model):
    """Cache search results to avoid repeated API calls"""
    
    query = models.CharField(max_length=255, db_index=True)
    results = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['query', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.query} (expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_cached_results(cls, query, max_age_hours=24):
        """Get cached results if available and not expired"""
        now = timezone.now()
        try:
            cached = cls.objects.filter(
                query__iexact=query,
                expires_at__gt=now
            ).order_by('-created_at').first()
            
            if cached:
                return cached.results
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error accessing cache: {e}")
        return None
    
    @classmethod
    def cache_results(cls, query, results, ttl_hours=24):
        """Cache search results"""
        try:
            return cls.objects.create(
                query=query,
                results=results,
                expires_at=timezone.now() + timedelta(hours=ttl_hours)
            )
        except Exception as e:
            print(f"Error caching results: {e}")
            return None
