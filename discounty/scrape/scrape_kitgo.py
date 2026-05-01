import os
import time
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

def translate():
    result = {}
    QWERTY = "ABVGD\\E`@ZYIJKLQMNWOPRST]UFHC^X["
    JCUKEN = "АБВГДЃЕЖЖЗЅИЈКЛЉМНЊОПРСТЌУФХЦЧЏШ"
    for (latin, cyrillic) in zip(QWERTY, JCUKEN):
        result[ord(latin)] = cyrillic
        if latin.isupper():
            result[ord(latin.upper())] = cyrillic.upper()
    return result
TRANSLATE = translate()

def scrape_kitgo():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://www.superkitgo.mk/table.php?market=market75")
        print("Scraping from: ", driver.title)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loadingOverlay"))
        )

        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "loadingOverlay"))
        )

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "perPageSelect"))
        )
        Select(select_results).select_by_value("500")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loadingOverlay"))
        )

        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "loadingOverlay"))
        )

        location_city = "Скопје"
        location_market = "Џевахир"

        market, _ = Market.objects.get_or_create(
            name="Кит-Го",
            defaults={
                "description": "Специјалитети по супер цена\n\nОдлични промоции секој ден! Искористете ги нашите акции и дополнителни попусти на избрани артикли."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "kit-go.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("kitgo.jpg", File(f), save=False)

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
                    if len(row_data) > 1:
                        name = str.translate(row_data[1], TRANSLATE)
                        description = row_data[2]
                        availability = row_data[3] == "DA"
                        price = int(float(row_data[5].split()[0][:-3].replace(",", ".").replace(".", "")))
                        unit_price = float(row_data[4].split()[0][:-3])
                        regular_price = int(float(row_data[6].split()[0][:-3].replace(",", ".").replace(".", "")))

                        if int(row_data[7].split()[0]) > 0:
                            discount_price = int(row_data[7].split()[0])
                            discount_type = row_data[9]
                            discount_date_from_temp = row_data[10].split()[0]
                            discount_date_from = datetime.strptime(discount_date_from_temp, "%Y-%m-%d").date()
                            discount_date_to_temp = row_data[10].split()[2]
                            discount_date_to = datetime.strptime(discount_date_to_temp, "%Y-%m-%d").date()
                            if len(row_data[8]) > 2:
                                discount_percentage = float(row_data[8].replace("-", "").replace(",", ".")[:-1])
                            else:
                                discount_percentage = None

                        else:
                            discount_price = None
                            discount_percentage = None
                            discount_type = None
                            discount_date_from = None
                            discount_date_to = None

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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "fa-chevron-right")))
                old_first_row = driver.find_element(By.CSS_SELECTOR, "table tbody tr")
                next_button.click()

                WebDriverWait(driver, 15).until(
                    EC.staleness_of(old_first_row)
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
    scrape_kitgo()