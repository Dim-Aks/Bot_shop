from django.contrib import admin

from .models import Category, SubCategory, Product

admin.site.site_header = "Администрирование бота"  # Заголовок сайта
admin.site.site_title = "Администрирование"  # Заголовок в панели управления
admin.site.index_title = "Панель управления"  # Заголовок на главной странице


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Отображение полей в админке
    search_fields = ('name',)  # Поле для поиска


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)  # Фильтрация по категории
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'price')
    list_filter = ('category', 'subcategory')
    search_fields = ('name', 'description')
