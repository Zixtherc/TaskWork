
from load_django import *

from decimal import Decimal
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from parser_app.models import Product


URL = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_13_Pro_256Gb_Gold_Grade_B_USED_iP13Pr25Gol_B-p1339097.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
}


def get_text(element):
    return element.get_text(" ", strip=True) if element else None


def get_characteristics(soup):
    result = {}

    for item in soup.select("div.br-pr-chr-item"):
        spans = item.find_all("span", limit=2)

        if len(spans) == 2:
            key, value = map(get_text, spans)
            if key and value:
                result[key] = value

    return result


def get_images(soup, url):
    block = soup.select_one("div.main-pictures-block")
    if not block:
        return []

    return list(dict.fromkeys(
        urljoin(url, img.get("src") or img.get("data-src"))
        for img in block.find_all("img")
        if img.get("src") or img.get("data-src")
    ))


def parse_product(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    chars = get_characteristics(soup)

    resolution = next(
        (v for k, v in chars.items()
         if "роздільна здатність" in k.lower()
         or "разрешение экрана" in k.lower()
         or "screen resolution" in k.lower()),
        None,
    )

    def labeled(label):
        return next(
            (v for k, v in chars.items() if k == label),
            None,
        )

    promo = soup.select_one("div.price-bonuses-block div.red-price")
    reviews = soup.select_one("a.reviews-count span")

    return {
        "title": get_text(soup.select_one("div.title h1")),
        "color": labeled("Колір"),
        "built_in_memory": labeled("Вбудована пам'ять"),
        "manufacturer": labeled("Виробник"),
        "regular_price": get_text(soup.select_one("div.price-wrapper span")),
        "promotional_price": get_text(promo),
        "images": get_images(soup, url),
        "code": get_text(soup.select_one("span.br-pr-code-val")),
        "reviews_count": get_text(reviews),
        "screen_diagonal": labeled("Діагональ екрану"),
        "screen_resolution": resolution,
        "characteristics": chars,
    }


def save_product(data):
    def price(value):
        return Decimal(value.replace(" ", "").replace("\xa0", "")) if value else None

    product, created = Product.objects.update_or_create(
        product_code=data["code"],
        defaults={
            "title": data["title"],
            "color": data["color"],
            "memory": data["built_in_memory"],
            "manufacturer": data["manufacturer"],
            "price": price(data["regular_price"]),
            "promo_price": price(data["promotional_price"]),
            "photos": data["images"],
            "reviews_count": int(data["reviews_count"] or 0),
            "screen_diagonal": data["screen_diagonal"],
            "screen_resolution": data["screen_resolution"],
            "characteristics": data["characteristics"],
        },
    )

    print(f"{'Создан' if created else 'Обновлён'} товар: {product.title}")
    print("Разрешение экрана:", product.screen_resolution)


def main():
    data = parse_product(URL)

    if not data["code"]:
        raise ValueError("Не удалось получить код товара")

    save_product(data)

if __name__ == "__main__":
    main()