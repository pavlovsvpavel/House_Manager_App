# Generated by Django 5.1.2 on 2024-11-06 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_bills', '0004_clientmonthlybill_fee_cashier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientmonthlybill',
            name='total_amount_temp',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]