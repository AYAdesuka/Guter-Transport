from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    ACCOUNT_TYPE_CHOICES = [
        ('client', 'Частное лицо'),
        ('b2b', 'Компания (B2B)'),
    ]
    account_type = models.CharField(
        max_length=10, 
        choices=ACCOUNT_TYPE_CHOICES, 
        default='client',
        verbose_name='Тип аккаунта'
    )
    company_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Название компании'
    )

    def __str__(self):

        if self.account_type == 'b2b' and self.company_name:
            return f'{self.last_name} {self.first_name} ({self.company_name})'
        return f'{self.last_name} {self.first_name}'

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'