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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options

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

def scrape_dim():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://dim.mk/cenovnik/")
        print("Scraping from: ", driver.title)

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/p/iframe"))
        )

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "results-per-page"))
        )
        Select(select_results).select_by_value("250")

        select_market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "org-list"))
        )

        select = Select(select_market)
        select.select_by_value("42")
        select_text = select.first_selected_option.text

        location_city = select_text.split()[0]
        location_market = select_text.split()[1]

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Дим",
            defaults={
                'description': "Дим маркет ги отвори своите први 2 маркети во ист ден на 23.12.2017 година во Стајковци и Кисела вода, со што го одбележуваме стартот на една убава и успешна приказна.\n\nОттогаш Дим е застапен на 11 локации во Скопје, 5 локации во Куманово, 1 во Свети Николе и 1 во Берово.\n\nЕкспанзијата е во тек и се очекуваат нови маркети на нови локации во Скопје како и низ целата држава.\n\nНашата цел и принцип на работа пред се, се задоволни потрошувачи.\n\nВо нашите маркети ќе најдете свежо овошје и зеленчук, бренд производи по одлични цени како и наши внимателно одбрани приватни брендови и производи ексклузивни за Дим кои не штедат на квалитет а сепак го штедат вашиот џеб."
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "dim.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("dim.jpg", File(f), save=False)

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
                    temp = row_data[1].replace("*", "").replace("!", "").replace("?", "")
                    name = str.translate(temp, TRANSLATE)
                    price = int(float((row_data[2].replace(",", "."))))
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
                    regular_price = int(float(row_data[6]))
                    if len(row_data[7]) <= 1:
                        discount_price = None
                        discount_percentage = None
                        discount_type = None
                        discount_date_from = None
                        discount_date_to = None
                    else:
                        discount_price = int(float(row_data[7].split()[0].replace(",", ".")))
                        discount_percentage = float(row_data[7].replace("-", "").split()[2].split("%")[0])
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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/div[2]/div/div[2]/div/div/div/div/div[3]/div/button[3]")))
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
    scrape_dim()