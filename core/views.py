from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Category, Product
from .plugins import plugin_manager

def home(request):
    categories = Category.objects.all()[:3]  # Get first 3 categories
    featured_products = Product.objects.filter(featured=True)[:8]  # Get up to 8 featured products
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'core/home.html', context)

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def product_management(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'admin/product_management.html', {
        'products': products,
        'categories': categories,
    })

@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def add_product(request):
    name = request.POST.get('name')
    description = request.POST.get('description')
    price = request.POST.get('price')
    category_id = request.POST.get('category')
    featured = request.POST.get('featured') == 'on'
    
    category = get_object_or_404(Category, id=category_id)
    
    product = Product.objects.create(
        name=name,
        description=description,
        price=price,
        category=category,
        featured=featured
    )
    
    if 'image' in request.FILES:
        product.image = request.FILES['image']
        product.save()
    
    return redirect('product_management')

@user_passes_test(is_superuser)
def get_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'category': product.category.id,
        'featured': product.featured,
        'image': product.image.url if product.image else None,
        'categories': [{'id': c.id, 'name': c.name} for c in categories]
    })

@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    product.name = request.POST.get('name')
    product.description = request.POST.get('description')
    product.price = request.POST.get('price')
    product.category = get_object_or_404(Category, id=request.POST.get('category'))
    product.featured = request.POST.get('featured') == 'on'
    
    if 'image' in request.FILES:
        product.image = request.FILES['image']
    
    product.save()
    return redirect('product_management')

@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('product_management')

def logout_view(request):
    logout(request)
    return redirect('home')

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'core/product_detail.html', {
        'product': product
    })

@user_passes_test(is_superuser)
def plugin_management(request):
    if request.method == 'POST':
        plugin_name = request.POST.get('plugin_name')
        action = request.POST.get('action')
        
        if action == 'enable':
            plugin_manager.enable_plugin(plugin_name)
        elif action == 'disable':
            plugin_manager.disable_plugin(plugin_name)
    
    # 獲取插件信息
    plugins = plugin_manager.get_all_plugins()
    
    # 讀取插件日誌
    try:
        with open('plugin.log', 'r') as f:
            plugin_logs = f.readlines()[-50:]  # 只顯示最後50行
    except FileNotFoundError:
        plugin_logs = ['No plugin logs found']
    
    return render(request, 'admin/plugin_management.html', {
        'plugins': plugins,
        'plugin_logs': plugin_logs
    })
