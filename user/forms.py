from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import re
from .models import CustomUser
from transport.models import CargoRequest, City


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(label='ФИО', max_length=150)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Телефон', max_length=16)

    class Meta:
        model = CustomUser
        fields = ('username', 'full_name', 'phone', 'email') # Пароли UserCreationForm добавит сам
        labels = {'username': 'Логин'}

    # ТЕПЕРЬ ОНИ СНАРУЖИ И БУДУТ РАБОТАТЬ:
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


class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-light border-0 py-2 rounded-3 shadow-none input-dash',
            'placeholder': '••••••••',
        }),
    )
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-light border-0 py-2 rounded-3 shadow-none input-dash',
            'placeholder': 'Минимум 8 знаков',
        }),
    )
    new_password2 = forms.CharField(
        label='Повторите новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-light border-0 py-2 rounded-3 shadow-none input-dash',
            'placeholder': 'Повторите пароль',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Неверный текущий пароль.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'Пароли не совпадают.')

        if password1:
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(password1, self.user)
            except ValidationError as exc:
                for message in exc.messages:
                    self.add_error('new_password1', message)

        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save(update_fields=['password'])
        return self.user


CITY_SELECT_ATTRS = {
    'class': 'form-select order-input py-2 shadow-none',
}


class CargoRequestCreateForm(forms.ModelForm):
    tariff = forms.ChoiceField(
        label="Тариф *",
        choices=[
            ('standard', 'Стандарт (Обычный)'),
            ('express', 'Экспресс (+50%)'),
            ('refrigerated', 'Рефрижератор (+80%)'),
        ],
        widget=forms.Select(attrs={
            'id': 'tariff',
            'class': 'form-select order-input py-2 shadow-none',
        }),
    )
    contact_name = forms.CharField(
        label="Контактное лицо *",
        max_length=150,
        widget=forms.TextInput(attrs={
            'id': 'contact_name',
            'placeholder': 'Иван Иванов',
            'class': 'form-control order-input py-2 shadow-none',
        }),
    )
    contact_phone = forms.CharField(
        label="Телефон *",
        max_length=20,
        widget=forms.TextInput(attrs={
            'id': 'contact_phone',
            'placeholder': '+7 (707) 123-45-67',
            'class': 'form-control order-input py-2 shadow-none',
        }),
    )

    class Meta:
        model = CargoRequest
        fields = [
            'from_city', 'to_city',
            'cargo_description', 'weight', 'volume', 'pickup_date',
            'contact_name', 'contact_phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cities = City.objects.filter(is_active=True).order_by('name')

        self.fields['from_city'].queryset = cities
        self.fields['from_city'].empty_label = 'Выберите город отправления...'
        self.fields['from_city'].widget.attrs.update({
            **CITY_SELECT_ATTRS,
            'id': 'from_city',
        })

        self.fields['to_city'].queryset = cities
        self.fields['to_city'].empty_label = 'Выберите город назначения...'
        self.fields['to_city'].widget.attrs.update({
            **CITY_SELECT_ATTRS,
            'id': 'to_city',
        })

        self.fields['cargo_description'].widget = forms.Textarea(attrs={
            'id': 'id_cargo_description',
            'class': 'form-control order-input py-2 shadow-none',
            'placeholder': 'Что именно перевозим?',
            'rows': 2,
        })
        self.fields['pickup_date'].widget.attrs.update({
            'id': 'pickup_date',
            'min': now().date().isoformat(),
            'class': 'form-control order-input py-2 shadow-none',
        })
        self.fields['weight'].widget.attrs.update({
            'id': 'weight',
            'class': 'form-control order-input py-2 shadow-none',
            'step': '0.01',
        })
        self.fields['volume'].required = True
        self.fields['volume'].widget.attrs.update({
            'id': 'volume',
            'class': 'form-control order-input py-2 shadow-none',
            'step': '0.01',
            'placeholder': '10',
        })
        if not self.is_bound:
            self.fields['weight'].initial = '1.0'
            self.fields['volume'].initial = '1.0'
            self.fields['tariff'].initial = 'standard'

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')

        if not phone:
            raise forms.ValidationError("Введите номер телефона")

        digits = re.sub(r'\D', '', phone)

        if len(digits) != 11:
            raise forms.ValidationError("Номер телефона должен содержать 11 цифр (например: +7XXXXXXXXXX)")

        if not digits.startswith(('7', '8')):
            raise forms.ValidationError("Номер должен начинаться с 7 или 8")

        return phone

    def clean_pickup_date(self):
        pickup_date = self.cleaned_data.get('pickup_date')
        today = now().date()
        if pickup_date < today:
            raise forms.ValidationError("Дата забора груза не может быть в прошлом.")
        return pickup_date

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight <= 0:
                raise forms.ValidationError("Вес должен быть больше нуля.")
            if weight > 22.0:
                raise forms.ValidationError("Максимальный вес — 22 тонны.")
        return weight

    def clean_volume(self):
        volume = self.cleaned_data.get('volume')
        if volume is not None:
            if volume <= 0:
                raise forms.ValidationError("Объём должен быть больше нуля.")
            if volume > 86.0:
                raise forms.ValidationError("Максимальный объём — 86 м³.")
        return volume

