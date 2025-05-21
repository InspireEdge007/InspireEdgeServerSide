from django.contrib import admin
from .models import ShopifyStore, WooCommerceStore, BigCommerceStore, CustomStore, CustomProduct, Category

@admin.register(ShopifyStore)
class ShopifyStoreAdmin(admin.ModelAdmin):
    list_display = ('shop_domain', 'user', 'created_at')
    search_fields = ('shop_domain', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('access_token',)

@admin.register(WooCommerceStore)
class WooCommerceStoreAdmin(admin.ModelAdmin):
    list_display = ('store_url', 'user', 'created_at')
    search_fields = ('store_url', 'user__email')
    list_filter = ('created_at',)

@admin.register(BigCommerceStore)
class BigCommerceStoreAdmin(admin.ModelAdmin):
    list_display = ('store_hash', 'user', 'created_at')
    search_fields = ('store_hash', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('access_token',)


# @admin.register(CustomStore)
# class CustomStoreAdmin(admin.ModelAdmin):
#     list_display = ('user', 'name', 'description')
#     search_fields = ('name', 'user__username')

# @admin.register(CustomProduct)
# class CustomProductAdmin(admin.ModelAdmin):
#     list_display = ('store', 'name', 'price', 'description', 'image')
#     search_fields = ('name',)
#     list_filter = ('store',)


admin.site.register(CustomStore)
admin.site.register(CustomProduct)
admin.site.register(Category)
