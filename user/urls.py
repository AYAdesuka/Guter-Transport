from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'user'

urlpatterns = [

    path('auth/', views.auth_page, name='auth'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('myprofile/', views.myprofile, name='my_profile'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('orders/', views.orders_dashboard, name='orders_dashboard'),
    path('create/', views.shipment_create_view, name='create'),
    path('api/calculate/', views.calculate_delivery_api, name='calculate_api'),
    path('api/autocomplete/', views.address_autocomplete_api, name='autocomplete_api'),
]