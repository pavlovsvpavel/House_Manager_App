# Generated by Django 5.1.2 on 2024-11-06 08:58

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('house_bills', '0002_housemonthlybill_signature_houseotherbill_signature'),
    ]

    operations = [
        migrations.RenameField(
            model_name='housemonthlybill',
            old_name='fee_manager_and_cashier',
            new_name='fee_manager',
        ),
    ]
