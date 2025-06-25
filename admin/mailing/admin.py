import logging
import os

from aiogram import Bot
from asgiref.sync import async_to_sync
from django.contrib import admin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.urls import path
from django.urls import reverse
from django.utils.html import format_html
from dotenv import load_dotenv

from users.models import User
from .models import Mailing

logger = logging.getLogger('mailing')  # Получаем логгер для приложения mailing
load_dotenv()


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('send_at', 'sent', 'text', 'media_file', 'send_button')  # Отображение полей в админке
    list_filter = ('sent', 'send_at')  # Фильтры по статусу отправки и дате, времени
    readonly_fields = ('sent',)

    # Отображение превью текста
    def text_preview(self, obj):
        return obj.text[:50] + "..." if obj.text else ""

    text_preview.short_description = 'Текст сообщения'

    # HTML-кнопка в админке
    def send_button(self, obj):
        if not obj.sent:
            return format_html(
                '<button class="button" onclick="location.href=\'{}\'">Отправить</button>',
                f'/admin/mailing/mailing/{obj.pk}/send/'
            )
        else:
            return format_html("Отправлено")

    send_button.short_description = 'Отправить'
    send_button.allow_tags = True

    # кастомная ссылка для кнопки в каждой рассылке
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/send/', self.admin_site.admin_view(self.send_mailing), name='mailing_send'),
        ]
        return custom_urls + urls

    # Логика отправки сообщения
    def send_mailing(self, request, object_id):
        mailing = self.get_object(request, object_id)
        if not mailing.sent:
            try:
                self.send_message_to_all_users(mailing)
                mailing.sent = True
                mailing.save()
                self.message_user(request, "Рассылка успешно отправлена.", level=messages.SUCCESS)
                logger.info(f"Рассылка {mailing.pk} успешно отправлена.")
            except Exception as e:
                self.message_user(request, f"Ошибка при отправке рассылки: {e}", level=messages.ERROR)
                logger.error(f"Ошибка при отправке рассылки {mailing.pk}: {e}", exc_info=True)
        else:
            self.message_user(request, "Рассылка уже была отправлена.", level=messages.WARNING)
            logger.warning(f"Попытка повторной отправки рассылки {mailing.pk}.")

        return redirect(reverse('admin:mailing_mailing_changelist'))

    # Отправка сообщения каждому активному пользователю
    def send_message_to_all_users(self, mailing):
        bot = Bot(token=os.getenv("BOT_TOKEN"))
        users = User.objects.filter(is_active=True)
        for user in users:
            try:
                if mailing.media_file:
                    try:
                        with default_storage.open(mailing.media_file.name, 'rb') as file:
                            async_to_sync(bot.send_photo)(user.telegram_id, file.read(),
                                                          caption=mailing.text if mailing.text else None)
                            logger.info(f"Отправлено фото пользователю {user.telegram_id} для рассылки {mailing.pk}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке фото пользователю {user.telegram_id}: {e}", exc_info=True)
                elif mailing.text:
                    async_to_sync(bot.send_message)(user.telegram_id, mailing.text)
                    logger.info(f"Отправлено сообщение пользователю {user.telegram_id} для рассылки {mailing.pk}")
                else:
                    logger.warning(
                        f"Нет текста или медиафайла для отправки пользователю {user.telegram_id} для рассылки {mailing.pk}")
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}", exc_info=True)
