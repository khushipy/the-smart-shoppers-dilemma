from django.urls import path
from . import views

app_name = 'shopping'

urlpatterns = [
    # Root endpoint
    path('', views.api_root, name='api-root'),
    
    # Product search endpoint
    path('api/search/', views.ProductSearchView.as_view(), name='product-search'),
    
    # Product detail endpoint
    path('api/products/<str:product_id>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Search history endpoint
    path('api/search/history/', views.SearchHistoryView.as_view(), name='search-history'),
    
    # Health check endpoint
    path('health/', views.health_check, name='health-check'),
]
