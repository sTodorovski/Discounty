import os
import time
import django
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MarketApp.settings")
django.setup()
from django.db import transaction
from discounty.models import Market, Product
from django.core.files import File
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep

def scrape_stokomak():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://stokomak.com.mk/proverka-na-ceni/")
        print("Scraping from: ", driver.title)

        sleep(3)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "cookies-accept-btn"))
        ).click()

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div[1]/div[2]/main/div/article/div/div/div/div/div/iframe"))
        )

        select_quantity = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/div/form/div[3]/select"))
        )
        Select(select_quantity).select_by_value("100")

        select_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "org"))
        )
        select = Select(select_market)
        select.select_by_value("32")

        reselect_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "org"))
        )
        reselect = Select(reselect_market)
        reselect.select_by_value("32")

        location_city = reselect.first_selected_option.text
        location_market = ''

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Стокомак",
            defaults={
                "description": "СТОКОМАК ДОО Е основан во 1997 година со отворањето на првиот малопродажен објект од 50 м² во скопската населба Кисела Вода.\n\nКомпанијата во моментов има околу 1000 вработени, кои претставуваат значаен и најголем капитал за неа.\n\nСтокомак дисконти работи според принципите на светски познатите хард дисконт концепти и нуди ограничен асортиман од околу 1.400 внимателно селектирани производи, со кои им гарантира на своите купувачи најдобар квалитет по најниски цени.\n\nПокрај светски познатите брендови во својот асортиман, компанијата нуди и висококвалитетни производи под сопствени приватни марки, со дури 50% пониски цени. (линк до приватни марки)\n\nВо својата понуда, освен редовните производи, Стокомак има и широк избор на непрехрамбени артикли: текстил, кујнски апарати, мебел, спортска и летна опрема, производи од стакло, градинарски производи, детски играчки и многу други.\n\nСтокомак е значаен и еден од најголемите трговски ланци на домашниот пазар, кој во текот на овие години континуирано ја зголемува довербата кај поголемиот број купувачи на пазарот и доследно ги одржува ниските цени на производите.\n\nКако лидер во малопродажбата во Република Северна Македонија, компанијата е присутна во над 20 градови и има 77 малопродажни објекти.\n\nВо 2025 година, Стокомак започнува со експанзија на српскиот пазар, каде планира да отвори околу 10 нови маркети во текот на годината."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "stokomak.jpg")

        if os.path.exists(image_path):
            market.image.name = "markets/stokomak.jpg"

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
                    price = int(row_data[1].replace(",", ".").split()[0])
                    if len(row_data[2].split()) == 4:
                        unit_price = float(row_data[2].replace(",", ".").split()[2])
                    else:
                        unit_price = None
                    description = row_data[3]
                    availability = row_data[4] == "Да"
                    regular_price = int(row_data[5].split()[0])

                    if len(row_data) == 6:
                        discount_price = None
                        discount_percentage = None
                        discount_type = None
                        discount_date_from = None
                        discount_date_to = None

                    if len(row_data) == 9:
                        regular_price = int(row_data[5].split()[0])
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
    scrape_stokomak()