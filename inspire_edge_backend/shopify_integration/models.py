from django.db import models
from django.conf import settings

class ShopifyStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop_domain = models.CharField(max_length=255, unique=True)
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_domain
