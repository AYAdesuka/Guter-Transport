from django.core.management.base import BaseCommand
from transport.models import City, Driver, Vehicle, Testimonial

CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Пермь",
    "Воронеж",
    "Волгоград",
    "Краснодар",
    "Майкоп",
    "Белореченск",
    "Сочи",
    "Саратов",
    "Тюмень",
    "Тольятти",
    "Ижевск",
    "Барнаул",
    "Ульяновск",
    "Иркутск",
    "Хабаровск",
    "Ярославль",
    "Владивосток",
    "Махачкала",
    "Томск",
    "Оренбург",
    "Кемерово",
]

DRIVERS = [
    {"last_name": "Иванов", "first_name": "Сергей", "middle_name": "Петрович", "phone": "+7 (900) 111-22-33", "license_number": "77 AA 123456"},
    {"last_name": "Петров", "first_name": "Алексей", "middle_name": "", "phone": "+7 (900) 222-33-44", "license_number": "77 BB 654321"},
    {"last_name": "Сидоров", "first_name": "Дмитрий", "middle_name": "Иванович", "phone": "+7 (900) 333-44-55", "license_number": "77 CC 789012"},
]

VEHICLES = [
    {"license_plate": "А123ВС777", "brand": "КАМАЗ", "model_name": "65115", "vehicle_type": "truck", "capacity_tons": "20.00", "volume_m3": "45.00"},
    {"license_plate": "В456КМ777", "brand": "Mercedes-Benz", "model_name": "Actros", "vehicle_type": "truck", "capacity_tons": "15.00", "volume_m3": "35.00"},
    {"license_plate": "С789НР777", "brand": "GAZelle", "model_name": "Next", "vehicle_type": "van", "capacity_tons": "1.50", "volume_m3": "12.00"},
    {"license_plate": "Е012ТУ777", "brand": "Hyundai", "model_name": "HD78", "vehicle_type": "refrigerator", "capacity_tons": "3.50", "volume_m3": "18.00"},
]

TESTIMONIALS = [
    {
        "client_name": "ООО «ТехноМаркет»",
        "text": "Перевозим сборные партии на маркетплейсы каждую неделю. Guter Transport всегда держит сроки, а трекинг в личном кабинете экономит кучу звонков менеджерам.",
        "rating": 5,
    },
    {
        "client_name": "Анна Кузнецова",
        "text": "Оформила заявку онлайн, менеджер быстро подтвердил и назначил машину. Груз из Москвы в Казань доехал без задержек, цена совпала с расчётом на сайте.",
        "rating": 5,
    },
    {
        "client_name": "ИП Смирнов",
        "text": "Работаем с рефрижераторными перевозками — важна температура и аккуратность. Команда Guter Transport справляется стабильно, уже третий месяц без срывов.",
        "rating": 4,
    },
    {
        "client_name": "Сеть «Продукты 24»",
        "text": "Подключили B2B-аккаунт для регулярных поставок. Удобно видеть все отправки в одном месте и быстро оформлять новые заявки.",
        "rating": 5,
    },
    {
        "client_name": "Дмитрий Волков",
        "text": "Первый раз заказывал перевозку мебели между городами — всё прозрачно: заявка, подтверждение, водитель, доставка. Рекомендую.",
        "rating": 5,
    },
    {
        "client_name": "ООО «СтройКомплект»",
        "text": "Тяжёлые грузы и нестандартные маршруты — для нас это норма. Guter Transport подбирает технику под вес и объём, это реально помогает.",
        "rating": 4,
    },
]



class Command(BaseCommand):
    help = "Заполнить базу городами, водителями, транспортом и отзывами"

    def handle(self, *args, **kwargs):
        cities_created = 0
        drivers_created = 0
        vehicles_created = 0
        testimonials_created = 0

        for name in CITIES:
            _, was_created = City.objects.get_or_create(
                name=name,
                defaults={"is_active": True},
            )
            if was_created:
                cities_created += 1

        for data in DRIVERS:
            _, was_created = Driver.objects.get_or_create(
                license_number=data["license_number"],
                defaults=data,
            )
            if was_created:
                drivers_created += 1

        for data in VEHICLES:
            _, was_created = Vehicle.objects.get_or_create(
                license_plate=data["license_plate"],
                defaults=data,
            )
            if was_created:
                vehicles_created += 1

        for data in TESTIMONIALS:
            _, was_created = Testimonial.objects.get_or_create(
                client_name=data["client_name"],
                defaults={
                    "text": data["text"],
                    "rating": data["rating"],
                    "is_published": True,
                },
            )
            if was_created:
                testimonials_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Добавлено: {cities_created} городов, "
                f"{drivers_created} водителей, {vehicles_created} ТС, "
                f"{testimonials_created} отзывов"
            )
        )