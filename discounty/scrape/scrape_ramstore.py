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

def scrape_ramstore():
    start_time = time.time()

    options = Options()
    options.add_argument("--headless")

    options.set_preference("webdriver_accept_untrusted_certs", True)
    options.set_preference("webdriver_assume_untrusted_issuer", False)

    driver = webdriver.Firefox(options=options)

    try:
        driver.get("https://ramstore.com.mk/marketi/ramstore-tetovo/")
        print("Scraping from: ", driver.title)

        text = driver.title

        location_city = text.split()[1]
        location_market = text.split()[0]

        select_results = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "productsTable_length"))
        )
        Select(select_results).select_by_value("100")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        market, _ = Market.objects.get_or_create(
            name="Ramstore",
            defaults={
                'description': "Рамстор, кој во Македонија започна со работа во 2005 година е дел од CITY Plaza Holding, кој е присутен на македонскиот пазар 20 години.\n\nКако резултат на успешната работа и квалитетната услуга во малопродажниот сектор на Македонија во последните 20 години, а во насока на својата мисија и визија денес Рамстор ги нуди своите услуги во 8 различни градови низ Македонија со вкупно 27 маркети и една онлајн продавница на вкупна површина од 27.000 m2\n\nПорастот на бројот на вработени во развиените економии придонесува за растење на желбата кај поединците да одвојат повеќе време за себе, помалку време да поминуваат во купување. Во оваа смисла, нашите клиенти сакаат блиску до местото на живеење и работа да најдат разни видови производи од повеќе брендови и купувањето да биде брзо.\n\nСето ова укажува на долгорочните сериозни планови на Рамстор во согласнст со растот во Македонија кој сеуште трае. Денес во Македонија имаме вкупно 750 вработени и нормално новите инвестиции со себе ќе донесат и нови вработувања.\n\nВо текот на овие 20 години, додека им пружавме различно искуство во купувањето на нашитеклиенти во еден сосема нов свет на пазарењето, си поставивме за цел да ги пренесеме свеста за квалитетна услуга и квалитетни производи. На најдобар можен начин ги пречекуваме нашите купувачи во супермаркетите на Рамстор нудејќи им разновидни и свежи производи. Во овој период не само што имавме физички инвестиции туку инвестиравме и во безбедноста на нашите купувачи стекнувајќи се со сертификатите за безбедност на ISO 22000:2005 и HACCP.",
            }
        )

        image_path = os.path.join(settings.MEDIA_ROOT, "markets", "ramstore.jpg")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                market.image.save("ramstore.jpg", File(f), save=False)

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
                    price = int(float(row_data[1].replace(",", ".")))

                    if len(row_data[2].split()[0]) <= 1:
                        unit_price = None
                    elif len(row_data[2].split()[2]) > 1:
                        unit_price = float(row_data[2].split()[2].split("=")[1].replace(",", ".")[:-3])
                    else:
                        unit_price = None

                    description = row_data[3]
                    availability = row_data[4] == "ДА"
                    regular_price = price

                    if len(row_data[5]) > 0:
                        discount_price = int(float(row_data[6].replace(",", ".").split()[0]))
                        discount_percentage = float(row_data[6].replace(",", ".").replace("-", "").split()[1].split("%")[0])
                        discount_type = row_data[8]
                        discount_date_from_temp = row_data[9].split()[0]
                        discount_date_from = datetime.strptime(discount_date_from_temp, "%d.%m.%Y").date()
                        discount_date_to_temp = row_data[9].split()[2]
                        discount_date_to = datetime.strptime(discount_date_to_temp, "%d.%m.%Y").date()
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
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Следно")))
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
    scrape_ramstore()