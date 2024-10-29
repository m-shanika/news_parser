import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

app = Celery("configs")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-notifications-every-hour': {
        'task': 'apps.tasks.check_notifications',
        'schedule': crontab(minute="*/10"),
    },
    'check-news-every-day': { 
        'task': 'apps.tasks.check_news',
        'schedule': crontab(minute="*/10"),
    },
    'check-news-media-every-day': {
        'task': 'apps.tasks.check_news_media',
        'schedule': crontab(minute="*/10"),
    },
    'check-news-seller-every-day': {
        'task': 'apps.tasks.check_news_seller',  
        'schedule': crontab(minute="*/10"),
    },
    'check-ozon-news-every-hour': {
        'task': 'apps.tasks.check_ozon_news',
        'schedule': crontab(minute="0", hour="*/10"),
    },

}
