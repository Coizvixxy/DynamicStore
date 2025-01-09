from core.plugins import PluginInterface
from django.db.models import Q
from typing import List, Dict, Any

class Plugin(PluginInterface):
    """Advanced search plugin that provides enhanced product search capabilities"""
    
    @property
    def name(self) -> str:
        return "Advanced Search"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self) -> None:
        """Set up the advanced search functionality"""
        from core.models import Product  # Import here to avoid circular imports
        
        def advanced_search(
            keyword: str = None,
            category: str = None,
            min_price: float = None,
            max_price: float = None,
            **filters
        ) -> List[Dict[str, Any]]:
            """
            Perform advanced product search with multiple criteria
            """
            query = Q()
            
            if keyword:
                query &= (
                    Q(name__icontains=keyword) |
                    Q(description__icontains=keyword)
                )
            
            if category:
                query &= Q(category__name=category)
                
            if min_price is not None:
                query &= Q(price__gte=min_price)
                
            if max_price is not None:
                query &= Q(price__lte=max_price)
                
            # Add any additional custom filters
            for field, value in filters.items():
                if value is not None:
                    query &= Q(**{field: value})
            
            products = Product.objects.filter(query)
            
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'category': p.category.name if p.category else None,
                    'description': p.description
                }
                for p in products
            ]
        
        # Make the search function available globally
        setattr(Product, 'advanced_search', staticmethod(advanced_search))
    
    def cleanup(self) -> None:
        """Remove the advanced search functionality"""
        from core.models import Product
        
        if hasattr(Product, 'advanced_search'):
            delattr(Product, 'advanced_search') 