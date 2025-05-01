from django.contrib import admin
from .models import ShopifyStore

@admin.register(ShopifyStore)
class ShopifyStoreAdmin(admin.ModelAdmin):
    list_display = ('shop_domain', 'user', 'created_at')
    search_fields = ('shop_domain', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('access_token',)