import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название компании')),
                ('logo', models.ImageField(upload_to='clients/logos/', verbose_name='Логотип')),
                ('website', models.URLField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': 'Клиенты',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название услуги')),
                ('slug', models.SlugField(unique=True)),
                ('short_description', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('price_from', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Цена от')),
                ('unit', models.CharField(blank=True, max_length=50, verbose_name='Единица')),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Услуга',
                'verbose_name_plural': 'Услуги',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ServiceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Категория')),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.ImageField(blank=True, upload_to='services/icons/')),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Категория услуг',
                'verbose_name_plural': 'Категории услуг',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Guter Transport', max_length=200, verbose_name='Название компании')),
                ('slogan', models.CharField(blank=True, max_length=300, verbose_name='Слоган')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('email', models.EmailField(max_length=254)),
                ('address', models.TextField(blank=True, verbose_name='Адрес')),
                ('working_hours', models.CharField(blank=True, max_length=100, verbose_name='Режим работы')),
                ('whatsapp', models.CharField(blank=True, max_length=20)),
                ('telegram', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Настройки сайта',
                'verbose_name_plural': 'Настройки сайта',
            },
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_name', models.CharField(max_length=200, verbose_name='Клиент')),
                ('text', models.TextField()),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('photo', models.ImageField(blank=True, upload_to='testimonials/')),
                ('is_published', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CargoRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_city', models.CharField(max_length=150, verbose_name='Откуда')),
                ('to_city', models.CharField(max_length=150, verbose_name='Куда')),
                ('weight', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Вес (тонн)')),
                ('volume', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Объём (м³)')),
                ('pickup_date', models.DateField(verbose_name='Дата забора')),
                ('cargo_description', models.TextField(blank=True)),
                ('contact_name', models.CharField(max_length=150, verbose_name='Контактное лицо')),
                ('contact_phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('processed', 'В обработке'), ('confirmed', 'Подтверждена'), ('canceled', 'Отменена')], default='new', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cargo_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PortfolioProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название проекта')),
                ('slug', models.SlugField(unique=True)),
                ('from_city', models.CharField(max_length=100, verbose_name='Откуда')),
                ('to_city', models.CharField(max_length=100, verbose_name='Куда')),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Вес (тонн)')),
                ('date', models.DateField(verbose_name='Дата выполнения')),
                ('description', models.TextField()),
                ('main_image', models.ImageField(upload_to='portfolio/')),
                ('is_featured', models.BooleanField(default=False, verbose_name='На главной')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transport.client')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transport.service')),
            ],
            options={
                'verbose_name': 'Проект',
                'verbose_name_plural': 'Портфолио',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ProjectImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='portfolio/gallery/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='transport.portfolioproject')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='service',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='services', to='transport.servicecategory'),
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracking_number', models.CharField(blank=True, max_length=50, unique=True, verbose_name='Трекинг-номер')),
                ('from_city', models.CharField(max_length=150, verbose_name='Откуда')),
                ('from_address', models.TextField(blank=True)),
                ('to_city', models.CharField(max_length=150, verbose_name='Куда')),
                ('to_address', models.TextField(blank=True)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Вес (тонн)')),
                ('volume', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Объём (м³)')),
                ('cargo_description', models.TextField(blank=True)),
                ('pickup_date', models.DateField(verbose_name='Дата забора')),
                ('delivery_date_expected', models.DateField(blank=True, null=True, verbose_name='Плановая доставка')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Стоимость')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('confirmed', 'Подтверждена'), ('in_progress', 'В пути'), ('delivered', 'Доставлена'), ('canceled', 'Отменена'), ('problem', 'Проблема')], default='new', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Отправка',
                'verbose_name_plural': 'Отправки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ShipmentStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('confirmed', 'Подтверждена'), ('in_progress', 'В пути'), ('delivered', 'Доставлена'), ('canceled', 'Отменена'), ('problem', 'Проблема')], max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='transport.shipment')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
