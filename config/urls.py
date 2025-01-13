"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.plugins import plugin_manager

# 創建插件 URL patterns
def get_plugin_urls():
    """動態生成插件的 URL patterns"""
    server_logs = plugin_manager.get_plugin('server_logs')
    if server_logs:
        return [
            path('logs/', include(([
                path('', views.plugin_management, name='logs'),
                path('<str:log_type>/', views.plugin_management, name='view_logs'),
                path('<str:log_type>/api/', server_logs.get_logs_api, name='get_logs'),
                path('message/add/', server_logs.add_message, name='add_log_message'),
            ], 'server_logs'))),
        ]
    return []

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    
    # Product Management URLs
    path('management/products/', views.product_management, name='product_management'),
    path('management/product/add/', views.add_product, name='add_product'),
    path('management/product/<int:product_id>/', views.get_product, name='get_product'),
    path('management/product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('management/product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('management/plugins/', views.plugin_management, name='plugin_management'),
    
    # 插件 URLs
    path('plugins/', include((get_plugin_urls(), 'plugins'), namespace='plugins')),
    
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('nintendo-login/', views.nintendo_login_view, name='nintendo_login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
