from django.db import models
import logging

logger = logging.getLogger('users')


class User(models.Model):
    user_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name='Username')
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Фамилия')
    is_active = models.BooleanField(default=True, verbose_name='Активный')

    class Meta:
        verbose_name = 'пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_id})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Определяем, новый ли это объект
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"Создан новый пользователь: {self}")
        else:
            logger.info(f"Обновлен пользователь: {self}")

    def delete(self, *args, **kwargs):
        logger.warning(f"Удален пользователь: {self}")
        super().delete(*args, **kwargs)
