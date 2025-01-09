from django.test import TestCase
from core.plugins import plugin_manager
from core.models import Product, Category

class AdvancedSearchPluginTest(TestCase):
    def setUp(self):
        # Load the plugin
        plugin_manager.discover_plugins()
        
        # Create test data
        self.category = Category.objects.create(name="Electronics")
        
        self.products = [
            Product.objects.create(
                name="Gaming Laptop",
                description="High performance laptop",
                price=1200.00,
                category=self.category
            ),
            Product.objects.create(
                name="Budget Laptop",
                description="Affordable laptop",
                price=500.00,
                category=self.category
            )
        ]
    
    def test_keyword_search(self):
        results = Product.advanced_search(keyword="gaming")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Gaming Laptop")
    
    def test_price_range_search(self):
        results = Product.advanced_search(min_price=600.00)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Gaming Laptop")
        
        results = Product.advanced_search(max_price=600.00)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Budget Laptop")
    
    def test_combined_search(self):
        results = Product.advanced_search(
            keyword="laptop",
            min_price=1000.00,
            category="Electronics"
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Gaming Laptop") 