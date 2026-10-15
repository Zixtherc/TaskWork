from django.db import models

class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название товара")
    color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Цвет")
    memory = models.CharField(max_length=50, blank=True, null=True, verbose_name="Объем памяти")
    manufacturer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Производитель")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Обычная цена")
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Акционная цена")
    photos = models.JSONField(default=list, blank=True, verbose_name="Ссылки на фото")
    product_code = models.CharField(max_length=100, db_index=True, verbose_name="Код товара")
    reviews_count = models.IntegerField(default=0, verbose_name="Количество отзывов")
    screen_diagonal = models.CharField(max_length=50, blank=True, null=True, verbose_name="Диагональ экрана")
    screen_resolution = models.CharField(max_length=100, blank=True, null=True, verbose_name="Разрешение дисплея")
    characteristics = models.JSONField(default=dict, blank=True, verbose_name="Характеристики")

    def __str__(self):
        return self.title