from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 'registration_date', 'is_active')
    list_filter = ('is_active', 'registration_date')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')
    date_hierarchy = 'registration_date'  # Навигация по датам
