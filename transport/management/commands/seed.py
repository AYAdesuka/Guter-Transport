from django.core.management.base import BaseCommand
from transport.models import City

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



class Command(BaseCommand):
    help = "Заполнить базу городами"

    def handle(self, *args, **kwargs):
        created = 0

        for name in CITIES:
            _, was_created = City.objects.get_or_create(
                name=name,
                defaults={"is_active": True},
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Добавлено {created} городов")
        )