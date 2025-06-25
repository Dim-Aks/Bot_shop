from django.db import models


class Mailing(models.Model):
    text = models.TextField(blank=True, null=True, verbose_name='Текст сообщения')
    media_file = models.FileField(upload_to='mailing/', blank=True, null=True, verbose_name='Медиафайл')
    send_at = models.DateTimeField(verbose_name='Дата и время отправки')
    sent = models.BooleanField(default=False, verbose_name='Отправлено')

    class Meta:
        verbose_name = 'рассылку'
        verbose_name_plural = 'Рассылки'

    def __str__(self):
        return f"Рассылка на {self.send_at}"
