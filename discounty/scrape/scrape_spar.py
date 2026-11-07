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

def scrape_spar():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://spar.mk/pricelist/59")
        print("Scraping from: ", driver.title)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "CookieBanner-module-scss-module__iE5W0W__accept"))
        ).click()

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/section/div[2]/select[2]"))
        )
        Select(select_results).select_by_value("500")

        time.sleep(0.5)

        market, _ = Market.objects.get_or_create(
            name="Spar",
            defaults={
                'description': "Мисијата на SPAR International е да обезбеди брендот SPAR да остане водечки светски синџир на малопродажба на храна и да продолжиме да го развиваме нашиот бренд, нашето присуство и нашите партнери преку заедничка работа за подобрување на конкурентноста, продуктивноста и профитабилноста на нашите малопродажни и големопродажни партнери ширум светот.",
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "spar.jpg")

        if os.path.exists(image_path):
            market.image.name = "markets/spar.jpg"

        market.save()

        market.location_city = "Tetovo"
        market.location_market = "Tetovo"
        market.last_updated = datetime.now(ZoneInfo("Europe/Skopje"))
        market.save()

        Product.objects.filter(market=market).delete()

        has_next = True

        products = []

        while has_next:
            table_rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
            )

            time.sleep(0.5)

            for row in table_rows:
                table_data = row.find_elements(By.TAG_NAME, "td")
                row_data = []
                for data in table_data:
                    row_data.append(data.text)

                if not row_data:
                    continue

                try:
                    if len(row_data) > 1:
                        if row_data[2] == "да":
                            name = str.translate(row_data[0], TRANSLATE)
                            description = row_data[1]
                            availability = True
                            price = int(row_data[5])
                            unit_price = float(row_data[3])
                            regular_price = float(row_data[5])

                            if row_data[7] == "0":
                                discount_price = None
                                discount_percentage = None
                                discount_type = None
                                discount_date_from = None
                                discount_date_to = None
                            else:
                                discount_price = int(row_data[6])
                                discount_percentage = float(int(row_data[7]))
                                discount_type = row_data[8]
                                discount_date_from_temp = row_data[9].split(" - ")[0]
                                discount_date_from = datetime.strptime(discount_date_from_temp, "%Y-%m-%d").date()
                                discount_date_to_temp = row_data[9].split(" - ")[1]
                                discount_date_to = datetime.strptime(discount_date_to_temp, "%Y-%m-%d").date()

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

            # Product.objects.bulk_create(products)
            # products.clear()

            try:
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/section/div[4]/button[2]")))
                old_first_row = driver.find_element(By.CSS_SELECTOR, "table tbody tr")
                next_button.click()

                WebDriverWait(driver, 15).until(
                    EC.staleness_of(old_first_row)
                )

                time.sleep(0.5)
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
        scrape_spar()