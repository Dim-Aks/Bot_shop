from django.db import models

from products.models import Product
from users.models import User


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,  verbose_name='Продукт')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзин'
        unique_together = ('user', 'product')  # один и тот же продукт может быть добавлен в корзину единожды

    def __str__(self):
        return f'Корзина пользователя: {self.user.name}, Продукт: {self.product.name}, Количество: {self.quantity}'
