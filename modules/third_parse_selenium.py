from load_django import *

import re
from decimal import Decimal
from pprint import pprint
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from parser_app.models import Product


URL = "https://brain.com.ua/"
QUERY = "Apple iPhone 15 128GB Black"

SEARCH_INPUT_XPATH = "//input[contains(@class, 'quick-search-input')]"
SEARCH_BUTTON_XPATH = (
    "//input[@type='submit' and contains(@class, 'search-button')]"
)
FIRST_RESULT_XPATH = (
    "(//a[contains(@href, '-p') and contains(@href, '.html')])[1]"
)

CODE_XPATH = "//span[contains(@class, 'br-pr-code-val')]"
TITLE_XPATH = "//div[contains(@class, 'title')]/h1"
PRICE_XPATH = "(//div[contains(@class, 'price-wrapper')]//span)[1]"
PROMO_PRICE_XPATH = (
    "//div[contains(@class, 'price-bonuses-block')]"
    "//div[contains(@class, 'red-price')]"
)
REVIEWS_XPATH = "//a[contains(@class, 'reviews-count')]/span"
IMAGES_XPATH = "//div[contains(@class, 'main-pictures-block')]//img"
CHARACTERISTICS_XPATH = (
    "//div[contains(@class, 'br-pr-chr-item')]"
)

COLOR_LABELS = ("Колір", "Цвет")
MEMORY_LABELS = ("Вбудована пам'ять", "Встроенная память")
MANUFACTURER_LABELS = ("Виробник", "Производитель")
DIAGONAL_LABELS = ("Діагональ екрану", "Диагональ экрана")
RESOLUTION_LABELS = (
    "Роздільна здатність",
    "Разрешение экрана",
)


def get_text(root, xpath):
    try:
        text = root.find_element(
            By.XPATH, xpath
        ).get_attribute("textContent")
    except NoSuchElementException:
        return None

    return text.strip() or None


def get_characteristics(driver):
    characteristics = {}

    for item in driver.find_elements(
        By.XPATH, CHARACTERISTICS_XPATH
    ):
        spans = item.find_elements(By.XPATH, ".//span")

        if len(spans) < 2:
            continue

        key = spans[0].get_attribute("textContent").strip()
        value = spans[1].get_attribute("textContent").strip()

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


def get_photos(driver, page_url):
    photos = []

    for img in driver.find_elements(By.XPATH, IMAGES_XPATH):
        src = img.get_attribute("src") or img.get_attribute("data-src")

        if src:
            photos.append(urljoin(page_url, src))

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


def parse_product(driver):
    characteristics = get_characteristics(driver)

    product = {
        "title": get_text(driver, TITLE_XPATH),
        "color": find_by_label(characteristics, COLOR_LABELS),
        "memory": find_by_label(characteristics, MEMORY_LABELS),
        "manufacturer": find_by_label(
            characteristics, MANUFACTURER_LABELS
        ),
        "price": to_price(get_text(driver, PRICE_XPATH)),
        "promo_price": to_price(
            get_text(driver, PROMO_PRICE_XPATH)
        ),
        "photos": get_photos(driver, driver.current_url),
        "product_code": get_text(driver, CODE_XPATH),
        "reviews_count": to_count(
            get_text(driver, REVIEWS_XPATH)
        ),
        "screen_diagonal": find_by_label(
            characteristics, DIAGONAL_LABELS
        ),
        "screen_resolution": find_by_label(
            characteristics, RESOLUTION_LABELS
        ),
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

    print(
        "Создано" if created else "Уже существует",
        "->",
        obj,
    )


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get(URL)

        search_input = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, SEARCH_INPUT_XPATH)
            )
        )
        search_input.send_keys(QUERY)

        driver.find_element(
            By.XPATH, SEARCH_BUTTON_XPATH
        ).click()

        first_result = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, FIRST_RESULT_XPATH)
            )
        )
        first_result.click()

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, CODE_XPATH)
            )
        )

        product = parse_product(driver)

    except TimeoutException:
        print("Элементы страницы не успели загрузиться")
        return

    finally:
        driver.quit()

    pprint(product)

    if not product["product_code"]:
        print("Код товара не найден, ничего не сохранено")
        return

    save_product(product)


if __name__ == "__main__":
    main()