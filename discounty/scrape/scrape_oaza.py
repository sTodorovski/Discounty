import os
import time
from operator import truediv

import django
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MarketApp.settings")
django.setup()
from discounty.models import Market, Product
from django.core.files import File
from django.db import transaction
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait


def scrape_oaza():

    start_time = time.time()
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://oazamarket.mk/")
        print("Scraping from: ", driver.title)

        select_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "selected_org"))
        )
        Select(select_market).select_by_value("7")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Oaza",
            defaults={
                'description': "30 години успешна работа , години макотрпна работа,заедно со целиот наш тим,чекор по чекорпораснавме во успешна компанија со 4 маркети кои го задоволуваат пазарот и своите клиенти.„ОАЗА“ е друштво, кое е основано во далечната 1992 година. Оваа година славиме точно 30 години од отворањето.",
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "oaza.jpg")

        if os.path.exists(image_path):
            market.image.name = "markets/oaza.jpg"

        market.save()

        market.location_city = "Tetovo"
        market.location_market = "Tetovo"
        market.last_updated = datetime.now(ZoneInfo("Europe/Skopje"))
        market.save()

        Product.objects.filter(market=market).delete()

        # has_next = True

        products = []

        # while has_next:
        table_rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
        )

        for row in table_rows:
            table_data = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            for data in table_data:
                row_data.append(data.text)

            if not row_data:
                continue

            try:
                name = row_data[1]
                price = int(row_data[2])

                if row_data[3] == "":
                    unit_price = None
                else:
                    unit_price = float(int(row_data[3]))

                description = row_data[4]

                if row_data[5] == "Да":
                    availability = True
                else:
                    availability = False

                regular_price = int(row_data[6])

                if row_data[7] == "-":
                    discount_price = None
                    discount_percentage = None
                else:
                    discount_price = int(row_data[7])
                    discount_percentage = int(discount_price / price * 100)

                if row_data[8] == "":
                    discount_type = None
                else:
                    discount_type = row_data[8]

                if row_data[9] == "":
                    discount_date_from = None
                    discount_date_to = None
                else:
                    discount_date_from = row_data[9]
                    discount_date_to = row_data[9]

                products.append(
                    Product(
                        name=name,
                        price=price,
                        unit_price=unit_price,
                        description=description,
                        availability=availability,
                        regular_price=regular_price,
                        discount_price=discount_price,
                        discount_percentage=discount_percentage,
                        discount_type=discount_type,
                        discount_date_from=discount_date_from,
                        discount_date_to=discount_date_to,
                        market=market,
                    )
                )

            except Exception as e:
                print("FAILED ROW:", row_data)
                print("Error: ", e)
                continue

        with transaction.atomic():
            Product.objects.bulk_create(products, batch_size=1000)

    finally:
        end_time = time.time()

        duration = end_time - start_time

        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print(f"Finished scraping: {driver.title} in {minutes}m {seconds}s")

        driver.quit()





if __name__ == "__main__":
    scrape_oaza()