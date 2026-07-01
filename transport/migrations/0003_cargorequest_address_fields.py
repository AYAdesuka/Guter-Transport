from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transport', '0002_city_alter_shipment_cargo_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargorequest',
            name='from_address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Адрес отправления'),
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='to_address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Адрес доставки'),
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='tariff',
            field=models.CharField(
                choices=[
                    ('standard', 'Стандарт'),
                    ('express', 'Экспресс'),
                    ('refrigerated', 'Рефрижератор'),
                ],
                default='standard',
                max_length=20,
                verbose_name='Тариф',
            ),
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='estimated_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='Расчётная стоимость',
            ),
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='distance_km',
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=8,
                null=True,
                verbose_name='Расстояние (км)',
            ),
        ),
    ]
