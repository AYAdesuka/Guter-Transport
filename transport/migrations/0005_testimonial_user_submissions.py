import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transport', '0004_driver_vehicle_and_request_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='testimonial',
            name='shipment',
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='testimonial', to='transport.shipment', verbose_name='Отправка',
            ),
        ),
        migrations.AddField(
            model_name='testimonial',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='testimonials', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь',
            ),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='client_name',
            field=models.CharField(max_length=200, verbose_name='Клиент'),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='is_published',
            field=models.BooleanField(default=False, verbose_name='Опубликован на сайте'),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='rating',
            field=models.PositiveSmallIntegerField(default=5, verbose_name='Оценка'),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='text',
            field=models.TextField(verbose_name='Текст отзыва'),
        ),
    ]
