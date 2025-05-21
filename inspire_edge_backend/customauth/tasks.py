from celery import shared_task
from django.utils import timezone
from .models import User




@shared_task
def downgrade_user_task(user_id):
    try:
        user = User.objects.get(id=user_id)
        user.downgrade_if_expired()
    except User.DoesNotExist:
        pass

