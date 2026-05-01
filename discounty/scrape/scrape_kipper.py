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
from time import sleep

def scrape_kipper():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://kipper.mk/mk/kipper-61/")
        print("Scraping from: ", driver.title)

        driver.execute_script("return document.body.scrollHeight;")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "products_processing"))
        )

        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "products_processing"))
        )

        location_city = driver.find_element(By.CSS_SELECTOR, '[data-id="d1c2f1c"]').text
        location_market = driver.find_element(By.CSS_SELECTOR, '[data-id="f71984f"]').text

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "products_processing"))
        )

        select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dt-length-0"))
        )
        Select(select).select_by_value("100")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "products_processing"))
        )

        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "products_processing"))
        )

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Kipper",
            defaults={
                'description': "Kipper е ланец на маркети во сегментот на хард попуст. Компанијата е основана во Април 2011 година на македонскиот пазар и досега покажува континуиран раст низ годините. Компанијата работи на поголем дел од територијата на Северна Македонија.\n\nГлавниот фокус на компанијата се нејзините купувачи, со најповолни цени достапни на пазарот, притоа задржувајќи го највисокиот квалитет во своите производи.\n\nСедиштето на компанијата е во Желино, на 10 км од Тетово. Централниот магацин е исто така составен дел од дирекцијата.\n\nСо цел да се постигне главниот фокус, да се испорача најдобар квалитет за најповолна цена на пазарот, Киппер имплементира функции во својата секојдневна оперативна рутина како:\n- Ефикасност во логистиката\n- Управување со работна сила\n- Портфолио на производи\n- Маркетинг со ниски трошоци\n- Наши брендови"
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "kipper.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("kipper.jpg", File(f), save=False)

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

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "td"))
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
                    if row_data[1] is int:
                        price = int(row_data[1].split()[0])
                    else:
                        price = int(row_data[5][:-4])

                    if len(row_data[2].split()) > 0:
                        if "=" not in row_data[2]:
                            unit_price = None
                        elif len(row_data[2].split("=")[0]) > 0:
                            unit_price = float(row_data[2].split("=")[1].replace(",", ".")[:-4])
                        else:
                            unit_price = None
                    else:
                        unit_price = None

                    description = row_data[3]
                    availability = row_data[4] == "ДА"

                    regular_price = int(row_data[5][:-4])

                    if len(row_data[6].split()) > 0:
                        discount_price = int(row_data[6].split()[0])
                        discount_percentage = float(row_data[6].replace("-", "").split()[2][1:][:-2])
                        discount_type = row_data[7]
                        if len(row_data[8].split()) > 0:
                            discount_date_from_temp = row_data[8].split()[0]
                            discount_date_from = datetime.strptime(discount_date_from_temp, "%Y-%m-%d").date()
                            discount_date_to_temp = row_data[8].split()[2]
                            discount_date_to = datetime.strptime(discount_date_to_temp, "%Y-%m-%d").date()
                        else:
                            discount_date_from = None
                            discount_date_to = None
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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "next")))
                old_first_row = driver.find_element(By.CSS_SELECTOR, "table tbody tr")
                next_button.click()

                WebDriverWait(driver, 15).until(
                    EC.staleness_of(old_first_row)
                )
                sleep(1)
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
    scrape_kipper()