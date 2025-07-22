from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user_id', 'username', 'first_name', 'last_name')
