from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (
    SiteSettings, ServiceCategory, Service, Client,
    PortfolioProject, ProjectImage, Testimonial,
    CargoRequest, Shipment, ShipmentStatusHistory
)

User = get_user_model()


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('title', 'phone', 'email')
    
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)  # Обязательно для autocomplete_fields


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price_from', 'is_active', 'order')
    list_editable = ('price_from', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'short_description')  # Обязательно для autocomplete_fields
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('category',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_logo', 'order')
    list_editable = ('order',)
    search_fields = ('name',)  # Обязательно для autocomplete_fields
    ordering = ('order', 'name')

    def get_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:contain" />', obj.logo.url)
        return "—"
    get_logo.short_description = "Логотип"


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3
    fields = ('image', 'caption', 'order')


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'from_city', 'to_city', 'date', 'is_featured')
    list_filter = ('is_featured', 'client', 'service')
    search_fields = ('title', 'from_city', 'to_city')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('client', 'service')
    inlines = [ProjectImageInline]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'rating', 'is_published', 'created_at')
    list_filter = ('is_published', 'rating')
    search_fields = ('client_name', 'text')
    readonly_fields = ('created_at',)


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
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)

    fieldsets = (
        ('Управление статусом', {
            'fields': ('status', 'user')
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
    list_display = ('tracking_number', 'user', 'from_city', 'to_city', 'weight', 'status', 'price', 'pickup_date')
    list_filter = ('status', 'created_at', 'pickup_date')
    search_fields = ('tracking_number', 'user__last_name', 'user__first_name', 'from_city__name', 'to_city__name')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
    autocomplete_fields = ('user',)
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
    
    # Добавляем в поиск, чтобы autocomplete_fields на User работал без ошибок
    UserAdmin.search_fields = search_fields 
    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('middle_name', 'birth_date', 'phone', 'address'),
        }),
    )