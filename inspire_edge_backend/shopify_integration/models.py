from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
User = get_user_model()


class ShopifyStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop_domain = models.CharField(max_length=255, unique=True,verbose_name="Shop Domain")
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_domain

class WooCommerceStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    store_url = models.URLField(unique=True)
    consumer_key = models.CharField(max_length=255)
    consumer_secret = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_url

class BigCommerceStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    store_hash = models.CharField(max_length=100, unique=True)
    access_token = models.TextField()
    scope = models.TextField()
    context = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_hash


# custom store integration
class CustomStore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_stores')
    store_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Custom Store'
        verbose_name_plural = 'Custom Stores'

    def __str__(self):
        return self.store_name


class Category(models.Model):
    shop = models.ForeignKey(CustomStore, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=64)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class CustomProduct(models.Model):
    shop = models.ForeignKey(CustomStore, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=256)
    code = models.CharField(max_length=16, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.FloatField()
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Custom Product'
        verbose_name_plural = 'Custom Products'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.category.shop != self.shop:
            raise ValidationError("Product category must belong to the same shop.")

    def __str__(self):
        return f"{self.name} - {self.price}"