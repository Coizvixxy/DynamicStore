from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Category, Product, Vendor, Customer
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
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # 通過 email 查找用戶
            user = User.objects.get(email=email)
            # 使用用戶名（email）和密碼進行驗證
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # 根據用戶類型重定向
                if user.is_staff:
                    return redirect('product_management')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
        
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
    
    # 保存表單數據以便在驗證失敗時重新填充
    form_data = {
        'nickname': request.POST.get('nickname', ''),
        'email': request.POST.get('email', ''),
        'birth_year': request.POST.get('birth_year', ''),
        'birth_month': request.POST.get('birth_month', ''),
        'birth_day': request.POST.get('birth_day', ''),
        'gender': request.POST.get('gender', ''),
        'country': request.POST.get('country', '')
    }
    
    context = {
        'year_range': year_range,
        'form_data': form_data  # 添加表單數據到上下文
    }
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # 驗證必填字段
        required_fields = ['nickname', 'email', 'birth_year', 'birth_month', 'birth_day']
        missing_fields = [field for field in required_fields if not form_data[field]]
        if missing_fields:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'auth/register_customer.html', context)
        
        # 密碼驗證
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register_customer.html', context)
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'auth/register_customer.html', context)
        
        # 檢查密碼強度
        if not any(char.isdigit() for char in password1):
            messages.error(request, 'Password must contain at least one number.')
            return render(request, 'auth/register_customer.html', context)
            
        if not any(char.isalpha() for char in password1):
            messages.error(request, 'Password must contain at least one letter.')
            return render(request, 'auth/register_customer.html', context)
        
        # 檢查郵箱
        if User.objects.filter(email=form_data['email']).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register_customer.html', context)
        
        try:
            # 創建用戶
            user = User.objects.create_user(
                username=form_data['email'],
                email=form_data['email'],
                password=password1,
                first_name=form_data['nickname']
            )
            
            # 設置生日
            try:
                birth_date = datetime(
                    int(form_data['birth_year']), 
                    int(form_data['birth_month']), 
                    int(form_data['birth_day'])
                ).date()
                user.customer.birth_date = birth_date
            except ValueError:
                messages.error(request, 'Invalid birth date.')
                user.delete()
                return render(request, 'auth/register_customer.html', context)
            
            # 更新其他信息
            user.customer.gender = form_data['gender']
            user.customer.country = form_data['country']
            user.customer.save()
            
            # 自動登入
            login(request, user)
            messages.success(request, f'Welcome, {form_data["nickname"]}! Your account has been created successfully.')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'auth/register_customer.html', context)
    
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
        store_category = request.POST.get('store_category')
        store_description = request.POST.get('store_description')
        business_registration = request.POST.get('business_registration')
        phone = request.POST.get('phone')
        position = request.POST.get('position')
        business_address = request.POST.get('business_address')
        
        # 驗證密碼
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register_vendor.html')
            
        # 檢查用戶名是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register_vendor.html', {
                'form_data': request.POST  # 保存表單數據
            })
        
        # 檢查郵箱是否已存在
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register_vendor.html', {
                'form_data': request.POST  # 保存表單數據
            })
            
        try:
            # 創建用戶
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_staff=True
            )
            
            # 創建商家檔案
            vendor = Vendor.objects.create(
                user=user,
                store_name=store_name,
                store_category=store_category,
                store_description=store_description,
                business_registration=business_registration,
                phone=phone,
                position=position,
                business_address=business_address
            )
            
            # 處理上傳的圖片
            if 'store_logo' in request.FILES:
                vendor.store_logo = request.FILES['store_logo']
            if 'store_banner' in request.FILES:
                vendor.store_banner = request.FILES['store_banner']
            vendor.save()
            
            login(request, user)
            messages.success(request, 'Vendor registration successful!')
            return redirect('home')
            
        except Exception as e:
            # 如果創建過程中出現錯誤，刪除已創建的用戶
            if 'user' in locals():
                user.delete()
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'auth/register_vendor.html', {
                'form_data': request.POST  # 保存表單數據
            })
    
    return render(request, 'auth/register_vendor.html')
