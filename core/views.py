from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Category, Product
from .plugins import plugin_manager
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import datetime

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

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('home')
    
    return render(request, 'auth/register.html')

def nintendo_accounts_view(request):
    return render(request, 'auth/nintendo_accounts.html')

def register_customer(request):
    current_year = datetime.now().year
    year_range = range(current_year, current_year - 100, -1)
    
    context = {
        'year_range': year_range
    }
    
    if request.method == 'POST':
        # 獲取表單數據
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        shipping_address = request.POST.get('shipping_address')
        
        # 驗證密碼
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register_customer.html', context)
        
        # 檢查用戶名和郵箱是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register_customer.html', context)
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register_customer.html', context)
        
        # 創建用戶
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        
        # 創建客戶檔案
        customer = Customer.objects.create(
            user=user,
            shipping_address=shipping_address
        )
        
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('home')
    
    return render(request, 'auth/register_customer.html', context)

def register_vendor(request):
    if request.method == 'POST':
        # 獲取表單數據
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        store_name = request.POST.get('store_name')
        store_description = request.POST.get('store_description')
        
        # 驗證密碼
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register_vendor.html')
        
        # 檢查用戶名和郵箱是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register_vendor.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register_vendor.html')
        
        # 創建用戶
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=True  # 給予商家後台訪問權限
        )
        
        # 創建商家檔案
        vendor = Vendor.objects.create(
            user=user,
            store_name=store_name,
            store_description=store_description
        )
        
        login(request, user)
        messages.success(request, 'Vendor registration successful!')
        return redirect('home')
    
    return render(request, 'auth/register_vendor.html')
