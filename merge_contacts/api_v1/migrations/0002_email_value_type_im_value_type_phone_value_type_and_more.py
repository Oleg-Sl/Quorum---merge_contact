# Generated by Django 4.1 on 2022-09-03 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='VALUE_TYPE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Тип электронной почты'),
        ),
        migrations.AddField(
            model_name='im',
            name='VALUE_TYPE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Тип мессенджера'),
        ),
        migrations.AddField(
            model_name='phone',
            name='VALUE_TYPE',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Тип телефона'),
        ),
        migrations.AddField(
            model_name='web',
            name='VALUE_TYPE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Тип ресурса'),
        ),
        migrations.AlterField(
            model_name='email',
            name='VALUE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Адрес электронной почты'),
        ),
        migrations.AlterField(
            model_name='im',
            name='VALUE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Мессенджеры'),
        ),
        migrations.AlterField(
            model_name='phone',
            name='VALUE',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Телефон контакта'),
        ),
        migrations.AlterField(
            model_name='web',
            name='VALUE',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='URL ресурсов контакта'),
        ),
    ]