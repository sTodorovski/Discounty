import os
import django
from django.core.files import File
from MarketApp import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MarketApp.settings")
django.setup()
import time
from zoneinfo import ZoneInfo
from django.db import transaction
from discounty.models import Product, Market
import pdfplumber
from datetime import datetime
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "kam_data")
os.makedirs(PDF_DIR, exist_ok=True)

today = datetime.now()
URL = f"https://kam.com.mk/{today.year}/{today.month:02d}/{today.day:02d}/90.pdf"
PDF_PATH = os.path.join(PDF_DIR, "kam_data.pdf")

def download_pdf():
    response = requests.get(URL)
    response.raise_for_status()

    with open(PDF_PATH, "wb") as f:
        f.write(response.content)

def scrape_kam():
    start_time = time.time()

    print("Scraping from: KAM - Тетово")

    download_pdf()

    location_city = "Тетово"
    location_market = "РЕМОЛ"

    market, created = Market.objects.get_or_create(
        name="КАМ",
        defaults={
            "description": "КАМ ДОО датира од 1995 година, со отворањето на првата продавница во приземјето на Градски Трговски Центар во Скопје, од страна на фирмата основач КАМФУД (сега КАМ ИМОБИЛИЕН).\n\nКАМ Маркет е првиот синџир маркети од типот хард-дисконти коишто постојат на домашниот пазар. Во моментов во Македонија работат 86 маркети, а компанијата брои над 1500 вработени.\n\nПред 8 години, КАМ Маркет влезе и се позиционираше и на пазарот во соседна Бугарија, кадешто во моментов со успех работат 26 маркети.",
        }
    )

    image_path = os.path.join(settings.MEDIA_ROOT, "markets", "kam.jpg")

    if os.path.exists(image_path):
        market.image.name = "markets/kam.jpg"

    market.save()

    market.location_city = location_city
    market.location_market = location_market
    market.last_updated = datetime.now(ZoneInfo("Europe/Skopje"))
    market.save()

    data = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                data.extend(table)

    products = []

    for row in data:
        try:
            if row[0] is not None:
                if row[0] != "Назив на\nстока-\nпроизвод":
                    name = row[0].replace("\n", " ")
                    price = int(row[1].split("ден.")[0].replace(".", ""))

                    if len(row[2].replace("\n", "")) != 0:
                        unit_price = float(row[2].replace("\n", "").split(" = ")[1].split("ден.")[0])
                    else:
                        unit_price = None

                    if len(row[3].replace("\n", " ")) != 0:
                        description = row[3].replace("\n", " ")
                    else:
                        description = " "

                    if row[4] == "Да":
                        availability = True
                    else:
                        availability = False

                    if len(row[5]) != 0:
                        regular_price = int(row[5].split("ден.")[0].replace(".", ""))
                    else:
                        regular_price = price

                    if len(row[6]) != 0:
                        discount_price = int(row[6].replace("\n", " ").split("ден.")[0].replace(".", ""))
                        discount_type = row[7]
                        discount_date_from_temp = row[8].replace("\n", " ").split(" до ")[0]
                        discount_date_from = datetime.strptime(discount_date_from_temp, "%d.%m.%Y").date()
                        discount_date_to_temp = row[8].replace("\n", " ").split(" до ")[1]
                        discount_date_to = datetime.strptime(discount_date_to_temp, "%d.%m.%Y").date()
                        if len(row[6].replace("\n", " ").split("ден.")[1]) != 0:
                            discount_percentage = float(row[6].replace("\n", " ").split("ден.")[1].split("Попуст: ")[1].replace("%", ""))
                        else:
                            discount_percentage = 0.0
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
                            market=market
                        )
                    )

        except Exception as e:
            print("FAILED ROW:", row)
            print("Error:", e)
            continue

    with transaction.atomic():
        Product.objects.filter(market=market).delete()
        Product.objects.bulk_create(products, batch_size=1000)

    end_time = time.time()
    duration = end_time - start_time

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print(f"Finished scraping: КАМ in {minutes}m {seconds}s")

if __name__ == "__main__":
    scrape_kam()