import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AI.settings")

app = Celery("AI")

app.config_from_object("django.conf:settings", namespace="CELERY")


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

broker_connection_retry_on_startup = True

# app.conf.beat_schedule = {
#     'run-at-midnight': {
#         'task': 'customauth.tasks.check_and_downgrade_expired_premium_users',
#         'schedule': crontab(hour=0, minute=0 ),
#     },
# }
