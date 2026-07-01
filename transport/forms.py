from django import forms
from .models import Shipment

from django import forms
from .models import CargoRequest, Shipment, City

CONTROL_CLASSES = 'form-control bg-light border-0 rounded-3 py-2'
SELECT_CLASSES = 'form-select bg-light border-0 rounded-3 py-2'


class CargoRequestForm(forms.ModelForm):
    
    from_city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True),
        empty_label="Выберите город отправления...",
        widget=forms.Select(attrs={'class': SELECT_CLASSES})
    )
    to_city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True),
        empty_label="Выберите город назначения...",
        widget=forms.Select(attrs={'class': SELECT_CLASSES})
    )

    class Meta:
        model = CargoRequest
        fields = [
            'from_city', 'to_city', 'weight', 'volume', 
            'pickup_date', 'cargo_description', 'contact_name', 'contact_phone'
        ]
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date', 'class': CONTROL_CLASSES}),
            'weight': forms.NumberInput(attrs={'placeholder': 'Вес в тоннах (например: 2.5)', 'step': '0.01', 'class': CONTROL_CLASSES}),
            'volume': forms.NumberInput(attrs={'placeholder': 'Объем в м³ (необязательно)', 'step': '0.01', 'class': CONTROL_CLASSES}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'Как к вам обращаться?', 'class': CONTROL_CLASSES}),
            'contact_phone': forms.TextInput(attrs={'placeholder': '+7 (999) 000-00-00', 'class': CONTROL_CLASSES}),
            'cargo_description': forms.Textarea(attrs={'placeholder': 'Краткое описание груза...', 'rows': 3, 'class': CONTROL_CLASSES}),
        }


class ShipmentForm(forms.ModelForm):
    
    from_city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True),
        empty_label="Выберите город...",
        widget=forms.Select(attrs={'class': SELECT_CLASSES})
    )
    to_city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True),
        empty_label="Выберите город...",
        widget=forms.Select(attrs={'class': SELECT_CLASSES})
    )

    class Meta:
        model = Shipment
        fields = [
            'from_city', 'from_address', 
            'to_city', 'to_address', 
            'weight', 'volume', 
            'cargo_description', 'pickup_date'
        ]
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date', 'class': CONTROL_CLASSES}),
            'from_address': forms.TextInput(attrs={'placeholder': 'Улица, дом, склад забора', 'class': CONTROL_CLASSES}),
            'to_address': forms.TextInput(attrs={'placeholder': 'Улица, дом, пункт назначения', 'class': CONTROL_CLASSES}),
            'weight': forms.NumberInput(attrs={'placeholder': 'В тоннах (например: 1.5)', 'step': '0.01', 'class': CONTROL_CLASSES}),
            'volume': forms.NumberInput(attrs={'placeholder': 'В м³ (необязательно)', 'step': '0.01', 'class': CONTROL_CLASSES}),
            'cargo_description': forms.Textarea(attrs={'placeholder': 'Что везем? Особенности груза...', 'rows': 2, 'class': CONTROL_CLASSES}),
        }