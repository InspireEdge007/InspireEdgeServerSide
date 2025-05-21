from .models import LocalProduct

def get_local_store_products(user):
    
    # Fetch products from all local stores for a specific user.
    
    return LocalProduct.objects.filter(store__user=user).values(
        'id', 'name', 'description', 'price', 'image'
    )
