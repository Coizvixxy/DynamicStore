from core.plugins import PluginInterface
from django.db import models
from django.conf import settings
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from core.models import Product

class ReviewModel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'

class Plugin(PluginInterface):
    """Product Reviews plugin that allows users to rate and review products"""
    
    @property
    def name(self) -> str:
        return "Product Reviews"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_urls(self):
        return [
            path('product/<int:product_id>/review/', self.add_review, name='add_review'),
            path('product/<int:product_id>/reviews/', self.view_reviews, name='view_reviews'),
        ]
    
    def initialize(self) -> None:
        """Initialize the plugin"""
        # Add the review model to Django's migration system
        from django.apps import apps
        if not apps.is_installed('core'):
            raise RuntimeError("Core app must be installed")
            
        if not apps.get_model('core', 'ReviewModel', False):
            # Create the model only if it doesn't exist
            from django.db import connection
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(ReviewModel)
    
    def cleanup(self) -> None:
        """Cleanup when plugin is disabled"""
        # Could remove the model tables if needed
        pass
    
    def add_review(self, request, product_id):
        if not request.user.is_authenticated:
            return redirect('login')
            
        product = get_object_or_404(Product, id=product_id)
        
        if request.method == 'POST':
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            
            ReviewModel.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            
            return redirect('product_detail', product_id=product_id)
            
        return render(request, 'product_reviews/add_review.html', {
            'product': product
        })
    
    def view_reviews(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        reviews = ReviewModel.objects.filter(product=product).order_by('-created_at')
        
        return render(request, 'product_reviews/view_reviews.html', {
            'product': product,
            'reviews': reviews
        }) 