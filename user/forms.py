from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import re
from .models import CustomUser
from transport.models import Shipment


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(label = 'ФИО', max_length = 150)
    email = forms.EmailField(label = 'Email')
    phone = forms.CharField(label='Телефон', max_length=16)

    class Meta:
        model = CustomUser
        fields = ('username', 'full_name', 'phone', 'email', 'password1', 'password2',)
        labels = {
           'username': 'Логин'
        }

        def clean_username(self):
            username = self.cleaned_data.get('username')

            if not re.fullmatch(r'[A-Za-z0-9]+', username):
                raise ValidationError('Логин должен содержать только латинские буквы и цифры')

            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError('Пользователь с таким логином уже существует')

            return username

        def clean_full_name(self):
            full_name = self.cleaned_data.get('full_name')

            if not re.fullmatch(r'[А-Яа-яЁё\s]+', full_name):
                raise ValidationError('ФИО должно содержать только кириллицу и пробелы')

            return full_name

        def clean_phone(self):
            phone = self.cleaned_data.get('phone')

            if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', phone):
                raise ValidationError('Телефон должен быть в формате 8(XXX)XXX-XX-XX')

            if CustomUser.objects.filter(phone=phone).exists():
                raise ValidationError('Пользователь с таким телефоном уже существует')

            return phone


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class ShipmentCreateForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['from_city', 'from_address', 'to_city', 'to_address', 
                  'cargo_description', 'weight', 'volume', 'pickup_date']
        
    def clean_pickup_date(self):
        pickup_date = self.cleaned_data.get('pickup_date')
        today = now().date()

        if pickup_date < today:
            raise forms.ValidationError("Дата забора груза не может быть в прошлом.")
            
        if pickup_date.year < today.year:
            raise forms.ValidationError("Укажите корректный год.")
            
        return pickup_date

    def clean_volume(self):
        volume = self.cleaned_data.get('volume')
        max_truck_volume = 86.0  
        
        if volume is not None:
            if volume <= 0:
                raise forms.ValidationError("Объём груза должен быть больше нуля.")
            if volume > max_truck_volume:
                raise forms.ValidationError(
                    f"Груз слишком объёмный! Максимальная вместимость одного автомобиля — {max_truck_volume} м³."
                )
                
        return volume

    def clean_weight(self):
        # Раз уж мы защищаем машину от перегруза, давай ограничим и вес (в тоннах)
        weight = self.cleaned_data.get('weight')
        max_truck_weight = 22.0  # Стандартная грузоподъемность фуры — 20-22 тонны
        
        if weight is not None:
            if weight <= 0:
                raise forms.ValidationError("Вес груза должен быть больше нуля.")
            if weight > max_truck_weight:
                raise forms.ValidationError(
                    f"Груз слишком тяжелый! Максимальный вес для одной транспортировки — {max_truck_weight} тонн."
                )
        return weight
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pickup_date'].widget.attrs['min'] = now().date().isoformat()