from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('house_bills', '0008_remove_housemonthlybill_total_amount_temp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='housemonthlybill',
            name='year',
            field=models.CharField(choices=[('2024', '2024'), ('2025', '2025'), ('2026', '2026')], max_length=4, verbose_name='Year'),
        ),
        migrations.AlterField(
            model_name='houseotherbill',
            name='year',
            field=models.CharField(choices=[('2024', '2024'), ('2025', '2025'), ('2026', '2026')], max_length=4, verbose_name='Year'),
        ),
    ]
