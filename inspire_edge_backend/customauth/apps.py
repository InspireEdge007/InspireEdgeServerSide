# inspire_edge_backend/customauth/apps.py
from django.apps import AppConfig

class CustomAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "customauth"
    label = "customauth"