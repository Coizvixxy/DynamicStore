import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    shipping_address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=3, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile (UUID: {self.uuid})"

class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    store_name = models.CharField(max_length=100)
    store_category = models.CharField(max_length=50, blank=True, null=True)
    store_description = models.TextField(blank=True)
    store_logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)
    store_banner = models.ImageField(upload_to='store_banners/', null=True, blank=True)
    business_registration = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.store_name} (UUID: {self.uuid})"

# 信號接收器，在創建用戶時自動創建相應的檔案
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """只為非商家用戶創建客戶檔案"""
    if created and not instance.is_staff:
        Customer.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用戶檔案"""
    if not instance.is_staff:
        if not hasattr(instance, 'customer'):
            Customer.objects.create(user=instance)
        instance.customer.save()
