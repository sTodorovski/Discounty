import os
import time
import django
from MarketApp import settings
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
from selenium.webdriver.support.wait import WebDriverWait

def translate():
    result = {}
    QWERTY = "ABVGD\E@ZYIJKLQMNWOPRST]UFHC^X["
    JCUKEN = "АБВГДЃЕЖЗЅИЈКЛЉМНЊОПРСТЌУФХЦЧЏШ"
    for (latin, cyrillic) in zip(QWERTY, JCUKEN):
        result[ord(latin)] = cyrillic
        if latin.isupper():
            result[ord(latin.upper())] = cyrillic.upper()
    return result
TRANSLATE = translate()

def scrape_vero():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://pricelist.vero.com.mk/94_1.html")
        print("Scraping from: ", driver.title)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        location_city = "Тетово"
        location_market = driver.find_element(By.TAG_NAME, "h1").text

        market, _ = Market.objects.get_or_create(
            name="Веро",
            defaults={
                "description": "Компанијата „Веропулос“ е првата странска компанија од малопродажниот сектор која влезе на македонскиот пазар во 1997 година, отворајќи го првиот модерен Веро супермаркет во Скопје.\n\nВодејќи се од основното начело во работењето, „Сѐ на едно место“, овозможуваме широк асортиман на најквалитетни домашни и увозни производи по најконкурентни цени и премиум услуга, со што доследно се грижиме за потребите на потрошувачите, нивното здравје и максимално задоволство.\n\nСо внимателен избор на нашите добавувачи, осигуруваме квалитет и безбедност на производите. Строгата контрола на синџирот на снабдување ни дава сигурност дека и нашите партнери се придржуваат кон највисоките стандарди за квалитет, безбедност и здравје.\n\nПреку континуирана посветеност во работата, Веро е синоним за врвен квалитет и лидер во малопродажбата кој воведува нови трендови, поставува високи стандарди и овозможува уникатно шопинг искуство за сите генерации."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "vero.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("vero.jpg", File(f), save=False)

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
                    if len(row_data) == 10:
                        name = str.translate(row_data[0], TRANSLATE)
                        price = int(row_data[1])
                        if len(row_data[2].split()) == 2:
                            unit_price = float(row_data[2].replace(",", ".").split()[0])
                        else:
                            unit_price = None
                        availability = row_data[3] == "Да"
                        description = row_data[4]
                        regular_price = int(row_data[5])
                        if len(row_data[6]) != 0:
                            discount_price = int(row_data[6])
                            discount_percentage = abs(float(row_data[7].replace(",", ".")[:2]))
                            discount_type = row_data[8]
                            discount_date_from_temp = row_data[9].split(" - ")[0]
                            discount_date_from = datetime.strptime(discount_date_from_temp, "%d/%m/%Y").date()
                            discount_date_to_temp = row_data[9].split(" - ")[1]
                            discount_date_to = datetime.strptime(discount_date_to_temp, "%d/%m/%Y").date()
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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "🠊")))
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
    scrape_vero()