from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
import logging
from django.core.mail import send_mail
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

logger = logging.getLogger(__name__)

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


class EmailVerificationCode(models.Model):
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Код подтверждения email'
        verbose_name_plural = 'Коды подтверждения email'
        ordering = ['-created_at']

    @classmethod
    def create_for_email(cls, email: str, lifetime_minutes: int = 15):
        cls.objects.filter(email__iexact=email, is_used=False).update(is_used=True)
        code = f'{random.randint(100000, 999999)}'
        return cls.objects.create(
            email=email.lower(),
            code=code,
            expires_at=timezone.now() + timedelta(minutes=lifetime_minutes),
        )

    def is_valid(self, code: str) -> bool:
        return (
            not self.is_used
            and self.expires_at >= timezone.now()
            and self.code == code.strip()
        )

    @classmethod
    def verify(cls, email: str, code: str):
        record = (
            cls.objects.filter(email__iexact=email, is_used=False, code=code.strip())
            .order_by('-created_at')
            .first()
        )
        if not record or not record.is_valid(code):
            return None
        record.is_used = True
        record.save(update_fields=['is_used'])
        return record
    
@receiver(post_save, sender=EmailVerificationCode)
def send_verification_code_on_create(sender, instance, created, **kwargs):
    if created and not instance.is_used:
        subject = f'Доступ к личному кабинету Guter Transport (ID {instance.id})'
        message = (
            f'Уважаемый пользователь!\n\n'
            f'Вы получили это автоматическое уведомление, так как этот адрес электронной почты '
            f'был указан при создании профиля на платформе коммерческих перевозок Guter Transport.\n\n'
            f'Для подтверждения владения данным почтовым ящиком и завершения процедуры авторизации, '
            f'пожалуйста, введите в соответствующее поле на странице сайта следующий одноразовый цифровой ключ:\n\n'
            f'КЛЮЧ ДОСТУПА: {instance.code}\n\n'
            f'Данный ключ сформирован автоматически, действует ограниченное время (15 минут) '
            f'и не требует ответа на данное письмо. Если вы не совершали никаких действий на нашем сайте, '
            f'просто проигнорируйте это сообщение.\n\n'
            f'С уважением,\n'
            f'Служба технической поддержки Guter Transport.\n'
            f'Официальный сайт логистической платформы: http://localhost:8000'
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=False,
            )
            logger.info(f"Код верификации успешно отправлен на {instance.email}")
            
        except Exception as e:

            print(f"\n!!! ОШИБКА ОТПРАВКИ КОДА В СИГНАЛЕ !!!: {e}")
            print(f"Но сам код для теста: {instance.code}\n")
            logger.exception(f"Failed to send verification email to {instance.email}")