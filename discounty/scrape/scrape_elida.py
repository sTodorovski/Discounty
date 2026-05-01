import os
import django
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MarketApp.settings")
django.setup()
from discounty.models import Market, Product
from django.core.files import File
from django.db import transaction
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

def scrape_elida():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)\

    try:
        driver.get("https://elida.proverkanaceni.mk/")
        print("Scraping from: ", driver.title)

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "perPage"))
        )
        Select(select_results).select_by_value("100")

        select_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "org"))
        )

        select = Select(select_market)
        select.select_by_value("1")
        WebDriverWait(driver, 10).until(EC.staleness_of(select_market))

        reselect_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "org"))
        )
        reselect = Select(reselect_market)
        reselect.select_by_value("1")

        location_city = reselect.first_selected_option.text
        location_market = ''

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Елида",
            defaults={
                "description": "Елида Маркети е ланец на маркети во Куманово и Скопје. Во моментов имаме 30 маркети во Куманово и 5 маркети во Скопје, со повеќе од 300 вработени. Со маркети кои варираат просторно од 80 до 200 метри квадрати, Елида Маркети е лидер во категоријата на средни маркети во прехранбената индустрија во Куманово. Задоволството на нашите вработени е една од главните цели кон кои менаџментот на Елида Маркети континуирано се стреми."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "elida.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("elida.jpg", File(f), save=False)

        market.save()

        market.location_city = location_city
        market.location_market = location_market
        market.last_updated = datetime.now(ZoneInfo("Europe/Skopje"))
        market.save()

        Product.objects.filter(market=market).delete()

        has_next = True

        products = []

        while has_next:
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
                    name = row_data[0]
                    price = int(float(row_data[1].replace(",", ".").split()[0]))
                    if len(row_data[2].split()) == 4:
                        unit_price = float(row_data[2].split()[2])
                    else:
                        unit_price = None
                    description = row_data[3]
                    availability = row_data[4] == "Да"
                    regular_price = int(float(row_data[5].replace(",", ".").split()[0]))
                    if price == 0 or regular_price == 0:
                        price = 1
                        regular_price = 1

                    if len(row_data) == 6:
                        discount_price = None
                        discount_percentage = None
                        discount_type = None
                        discount_date_from = None
                        discount_date_to = None

                    if len(row_data) == 9:
                        discount_price = int(row_data[6].split()[0])
                        discount_percentage = int(row_data[6].split()[2].split('%')[0].split(':')[1])
                        discount_type = row_data[7]
                        discount_date_from_temp = row_data[8].split()[0]
                        discount_date_from = datetime.strptime(discount_date_from_temp, "%d.%m.%Y").date()
                        discount_date_to_temp = row_data[8].split()[2]
                        discount_date_to = datetime.strptime(discount_date_to_temp, "%d.%m.%Y").date()

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

            try:
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "»")))
                old_table = driver.find_element(By.TAG_NAME, "table")
                next_button.click()

                WebDriverWait(driver, 15).until(
                    EC.staleness_of(old_table)
                )
            except:
                has_next = False

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
    scrape_elida()