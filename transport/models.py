from django.db import models
import random
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.timezone import now

User = get_user_model()

RESOURCE_BUSY_SHIPMENT_STATUSES = ('new', 'confirmed', 'in_progress', 'problem')


class SiteSettings(models.Model):
    title = models.CharField("Название компании", max_length=200, default="Guter Transport")
    slogan = models.CharField("Слоган", max_length=300, blank=True)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField()
    address = models.TextField("Адрес", blank=True)
    working_hours = models.CharField("Режим работы", max_length=100, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return self.title


class City(models.Model):
    name = models.CharField("Название города", max_length=100, unique=True)
    is_active = models.BooleanField("Доступен для доставки", default=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    name = models.CharField("Категория", max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='services/icons/', blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"
        ordering = ['order']

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, related_name='services')
    title = models.CharField("Название услуги", max_length=200)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    price_from = models.DecimalField("Цена от", max_digits=12, decimal_places=2, null=True, blank=True)
    unit = models.CharField("Единица", max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['order']

    def __str__(self):
        return self.title

class Client(models.Model):
    name = models.CharField("Название компании", max_length=200)
    logo = models.ImageField("Логотип", upload_to='clients/logos/')
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['order']

    def __str__(self):
        return self.name


class PortfolioProject(models.Model):
    title = models.CharField("Название проекта", max_length=200)
    slug = models.SlugField(unique=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    
    from_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='portfolio_departures', verbose_name="Откуда")
    to_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='portfolio_arrivals', verbose_name="Куда")
    
    weight = models.DecimalField("Вес (тонн)", max_digits=8, decimal_places=2, null=True, blank=True)
    date = models.DateField("Дата выполнения")
    description = models.TextField()
    main_image = models.ImageField(upload_to='portfolio/')
    is_featured = models.BooleanField("На главной", default=False)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Портфолио"
        ordering = ['-date']

    def __str__(self):
        return self.title


class ProjectImage(models.Model):
    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class Testimonial(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='testimonials',
        null=True, blank=True, verbose_name='Пользователь',
    )
    shipment = models.OneToOneField(
        'Shipment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='testimonial', verbose_name='Отправка',
    )
    client_name = models.CharField("Клиент", max_length=200)
    text = models.TextField("Текст отзыва")
    rating = models.PositiveSmallIntegerField("Оценка", default=5)
    photo = models.ImageField(upload_to='testimonials/', blank=True)
    is_published = models.BooleanField("Опубликован на сайте", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client_name} — {self.rating}/5"


class Driver(models.Model):
    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    phone = models.CharField("Телефон", max_length=20)
    license_number = models.CharField("Номер ВУ", max_length=30, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='driver_profile', verbose_name="Пользователь",
    )

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    @property
    def active_shipment(self):
        return (
            self.shipments
            .filter(status__in=RESOURCE_BUSY_SHIPMENT_STATUSES)
            .select_related('from_city', 'to_city', 'vehicle')
            .order_by('-updated_at')
            .first()
        )

    @property
    def is_busy(self):
        return self.active_shipment is not None


class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('truck', 'Грузовик'),
        ('van', 'Фургон'),
        ('refrigerator', 'Рефрижератор'),
        ('trailer', 'Прицеп'),
    ]

    license_plate = models.CharField("Госномер", max_length=15, unique=True)
    brand = models.CharField("Марка", max_length=100)
    model_name = models.CharField("Модель", max_length=100)
    vehicle_type = models.CharField("Тип", max_length=20, choices=VEHICLE_TYPE_CHOICES, default='truck')
    capacity_tons = models.DecimalField("Грузоподъёмность (т)", max_digits=8, decimal_places=2)
    volume_m3 = models.DecimalField("Объём кузова (м³)", max_digits=8, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Транспортное средство"
        verbose_name_plural = "Транспортные средства"
        ordering = ['license_plate']

    def __str__(self):
        return f"{self.license_plate} — {self.brand} {self.model_name}"

    @property
    def active_shipment(self):
        return (
            self.shipments
            .filter(status__in=RESOURCE_BUSY_SHIPMENT_STATUSES)
            .select_related('from_city', 'to_city', 'driver')
            .order_by('-updated_at')
            .first()
        )

    @property
    def is_busy(self):
        return self.active_shipment is not None


class CargoRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_review', 'На рассмотрении'),
        ('processed', 'В обработке'),
        ('confirmed', 'Подтверждена'),
        ('canceled', 'Отменена'),
    ]

    TARIFF_CHOICES = [
        ('standard', 'Стандарт'),
        ('express', 'Экспресс'),
        ('refrigerated', 'Рефрижератор'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cargo_requests', null=True, blank=True)
    
    from_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='request_departures', verbose_name="Город отправления")
    from_address = models.CharField("Адрес отправления", max_length=255, blank=True)
    to_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='request_arrivals', verbose_name="Город назначения")
    to_address = models.CharField("Адрес доставки", max_length=255, blank=True)
    
    tariff = models.CharField("Тариф", max_length=20, choices=TARIFF_CHOICES, default='standard')
    estimated_price = models.DecimalField("Расчётная стоимость", max_digits=12, decimal_places=2, null=True, blank=True)
    distance_km = models.DecimalField("Расстояние (км)", max_digits=8, decimal_places=1, null=True, blank=True)

    weight = models.DecimalField("Вес (тонн)", max_digits=8, decimal_places=2)
    volume = models.DecimalField("Объём (м³)", max_digits=8, decimal_places=2, null=True, blank=True)
    pickup_date = models.DateField("Дата забора")
    cargo_description = models.TextField(blank=True)
    contact_name = models.CharField("Контактное лицо", max_length=150)
    contact_phone = models.CharField("Телефон", max_length=20)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_cargo_requests', verbose_name="Проверил",
    )
    reviewed_at = models.DateTimeField("Дата проверки", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id} — {self.from_city} → {self.to_city}"

    @property
    def is_pending(self):
        return self.status in ('pending_review', 'processed')

    @property
    def shipment(self):
        return getattr(self, 'linked_shipment', None)

    def confirm(self, driver, vehicle, reviewed_by):
        if self.status == 'confirmed':
            raise ValidationError('Заявка уже подтверждена.')
        if self.status == 'canceled':
            raise ValidationError('Нельзя подтвердить отменённую заявку.')
        if not self.user_id:
            raise ValidationError('У заявки нет привязанного пользователя.')
        if hasattr(self, 'linked_shipment'):
            raise ValidationError('Для этой заявки уже создана отправка.')
        if not driver.is_active:
            raise ValidationError('Выбранный водитель неактивен.')
        if not vehicle.is_active:
            raise ValidationError('Выбранное транспортное средство неактивно.')

        _validate_resource_availability(driver, vehicle)

        shipment = Shipment.objects.create(
            user=self.user,
            cargo_request=self,
            from_city=self.from_city,
            from_address=self.from_address,
            to_city=self.to_city,
            to_address=self.to_address,
            weight=self.weight,
            volume=self.volume,
            cargo_description=self.cargo_description,
            pickup_date=self.pickup_date,
            price=self.estimated_price,
            driver=driver,
            vehicle=vehicle,
            status='confirmed',
        )
        ShipmentStatusHistory.objects.create(
            shipment=shipment,
            status='confirmed',
            comment=f'Создано из заявки #{self.id}',
            updated_by=reviewed_by,
        )
        self.status = 'confirmed'
        self.reviewed_by = reviewed_by
        self.reviewed_at = now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return shipment


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('confirmed', 'Подтверждена'),
        ('in_progress', 'В пути'),
        ('delivered', 'Доставлена'),
        ('canceled', 'Отменена'),
        ('problem', 'Проблема'),
    ]

    RESOURCE_BUSY_STATUSES = RESOURCE_BUSY_SHIPMENT_STATUSES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipments')
    cargo_request = models.OneToOneField(
        CargoRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='linked_shipment', verbose_name="Заявка",
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='shipments', verbose_name="Водитель",
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='shipments', verbose_name="Транспорт",
    )
    tracking_number = models.CharField("Трекинг-номер", max_length=50, unique=True, blank=True)

    from_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='shipment_departures', verbose_name="Город отправления")
    from_address = models.TextField("Адрес забора", blank=True)
    
    to_city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='shipment_arrivals', verbose_name="Город назначения")
    to_address = models.TextField("Адрес доставки", blank=True)

    weight = models.DecimalField("Вес (тонн)", max_digits=8, decimal_places=2)
    volume = models.DecimalField("Объём (м³)", max_digits=8, decimal_places=2, null=True, blank=True)
    cargo_description = models.TextField("Описание груза", blank=True)

    pickup_date = models.DateField("Дата забора")
    delivery_date_expected = models.DateField("Плановая доставка", null=True, blank=True)

    price = models.DecimalField("Стоимость", max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отправка"
        verbose_name_plural = "Отправки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} — {self.from_city} → {self.to_city}"

    @classmethod
    def resource_busy_queryset(cls):
        return cls.objects.filter(status__in=cls.RESOURCE_BUSY_STATUSES)

    @classmethod
    def get_busy_drivers_map(cls):
        shipments = (
            cls.resource_busy_queryset()
            .filter(driver_id__isnull=False)
            .select_related('driver', 'vehicle', 'from_city', 'to_city')
        )
        return {shipment.driver_id: shipment for shipment in shipments}

    @classmethod
    def get_busy_vehicles_map(cls):
        shipments = (
            cls.resource_busy_queryset()
            .filter(vehicle_id__isnull=False)
            .select_related('driver', 'vehicle', 'from_city', 'to_city')
        )
        return {shipment.vehicle_id: shipment for shipment in shipments}

    def calculate_and_get_price(self, distance_km=None):
        dist = float(distance_km) if distance_km else 100.0
        base_rate_per_km = 6.0
        cost_by_distance = base_rate_per_km * dist
        extra_charges = 0.0

        weight_tons = float(self.weight) if self.weight else 0.0
        volume_m3 = float(self.volume) if self.volume else 0.0
        if weight_tons > 0 and volume_m3 > 0:
            weight_kg = weight_tons * 1000
            density = weight_kg / volume_m3

            if density < 250:
                extra_charges = volume_m3 * 300.0
            else:
                extra_charges = weight_tons * 500.0
        elif weight_tons > 0:
            extra_charges = weight_tons * 500.0
        elif volume_m3 > 0:
            extra_charges = volume_m3 * 300.0

        calculated_flat = cost_by_distance + extra_charges
        
        if calculated_flat < 2000.00:
            return 2000.00
        
        return round(calculated_flat, 2)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            year = now().year
            while True:
                random_digits = random.randint(1000, 9999)
                generated_track = f"GT-{year}-{random_digits}"
                if not Shipment.objects.filter(tracking_number=generated_track).exists():
                    self.tracking_number = generated_track
                    break
        if self.price is None:
            self.price = self.calculate_and_get_price()
                    
        super().save(*args, **kwargs)


def _validate_resource_availability(driver, vehicle, exclude_shipment_id=None):
    busy_qs = Shipment.resource_busy_queryset().select_for_update()
    if exclude_shipment_id:
        busy_qs = busy_qs.exclude(pk=exclude_shipment_id)

    driver_shipment = busy_qs.filter(driver=driver).first()
    if driver_shipment:
        raise ValidationError(
            f'Водитель {driver.full_name} уже выполняет отправку '
            f'{driver_shipment.tracking_number} ({driver_shipment.get_status_display()}).'
        )

    vehicle_shipment = busy_qs.filter(vehicle=vehicle).first()
    if vehicle_shipment:
        raise ValidationError(
            f'Транспорт {vehicle.license_plate} уже назначен на отправку '
            f'{vehicle_shipment.tracking_number} ({vehicle_shipment.get_status_display()}).'
        )


class ShipmentStatusHistory(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)