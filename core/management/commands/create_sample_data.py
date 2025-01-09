from django.core.management.base import BaseCommand
from core.models import Category, Product

class Command(BaseCommand):
    help = 'Creates sample categories and products'

    def handle(self, *args, **kwargs):
        # Create categories
        electronics = Category.objects.create(
            name='Electronics',
            description='Electronic devices and accessories'
        )
        
        clothing = Category.objects.create(
            name='Clothing',
            description='Fashion and apparel'
        )
        
        books = Category.objects.create(
            name='Books',
            description='Books and literature'
        )

        # Create some products
        Product.objects.create(
            name='Laptop',
            description='High performance laptop',
            price=999.99,
            category=electronics,
            featured=True
        )

        Product.objects.create(
            name='T-Shirt',
            description='Cotton t-shirt',
            price=19.99,
            category=clothing,
            featured=True
        )

        Product.objects.create(
            name='Python Programming',
            description='Learn Python programming',
            price=29.99,
            category=books,
            featured=True
        )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data')) 