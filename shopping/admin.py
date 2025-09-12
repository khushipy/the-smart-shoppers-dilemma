from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Product, SearchHistory, CachedSearchResult


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price_display', 'store', 'search_query_display', 'created_at')
    list_filter = ('brand', 'store', 'created_at')
    search_fields = ('name', 'brand', 'store', 'search_query')
    readonly_fields = ('created_at', 'updated_at', 'search_timestamp')
    date_hierarchy = 'created_at'
    
    def price_display(self, obj):
        if obj.price is not None:
            return f"${obj.price:.2f} {obj.currency}"
        return obj.price_text or "N/A"
    price_display.short_description = 'Price'
    
    def search_query_display(self, obj):
        return obj.search_query[:50] + ('...' if len(obj.search_query) > 50 else '')
    search_query_display.short_description = 'Search Query'


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'status', 'results_count', 'response_time_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('query', 'error_message')
    readonly_fields = ('created_at', 'completed_at', 'response_time')
    date_hierarchy = 'created_at'
    
    def response_time_display(self, obj):
        if obj.response_time is not None:
            return f"{obj.response_time:.2f}s"
        return "N/A"
    response_time_display.short_description = 'Response Time'


@admin.register(CachedSearchResult)
class CachedSearchResultAdmin(admin.ModelAdmin):
    list_display = ('query', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('query',)
    readonly_fields = ('created_at', 'results_preview')
    date_hierarchy = 'created_at'
    
    def results_preview(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.results, indent=2))
    results_preview.short_description = 'Results'
