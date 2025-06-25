from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    description = models.TextField(blank=True, null=True, verbose_name='Описание категории')

    class Meta:
        verbose_name = 'категорию'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 related_name='subcategories',
                                 verbose_name='Категория')
    name = models.CharField(max_length=100, verbose_name='Название подкатегории')
    description = models.TextField(blank=True, null=True, verbose_name='Описание подкатегории')

    class Meta:
        verbose_name = 'подкатегорию'
        verbose_name_plural = 'Подкатегории'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    subcategory = models.ForeignKey(SubCategory,
                                    on_delete=models.CASCADE,
                                    related_name='products',
                                    verbose_name='Подкатегория',
                                    blank=True,
                                    null=True)
    name = models.CharField(max_length=255, verbose_name='Название товара')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    photo = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name
