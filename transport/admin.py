from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (
    
    Testimonial, City,
    Driver, Vehicle, CargoRequest, Shipment, ShipmentStatusHistory
)

User = get_user_model()


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_display_links = ("id", "name")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_per_page = 20

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'user', 'rating', 'is_published', 'shipment', 'created_at')
    list_filter = ('is_published', 'rating', 'created_at')
    list_editable = ('is_published',)
    search_fields = ('client_name', 'text', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'shipment')
    actions = ('publish_reviews', 'unpublish_reviews')

    @admin.action(description='Опубликовать выбранные отзывы')
    def publish_reviews(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'Опубликовано отзывов: {updated}')

    @admin.action(description='Снять с публикации')
    def unpublish_reviews(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Снято с публикации: {updated}')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'license_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('last_name', 'first_name', 'phone', 'license_number')
    list_editable = ('is_active',)

    @admin.display(description='ФИО')
    def full_name(self, obj):
        return obj.full_name


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'brand', 'model_name', 'vehicle_type', 'capacity_tons', 'is_active')
    list_filter = ('vehicle_type', 'is_active')
    search_fields = ('license_plate', 'brand', 'model_name')
    list_editable = ('is_active',)


@admin.register(CargoRequest)
class CargoRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'status', 'user', 'contact_name', 'from_city', 'to_city',
        'tariff', 'estimated_price', 'pickup_date', 'weight', 'created_at',
    )
    list_editable = ('status',)
    list_filter = ('status', 'tariff', 'pickup_date', 'created_at')
    search_fields = (
        'id', 'contact_name', 'contact_phone',
        'from_city__name', 'to_city__name', 'from_address', 'to_address',
    )
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by')
    autocomplete_fields = ('user',)

    fieldsets = (
        ('Управление статусом', {
            'fields': ('status', 'user', 'reviewed_by', 'reviewed_at')
        }),
        ('Маршрут', {
            'fields': ('from_city', 'from_address', 'to_city', 'to_address', 'distance_km')
        }),
        ('Параметры груза', {
            'fields': ('weight', 'volume', 'pickup_date', 'cargo_description', 'tariff', 'estimated_price')
        }),
        ('Контакты клиента', {
            'fields': ('contact_name', 'contact_phone')
        }),
        ('Служебная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


class ShipmentStatusHistoryInline(admin.TabularInline):
    model = ShipmentStatusHistory
    extra = 1
    readonly_fields = ('created_at', 'updated_by')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_number', 'user', 'from_city', 'to_city',
        'driver', 'vehicle', 'weight', 'status', 'price', 'pickup_date',
    )
    list_filter = ('status', 'created_at', 'pickup_date')
    search_fields = (
        'tracking_number', 'user__last_name', 'user__first_name',
        'from_city__name', 'to_city__name', 'driver__last_name', 'vehicle__license_plate',
    )
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
    autocomplete_fields = ('user', 'cargo_request', 'driver', 'vehicle')
    inlines = [ShipmentStatusHistoryInline]


@admin.register(ShipmentStatusHistory)
class ShipmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'created_at', 'updated_by')
    list_filter = ('status',)
    readonly_fields = ('created_at',)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'last_name', 'first_name', 'phone', 'is_staff', 'is_active')
    search_fields = ('username', 'last_name', 'first_name', 'phone', 'email')

    UserAdmin.search_fields = search_fields
    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('middle_name', 'birth_date', 'phone', 'address'),
        }),
    )