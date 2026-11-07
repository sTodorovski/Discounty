import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MarketApp.settings")

app = Celery("MarketApp")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    timezone="Europe/Skopje",
    enable_utc=True,
)

app.conf.beat_schedule = {
    "scrape-all-markets-every-day-at-9": {
        "task": "discounty.tasks.scrape_all_markets",
        "schedule": crontab(hour=9, minute=0),
    },
}

app.autodiscover_tasks()
