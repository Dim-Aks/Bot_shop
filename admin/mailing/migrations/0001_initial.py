# Generated by Django 5.2.3 on 2025-06-25 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Mailing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, null=True, verbose_name='Текст сообщения')),
                ('media_file', models.FileField(blank=True, null=True, upload_to='mailing/', verbose_name='Медиафайл')),
                ('send_at', models.DateTimeField(verbose_name='Дата и время отправки')),
                ('sent', models.BooleanField(default=False, verbose_name='Отправлено')),
            ],
            options={
                'verbose_name': 'Рассылка',
                'verbose_name_plural': 'Рассылки',
            },
        ),
    ]
