# Generated by Django 5.1.2 on 2024-10-30 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('house_bills', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='housemonthlybill',
            name='signature',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='houseotherbill',
            name='signature',
            field=models.TextField(default=''),
        ),
    ]
