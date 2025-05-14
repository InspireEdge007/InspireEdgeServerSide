from django.db import models
from django.conf import settings

class ShopifyStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop_domain = models.CharField(max_length=255, unique=True,verbose_name="Shop Domain")
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_domain
