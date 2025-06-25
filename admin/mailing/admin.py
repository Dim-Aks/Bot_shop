from django.contrib import admin

from .models import Mailing


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('send_at', 'sent', 'text', 'media_file')  # Отображение полей в админке
    list_filter = ('sent', 'send_at')  # Фильтры по статусу отправки и дате, времени
    readonly_fields = ('sent',)

    def text_preview(self, obj):  # Отображение превью текста
        return obj.text[:50] + "..." if obj.text else ""

    text_preview.short_description = 'Текст сообщения'
