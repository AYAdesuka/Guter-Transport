import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_new_to_pending_review(apps, schema_editor):
    CargoRequest = apps.get_model('transport', 'CargoRequest')
    CargoRequest.objects.filter(status='new').update(status='pending_review')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transport', '0003_cargorequest_address_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                ('middle_name', models.CharField(blank=True, max_length=100, verbose_name='Отчество')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('license_number', models.CharField(blank=True, max_length=30, verbose_name='Номер ВУ')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('user', models.OneToOneField(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='driver_profile', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь',
                )),
            ],
            options={
                'verbose_name': 'Водитель',
                'verbose_name_plural': 'Водители',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_plate', models.CharField(max_length=15, unique=True, verbose_name='Госномер')),
                ('brand', models.CharField(max_length=100, verbose_name='Марка')),
                ('model_name', models.CharField(max_length=100, verbose_name='Модель')),
                ('vehicle_type', models.CharField(
                    choices=[
                        ('truck', 'Грузовик'),
                        ('van', 'Фургон'),
                        ('refrigerator', 'Рефрижератор'),
                        ('trailer', 'Прицеп'),
                    ],
                    default='truck', max_length=20, verbose_name='Тип',
                )),
                ('capacity_tons', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Грузоподъёмность (т)')),
                ('volume_m3', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Объём кузова (м³)',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Транспортное средство',
                'verbose_name_plural': 'Транспортные средства',
                'ordering': ['license_plate'],
            },
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата проверки'),
        ),
        migrations.AddField(
            model_name='cargorequest',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_cargo_requests', to=settings.AUTH_USER_MODEL, verbose_name='Проверил',
            ),
        ),
        migrations.RunPython(migrate_new_to_pending_review, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='cargorequest',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending_review', 'На рассмотрении'),
                    ('processed', 'В обработке'),
                    ('confirmed', 'Подтверждена'),
                    ('canceled', 'Отменена'),
                ],
                default='pending_review',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='shipment',
            name='cargo_request',
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='linked_shipment', to='transport.cargorequest', verbose_name='Заявка',
            ),
        ),
        migrations.AddField(
            model_name='shipment',
            name='driver',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='shipments', to='transport.driver', verbose_name='Водитель',
            ),
        ),
        migrations.AddField(
            model_name='shipment',
            name='vehicle',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='shipments', to='transport.vehicle', verbose_name='Транспорт',
            ),
        ),
    ]
