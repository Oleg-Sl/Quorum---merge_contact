# Generated by Django 4.1 on 2022-09-04 04:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0002_email_value_type_im_value_type_phone_value_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contacts',
            name='EMAIL',
        ),
        migrations.RemoveField(
            model_name='contacts',
            name='IM',
        ),
        migrations.RemoveField(
            model_name='contacts',
            name='PHONE',
        ),
        migrations.RemoveField(
            model_name='contacts',
            name='WEB',
        ),
        migrations.AddField(
            model_name='email',
            name='contacts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='EMAIL', to='api_v1.contacts', verbose_name='Контакт'),
        ),
        migrations.AddField(
            model_name='im',
            name='contacts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='IM', to='api_v1.contacts', verbose_name='Контакт'),
        ),
        migrations.AddField(
            model_name='phone',
            name='contacts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='PHONE', to='api_v1.contacts', verbose_name='Контакт'),
        ),
        migrations.AddField(
            model_name='web',
            name='contacts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='WEB', to='api_v1.contacts', verbose_name='Контакт'),
        ),
    ]
