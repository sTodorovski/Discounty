import time
from django.core.management import BaseCommand
from discounty.scrape.scrape_dim import scrape_dim
from discounty.scrape.scrape_elida import scrape_elida
from discounty.scrape.scrape_kam import scrape_kam
from discounty.scrape.scrape_kipper import scrape_kipper
from discounty.scrape.scrape_kitgo import scrape_kitgo
from discounty.scrape.scrape_konto import scrape_konto
from discounty.scrape.scrape_ramstore import scrape_ramstore
from discounty.scrape.scrape_stokomak import scrape_stokomak
from discounty.scrape.scrape_tinex import scrape_tinex
from discounty.scrape.scrape_vero import scrape_vero
from discounty.scrape.scrape_zito import scrape_zito
from discounty.scrape.scrape_zur import scrape_zur


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_time = time.time()

        self.stdout.write(self.style.SUCCESS("Starting all scrapers!"))

        scrapers = [
            scrape_kam,
            scrape_kipper,
            scrape_elida,
            scrape_stokomak,
            scrape_dim,
            scrape_tinex,
            scrape_zur,
            scrape_konto,
            scrape_zito,
            scrape_ramstore,
            scrape_vero,
            scrape_kitgo,
        ]

        success = 0
        failed = 0

        for scraper in scrapers:
            try:
                scraper()
                success += 1
            except:
                failed += 1

        end_time = time.time()
        duration = end_time - start_time

        minutes = int(duration // 60)
        seconds = int(duration % 60)

        self.stdout.write(self.style.SUCCESS(
            f"All scrapers finished in {minutes}m {seconds}s"
        ))

        self.stdout.write(f"Success: {success}, Failed: {failed}")