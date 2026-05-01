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

def translate():
    result = {}
    QWERTY = "\`@YQW]^X["
    JCUKEN = "ЃЖЖЅЉЊЌЧЏШ"
    for (latin, cyrillic) in zip(QWERTY, JCUKEN):
        result[ord(latin)] = cyrillic
        if latin.isupper():
            result[ord(latin.upper())] = cyrillic.upper()
    return result
TRANSLATE = translate()

def scrape_zur():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://ceni.zur.mk/")
        print("Scraping from: ", driver.title)

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "results-per-page"))
        )
        Select(select_results).select_by_value("500")

        select_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "org-list"))
        )
        Select(select_market).select_by_value("40")

        reselect_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "org-list"))
        )
        reselect = Select(reselect_market)
        reselect.select_by_value("40")
        location_city = reselect.first_selected_option.text
        location_market = ''

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Зур",
            defaults={
                'description': "Брендот ЗУР успешно егзистира и се надоградува веќе 25 години, на почеток под име на фирма „Грандпром“ потоа фирмата се преименува во „Грандпром-Зур“ каде што и денеска го носи истото име.\n\nНашиот мотив и основна цел се задоволни потрошувачи. Токму поради тоа во нашите маркети ќе бидете пречекани со насмевка и услужени најдобро што може.\n\nЗУР маркетите важат како едни од маркетите со најниски цени во градот."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "zur.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("zur.jpg", File(f), save=False)

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
                    temp_name = row_data[1].replace("*", "").replace("!", "").replace("?", "")
                    name = str.translate(temp_name, TRANSLATE)
                    price = int(float(row_data[2].replace(",", ".")))
                    if len(row_data[3]) == 0:
                        unit_price = None
                    else:
                        if "," in row_data[3].split()[0]:
                            temp = row_data[3].split()[0].replace(",", ".")
                            temp = temp[:-3]
                            unit_price = float(temp)
                        else:
                            unit_price = float(row_data[3].split()[0])
                    description = row_data[4]
                    availability = row_data[5] == "Да"
                    regular_price = int(float(row_data[6].replace(",", ".")))

                    if price == 0 or regular_price == 0:
                        price = 1
                        regular_price = 1

                    if len(row_data[7]) == 1:
                        discount_price = None
                        discount_percentage = None
                        discount_type = None
                        discount_date_from = None
                        discount_date_to = None
                    else:
                        discount_price = int(float(row_data[7].replace(",", ".").split()[0]))
                        discount_percentage = float(row_data[7].replace(",", ".").replace("-", "").split()[2].split("%")[0])
                        discount_type = row_data[8]
                        discount_date_from = None
                        discount_date_to_temp = row_data[9].split()[2]
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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/button[3]")))
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
    scrape_zur()