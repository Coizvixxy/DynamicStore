from core.plugins import PluginInterface
from django.urls import path
from django.shortcuts import render

class Plugin(PluginInterface):
    """Advanced search functionality for products"""
    
    @property
    def name(self) -> str:
        return "Advanced Search"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_urls(self):
        return [
            path('search/', self.search_view, name='advanced_search'),
        ]
    
    def search_view(self, request):
        return render(request, 'advanced_search/search.html') 