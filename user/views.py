import random
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from .models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from geopy.distance import geodesic
from geopy.exc import GeopyError
from transport.forms import ShipmentForm
from user.forms import CargoRequestCreateForm
from transport.models import Shipment, CargoRequest, City


EXCLUDED_NOMINATIM_TYPES = {
    'shop', 'supermarket', 'company', 'commercial', 'industrial',
    'warehouse', 'office', 'restaurant', 'cafe', 'hotel',
    'fuel', 'pharmacy', 'bank', 'atm', 'pub', 'bar', 'mall',
    'convenience', 'department_store', 'fast_food',
}

SKIP_ADDRESS_SEGMENTS = {
    'россия', 'russia', 'беларусь', 'belarus', 'казахстан', 'kazakhstan',
}

NOMINATIM_HEADERS = {
    'User-Agent': 'GuterTransportLogisticsSystem_v2/1.0 (myproject@guter.local)',
}
NOMINATIM_SEARCH_URL = 'https://nominatim.openstreetmap.org/search'


def nominatim_search(query, limit=5):
    if not query or len(query.strip()) < 2:
        return []
    try:
        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params={
                'q': query.strip(),
                'format': 'json',
                'addressdetails': 1,
                'limit': limit,
                'accept-language': 'ru',
                'countrycodes': 'ru,by,kz',
            },
            headers=NOMINATIM_HEADERS,
            timeout=8,
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return []


def build_geocode_queries(address_string):
    address = address_string.strip()
    queries = [address]
    lower = address.lower()
    if 'россия' not in lower and 'russia' not in lower:
        queries.append(f'{address}, Россия')

    parts = [part.strip() for part in address.split(',') if part.strip()]
    if len(parts) >= 2:
        city_street = f'{parts[0]}, {parts[1]}'
        if city_street not in queries:
            queries.append(f'{city_street}, Россия')
    if parts and parts[0] not in queries:
        queries.append(f'{parts[0]}, Россия')
    return queries


def resolve_address_coordinates(address_string, lat=None, lon=None):
    if lat not in (None, '') and lon not in (None, ''):
        try:
            return float(lat), float(lon), None
        except (TypeError, ValueError):
            pass

    for query in build_geocode_queries(address_string):
        results = nominatim_search(query, limit=1)
        if results:
            item = results[0]
            return float(item['lat']), float(item['lon']), item
    return None, None, None


def get_city_name_from_nominatim_item(item, address_string):
    if item:
        addr = item.get('address') or {}
        city_name = (
            addr.get('city') or addr.get('town') or addr.get('village')
            or addr.get('hamlet') or addr.get('municipality')
        )
        if city_name:
            return city_name[:100]

    if address_string:
        city_name = address_string.split(',')[0].strip()
        if city_name:
            return city_name[:100]
    return 'Не указан'


def format_short_address(item):
    addr = item.get('address') or {}

    locality = (
        addr.get('city') or addr.get('town') or addr.get('village')
        or addr.get('hamlet') or addr.get('municipality') or addr.get('suburb')
    )
    road = addr.get('road') or addr.get('pedestrian') or addr.get('street')
    house = addr.get('house_number')

    parts = []
    if locality:
        parts.append(locality)
    if road:
        road_lower = road.lower()
        if any(marker in road_lower for marker in ('ул', 'пр', 'пер', 'бул', 'ш.', 'шоссе')):
            road_label = road
        else:
            road_label = f'ул. {road}'
        parts.append(f'{road_label}, {house}' if house else road_label)
    elif house and locality:
        parts.append(f'д. {house}')

    if parts:
        return ', '.join(parts)[:120]

    display = (item.get('display_name') or '').strip()
    if not display:
        return ''

    segments = [segment.strip() for segment in display.split(',') if segment.strip()]
    filtered = []
    for segment in segments:
        if segment.isdigit() or (len(segment) == 6 and segment.isdigit()):
            continue
        if segment.lower() in SKIP_ADDRESS_SEGMENTS:
            continue
        filtered.append(segment)
        if len(filtered) >= 3:
            break
    return ', '.join(filtered)[:120]


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        reg_type = request.POST.get('reg_type', 'client')
        company_name = request.POST.get('company_name') if reg_type == 'b2b' else None

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует.')
            return redirect('user:auth')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с такой электронной почтой уже зарегистрирован.')
            return redirect('user:auth')

        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                account_type=reg_type,
                company_name=company_name
            )
            
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('/')
            
        except Exception as e:
            messages.error(request, f'Произошла ошибка при регистрации: {e}')
            return redirect('user:auth')

    return redirect('user:auth')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Рады видеть вас снова, {user.first_name}!')
            return redirect('/')
        else:
            messages.error(request, 'Неверный пароль или электронная почта.')
            return redirect('user:auth')

    return redirect('user:auth')


def auth_page(request):
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'html/auth.html')


@login_required(login_url='user:auth_page')
def myprofile(request):
    user_requests = request.user.cargo_requests.select_related('from_city', 'to_city').all()
    
    if request.method == 'POST' and 'create_shipment' in request.POST:
        # Важно: используем CargoRequestCreateForm вместо ShipmentForm!
        form = CargoRequestCreateForm(request.POST)
        if form.is_valid(): 
            cargo_request = form.save(commit=False)
            cargo_request.user = request.user
            cargo_request.status = 'new'  # Просто "Новая", никакого трек-номера тут нет!
            
            # Рассчитываем цену для заявки
            from_city = form.cleaned_data['from_city']
            to_city = form.cleaned_data['to_city']
            tariff = form.cleaned_data['tariff']
            weight = float(form.cleaned_data['weight'])
            volume = float(form.cleaned_data['volume'])

            # Наша логика расчёта (с учётом внутригородских рейсов)
            if from_city == to_city:
                distance_km, price = 0.0, 2500.0 # Твой базовый тариф
                # Тут можно скопировать логику наценок за вес/объем/тариф, если нужно
            else:
                distance_km, price = calculate_delivery_price_for_cities(
                    from_city, to_city, weight, volume, tariff
                )

            cargo_request.distance_km = distance_km
            cargo_request.estimated_price = price
            cargo_request.save()
            
            messages.success(request, 'Заявка успешно создана и отправлена на модерацию!')
            return redirect('user:my_profile')
    else:
        form = CargoRequestCreateForm()

    context = {
        'user': request.user,
        'requests': user_requests,
        'requests_count': user_requests.count(),
        'form': form
    }
    return render(request, 'html/profile.html', context)

@login_required
def orders_dashboard(request):
    if request.user.is_staff:
        shipments = Shipment.objects.select_related('user', 'from_city', 'to_city').all()
        requests = CargoRequest.objects.select_related('user', 'from_city', 'to_city').all()
    else:
        shipments = Shipment.objects.select_related('from_city', 'to_city').filter(user=request.user)
        requests = CargoRequest.objects.select_related('from_city', 'to_city').filter(user=request.user)

    if request.method == 'POST' and request.user.is_staff:
        action = request.POST.get('action')

        if 'shipment_id' in request.POST:
            shipment = get_object_or_404(Shipment, id=request.POST.get('shipment_id'))
            if action == 'cancel':
                shipment.status = 'canceled'
            elif action == 'change_status':
                shipment.status = request.POST.get('status')
            shipment.save()
            
        elif 'request_id' in request.POST:
            cargo_req = get_object_or_404(CargoRequest, id=request.POST.get('request_id'))
            
            if action == 'cancel':
                cargo_req.status = 'canceled'
                cargo_req.save()
                messages.warning(request, f"Заявка №{cargo_req.id} отклонена.")
                
            elif action == 'change_status':
                new_status = request.POST.get('status')
                cargo_req.status = new_status
                cargo_req.save()
                
                # Если менеджер одобрил заявку (замени 'approved' на свой статус, если в базе он называется иначе, например 'confirmed')
                if new_status == 'approved' or new_status == 'confirmed':
                    
                    # Проверяем по логике проекта, нет ли уже созданного Shipment, чтобы избежать дублирования
                    # (Ищем отправление этого же пользователя с теми же городами, весом и объёмом)
                    duplicate_exists = Shipment.objects.filter(
                        user=cargo_req.user,
                        from_city=cargo_req.from_city,
                        to_city=cargo_req.to_city,
                        weight=cargo_req.weight,
                        volume=cargo_req.volume,
                        status='new'
                    ).exists()
                    
                    if not duplicate_exists:
                        # Автоматически создаем подтвержденную поездку (Shipment) на основе заявки
                        Shipment.objects.create(
                            user=cargo_req.user,
                            from_city=cargo_req.from_city,
                            to_city=cargo_req.to_city,
                            weight=cargo_req.weight,
                            volume=cargo_req.volume,
                            status='new',  # Рейс создается в статусе "Новый/В обработке"
                            tracking_number=f"GT-{random.randint(10000, 99999)}",  # ТРЕК ГЕНЕРИРУЕТСЯ ТУТ
                            price=cargo_req.estimated_price if cargo_req.estimated_price else 0.0
                        )
                        messages.success(request, f"Заявка №{cargo_req.id} успешно одобрена. Сгенерировано отправление с трек-номером!")
            
        return redirect('user:orders_dashboard')

    context = {
        'shipments': shipments,
        'requests': requests,
        'shipment_statuses': Shipment.STATUS_CHOICES,
        'request_statuses': CargoRequest.STATUS_CHOICES,
    }
    return render(request, 'html/orders_list.html', context)


def get_coordinates(address_string, lat=None, lon=None):
    coords_lat, coords_lon, _ = resolve_address_coordinates(address_string, lat, lon)
    if coords_lat is not None and coords_lon is not None:
        return (coords_lat, coords_lon)
    return None


def get_route_distance_km(from_address, to_address, from_lat=None, from_lon=None, to_lat=None, to_lon=None):
    coords_from = get_coordinates(from_address, from_lat, from_lon)
    coords_to = get_coordinates(to_address, to_lat, to_lon)

    if not coords_from or not coords_to:
        return 0.0

    # 1. Пробуем OSRM (по дорогам)
    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{coords_from[1]},{coords_from[0]};{coords_to[1]},{coords_to[0]}?overview=false"
        )
        response = requests.get(url, timeout=4) # Уменьшил таймаут, чтобы юзер не ждал долго
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                return round(data['routes'][0]['distance'] / 1000, 1)
    except Exception as e:
        print(f"Ошибка OSRM (переключаемся на геодезику): {e}")

    try:
        direct_dist = geodesic(coords_from, coords_to).kilometers
        return round(direct_dist * 1.2, 1)
    except GeopyError:
        return 0.0


def calculate_delivery_price(
    from_address, to_address, weight=0.0, volume=0.0, tariff='standard',
    from_lat=None, from_lon=None, to_lat=None, to_lon=None,
):
    if not from_address or not to_address:
        return 0.0, 0.0

    distance_km = get_route_distance_km(
        from_address, to_address, from_lat, from_lon, to_lat, to_lon,
    )

    if not distance_km:
        return 0.0, 0.0

    base_rate_per_km = 6.0
    cost_by_distance = base_rate_per_km * distance_km
    extra_charges = 0.0

    if weight > 0 and volume > 0:
        density = (weight * 1000) / volume
        extra_charges = volume * 300.0 if density < 250 else weight * 500.0
    elif weight > 0:
        extra_charges = weight * 500.0
    elif volume > 0:
        extra_charges = volume * 300.0

    price = cost_by_distance + extra_charges

    if tariff == 'express':
        price *= 1.5
    elif tariff == 'refrigerated':
        price *= 1.8

    if price < 2000:
        price = 2000.0

    return distance_km, round(price, 2)


def calculate_delivery_price_for_cities(from_city, to_city, weight=0.0, volume=0.0, tariff='standard'):
    from_query = f'{from_city.name}, Россия'
    to_query = f'{to_city.name}, Россия'
    return calculate_delivery_price(from_query, to_query, weight, volume, tariff)

def calculate_delivery_api(request):
    from_city_id = request.GET.get('from_city_id', '').strip()
    to_city_id = request.GET.get('to_city_id', '').strip()
    tariff = request.GET.get('tariff', 'standard').strip()

    raw_weight = request.GET.get('weight', '').strip()
    try:
        weight = float(raw_weight.replace(',', '.')) if raw_weight else 0.0
    except (ValueError, TypeError):
        weight = 0.0

    raw_volume = request.GET.get('volume', '').strip()
    try:
        volume = float(raw_volume.replace(',', '.')) if raw_volume else 0.0
    except (ValueError, TypeError):
        volume = 0.0

    if not from_city_id or not to_city_id:
        return JsonResponse({'error': 'Не выбраны города'}, status=400)

    # Если города одинаковые — рассчитываем как внутригородской рейс
    if from_city_id == to_city_id:
        try:
            city = City.objects.get(id=from_city_id, is_active=True)
        except City.DoesNotExist:
            return JsonResponse({'error': 'Город не найден'}, status=404)
        

        base_city_price = 2500.0
        
        extra_charges = 0.0
        if weight > 0 and volume > 0:
            density = (weight * 1000) / volume
            extra_charges = volume * 300.0 if density < 250 else weight * 500.0
        elif weight > 0:
            extra_charges = weight * 500.0
        elif volume > 0:
            extra_charges = volume * 300.0

        price = base_city_price + extra_charges

        if tariff == 'express':
            price *= 1.5
        elif tariff == 'refrigerated':
            price *= 1.8

        return JsonResponse({
            'distance': 0.0,
            'price': round(price, 2),
            'from_city': city.name,
            'to_city': city.name,
        })

    try:
        from_city = City.objects.get(id=from_city_id, is_active=True)
        to_city = City.objects.get(id=to_city_id, is_active=True)
    except City.DoesNotExist:
        return JsonResponse({'error': 'Город не найден'}, status=404)

    distance_km, price = calculate_delivery_price_for_cities(
        from_city, to_city, weight, volume, tariff,
    )

    return JsonResponse({
        'distance': distance_km,
        'price': price,
        'from_city': from_city.name,
        'to_city': to_city.name,
    })


@login_required(login_url='user:auth')
def shipment_create_view(request):
    if request.method == 'POST':
        form = CargoRequestCreateForm(request.POST)
        if form.is_valid():
            from_city = form.cleaned_data['from_city']
            to_city = form.cleaned_data['to_city']
            tariff = form.cleaned_data['tariff']

            weight = float(form.cleaned_data['weight'])
            volume = float(form.cleaned_data['volume'])

            distance_km, price = calculate_delivery_price_for_cities(
                from_city, to_city, weight, volume, tariff,
            )

            cargo_request = form.save(commit=False)
            cargo_request.user = request.user
            cargo_request.status = 'new'
            cargo_request.tariff = tariff
            cargo_request.estimated_price = price if price else None
            cargo_request.distance_km = distance_km if distance_km else None
            cargo_request.save()

            messages.success(
                request,
                'Заявка отправлена! Менеджер проверит её и назначит перевозку.',
            )
            return redirect('user:orders_dashboard')

        messages.error(request, 'Проверьте правильность заполнения формы.')
    else:
        form = CargoRequestCreateForm()

    return render(request, 'html/shipment_create.html', {'form': form})