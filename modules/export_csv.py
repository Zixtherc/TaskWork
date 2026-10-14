
import sys
import os
import csv
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "braincom_project.settings")

import django

django.setup()

from parser_app.models import Product


def export_to_csv():
    file_path = ROOT_DIR / "products.csv"
    products = Product.objects.all()

    fieldnames = [
        "id",
        "title",
        "color",
        "memory",
        "manufacturer",
        "price",
        "promo_price",
        "photos",
        "product_code",
        "reviews_count",
        "screen_diagonal",
        "screen_resolution",
        "characteristics",
    ]

    with open(
        file_path,
        mode="w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            row = {
                "id": product.id,
                "title": product.title,
                "color": product.color,
                "memory": product.memory,
                "manufacturer": product.manufacturer,
                "price": product.price,
                "promo_price": product.promo_price,
                "photos": json.dumps(
                    product.photos,
                    ensure_ascii=False,
                ),
                "product_code": product.product_code,
                "reviews_count": product.reviews_count,
                "screen_diagonal": product.screen_diagonal,
                "screen_resolution": product.screen_resolution,
                "characteristics": json.dumps(
                    product.characteristics,
                    ensure_ascii=False,
                ),
            }

            writer.writerow(row)

    print(f"Экспорт завершен успешно. Файл сохранен: {file_path}")


if __name__ == "__main__":
    export_to_csv()
