from load_django import *

import re
from decimal import Decimal
from pprint import pprint
from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from parser_app.models import Product


URL = "https://brain.com.ua/"
QUERY = "Apple iPhone 15 128GB Black"

SEARCH_INPUT_XPATHS = (
    "//input[contains(@class, 'quick-search-input')]",
    "//input[@type='search']",
    "//input[contains(@name, 'search') or contains(@id, 'search')]",
    "//input[contains(@placeholder, 'Пошук') or contains(@placeholder, 'пошук')]",
)
SEARCH_BUTTON_XPATHS = (
    "//form[.//input[contains(@class, 'quick-search-input')]]//*[@type='submit']",
    "//form[.//input[@type='search']]//*[@type='submit']",
)
FIRST_RESULT_XPATH = "(//a[contains(@href, '-p') and contains(@href, '.html')])[1]"

CODE_XPATH = "//span[contains(@class, 'br-pr-code-val')]"
TITLE_XPATH = "//div[contains(@class, 'title')]/h1"
PRICE_XPATH = "(//div[contains(@class, 'price-wrapper')]//span)[1]"
PROMO_PRICE_XPATH = "//div[contains(@class, 'price-bonuses-block')]//div[contains(@class, 'red-price')]"
REVIEWS_XPATH = "//a[contains(@class, 'reviews-count')]/span"
IMAGES_XPATH = "//div[contains(@class, 'main-pictures-block')]//img"
CHARACTERISTICS_XPATH = "//div[contains(@class, 'br-pr-chr-item')]"

COLOR_LABELS = ("Колір", "Цвет")
MEMORY_LABELS = ("Вбудована пам'ять", "Встроенная память")
MANUFACTURER_LABELS = ("Виробник", "Производитель")
DIAGONAL_LABELS = ("Діагональ екрану", "Диагональ экрана")
RESOLUTION_LABELS = ("Роздільна здатність", "Разрешение экрана")


def launch_browser(playwright):
    for channel in ("msedge", "chrome", None):
        try:
            return playwright.chromium.launch(channel=channel, headless=False)
        except PlaywrightError:
            print(f"Браузер '{channel or 'bundled chromium'}' недоступен")

    raise RuntimeError(
        "Браузер не найд"
    )


def clean(text):
    return " ".join(text.split())


def find_visible(page, xpaths):
    for xpath in xpaths:
        locator = page.locator(f"xpath= {xpath}")
        if locator.count():
            return locator.first
    return None


def print_controls(page):
    controls = page.evaluate(
        """() => [...document.querySelectorAll('input, button')]
            .filter(e => e.offsetParent !== null)
            .map(e => ({tag: e.tagName.toLowerCase(), type: e.type, id: e.id,
                        name: e.name, cls: e.className,
                        placeholder: e.placeholder}))"""
    )
    pprint(controls)


def get_text(page, xpath):
    try:
        text = page.locator(f"xpath={xpath}").first.text_content(timeout=3000)
    except PlaywrightTimeoutError:
        return None
    return clean(text) if text and clean(text) else None


def get_characteristics(page):
    characteristics = {}
    for item in page.locator(f"xpath={CHARACTERISTICS_XPATH}").all():
        spans = item.locator("xpath=.//span").all_text_contents()
        if len(spans) < 2:
            continue
        key = clean(spans[0])
        value = clean(spans[1])
        if key and value:
            characteristics[key] = value
    return characteristics


def find_by_label(characteristics, labels):
    for label in labels:
        for key, value in characteristics.items():
            if key.rstrip(": ").lower() == label.lower():
                return value
    for label in labels:
        for key, value in characteristics.items():
            if label.lower() in key.lower():
                return value
    return None


def get_photos(page):
    photos = []
    for img in page.locator(f"xpath= {IMAGES_XPATH}").all():
        src = img.get_attribute("src") or img.get_attribute("data-src")
        if src:
            photos.append(urljoin(page.url, src))
    return list(dict.fromkeys(photos))


def to_price(text):
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    return Decimal(digits) if digits else None


def to_count(text):
    if not text:
        return 0
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else 0


def parse_product(page):
    characteristics = get_characteristics(page)

    product = {
        "title": get_text(page, TITLE_XPATH),
        "color": find_by_label(characteristics, COLOR_LABELS),
        "memory": find_by_label(characteristics, MEMORY_LABELS),
        "manufacturer": find_by_label(characteristics, MANUFACTURER_LABELS),
        "price": to_price(get_text(page, PRICE_XPATH)),
        "promo_price": to_price(get_text(page, PROMO_PRICE_XPATH)),
        "photos": get_photos(page),
        "product_code": get_text(page, CODE_XPATH),
        "reviews_count": to_count(get_text(page, REVIEWS_XPATH)),
        "screen_diagonal": find_by_label(characteristics, DIAGONAL_LABELS),
        "screen_resolution": find_by_label(characteristics, RESOLUTION_LABELS),
        "characteristics": characteristics,
    }
    return product


def save_product(product):
    obj, created = Product.objects.get_or_create(
        title=product["title"],
        color=product["color"],
        memory=product["memory"],
        manufacturer=product["manufacturer"],
        price=product["price"],
        promo_price=product["promo_price"],
        photos=product["photos"],
        product_code=product["product_code"],
        reviews_count=product["reviews_count"],
        screen_diagonal=product["screen_diagonal"],
        screen_resolution=product["screen_resolution"],
        characteristics=product["characteristics"],
    )
    print("Создано" if created else "Уже существует", "--", obj)


def main():
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        page = browser.new_page()

        step = "open main page"
        try:
            page.goto(URL)

            step = "find search input"
            search_input = find_visible(page, SEARCH_INPUT_XPATHS)
            if search_input is None:
                print("Поле поиска не найдено, видимые элементы управления на странице:")
                print_controls(page)
                return
            search_input.fill(QUERY, timeout=15000)

            step = "submit the search"
            search_button = find_visible(page, SEARCH_BUTTON_XPATHS)
            if search_button is None:
                search_input.press("Enter")
            else:
                search_button.click(timeout=15000)

            step = f"find first result: {FIRST_RESULT_XPATH}"
            page.locator(f"xpath={FIRST_RESULT_XPATH}").first.click(timeout=15000)

            step = f"find product code: {CODE_XPATH}"
            page.wait_for_selector(f"xpath={CODE_XPATH}", timeout=15000)

            product = parse_product(page)
        except PlaywrightTimeoutError:
            print("Превышено время ожидания на шаге -", step)
            print("Текущий URL -", page.url)
            return
        finally:
            browser.close()

    pprint(product)

    if not product["product_code"]:
        print("Код товара не найден, ничего не сохранено")
        return

    save_product(product)


if __name__ == "__main__":
    main()