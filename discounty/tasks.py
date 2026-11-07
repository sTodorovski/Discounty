from celery import shared_task
from django.core.management import call_command


@shared_task(name="discounty.tasks.scrape_all_markets", ignore_result=True)
def scrape_all_markets():
    call_command("scrape_all")
