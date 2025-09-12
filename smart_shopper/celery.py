# smart_shopper/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_shopper.settings')

app = Celery('smart_shopper')

# Using in-memory broker
app.conf.broker_url = 'memory://'
app.conf.result_backend = 'rpc://'
app.conf.task_always_eager = True  # Run tasks synchronously for development

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()