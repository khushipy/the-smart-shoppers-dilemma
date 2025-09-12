from rest_framework import serializers
from .models import Product, SearchHistory


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'price', 'currency', 'price_text',
            'weight', 'store', 'rating', 'review_count', 'url', 'image_url',
            'search_query', 'search_timestamp'
        ]
        read_only_fields = ['search_timestamp']
    
    def to_representation(self, instance):
        """Convert the instance to a dictionary representation"""
        if hasattr(instance, 'to_dict'):
            return instance.to_dict()
        return super().to_representation(instance)


class SearchHistorySerializer(serializers.ModelSerializer):
    """Serializer for SearchHistory model"""
    
    class Meta:
        model = SearchHistory
        fields = [
            'id', 'query', 'status', 'results_count', 'error_message',
            'response_time', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'status', 'results_count', 'error_message', 'response_time',
            'created_at', 'completed_at'
        ]


class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search requests"""
    query = serializers.CharField(max_length=255, required=True)
    max_results = serializers.IntegerField(default=10, min_value=1, max_value=50)
