import requests
import random
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import CustomUser, EmailVerificationCode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from geopy.distance import geodesic
from geopy.exc import GeopyError
from transport.forms import ShipmentForm
from user.forms import CargoRequestCreateForm, CustomPasswordChangeForm, TestimonialCreateForm
from transport.models import Shipment, CargoRequest, City, Driver, Vehicle, ShipmentStatusHistory, Testimonial
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import EmailVerificationCode


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
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        verification_code = request.POST.get('verification_code', '').strip()

        reg_type = request.POST.get('reg_type', 'client')
        company_name = request.POST.get('company_name') if reg_type == 'b2b' else None

        if not verification_code:
            messages.error(request, 'Введите код подтверждения из письма.')
            return redirect('user:auth')

        if not EmailVerificationCode.verify(email, verification_code):
            messages.error(request, 'Неверный или просроченный код подтверждения. Запросите новый.')
            return redirect('user:auth')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует.')
            return redirect('user:auth')

        if CustomUser.objects.filter(email__iexact=email).exists():
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
                company_name=company_name,
            )

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Email подтверждён.')
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


def get_user_display_name(user):
    if user.account_type == 'b2b' and user.company_name:
        return user.company_name
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return full_name or user.username


@login_required(login_url='user:auth')
def myprofile(request):
    user_requests = request.user.cargo_requests.select_related('from_city', 'to_city').all()
    pending_requests = user_requests.filter(status__in=['pending_review', 'processed'])
    user_shipments = Shipment.objects.filter(user=request.user).select_related('from_city', 'to_city')
    user_reviews = Testimonial.objects.filter(user=request.user).select_related('shipment').order_by('-created_at')
    reviewable_shipments = user_shipments.filter(status='delivered').exclude(testimonial__isnull=False)

    form = CargoRequestCreateForm()
    password_form = CustomPasswordChangeForm(user=request.user)
    review_form = TestimonialCreateForm(user=request.user)
    active_tab = request.GET.get('tab', 'overview')
    if active_tab not in ('overview', 'orders', 'requests', 'reviews', 'settings'):
        active_tab = 'overview'

    if request.method == 'POST':
        if 'change_password' in request.POST:
            active_tab = 'settings'
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Пароль успешно изменён.')
                return redirect(f"{request.path}?tab=settings")
            messages.error(request, 'Не удалось сменить пароль. Проверьте введённые данные.')

        elif 'create_review' in request.POST:
            active_tab = 'reviews'
            review_form = TestimonialCreateForm(user=request.user, data=request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.client_name = get_user_display_name(request.user)
                review.is_published = False
                review.save()
                messages.success(request, 'Спасибо! Отзыв отправлен на модерацию и скоро появится на сайте.')
                return redirect(f"{request.path}?tab=reviews")
            messages.error(request, 'Не удалось отправить отзыв. Проверьте форму.')

        elif 'create_shipment' in request.POST:
            form = CargoRequestCreateForm(request.POST)
            if form.is_valid():
                cargo_request = form.save(commit=False)
                cargo_request.user = request.user
                cargo_request.status = 'pending_review'

                from_city = form.cleaned_data['from_city']
                to_city = form.cleaned_data['to_city']
                tariff = form.cleaned_data['tariff']
                weight = float(form.cleaned_data['weight'])
                volume = float(form.cleaned_data['volume'])

                if from_city == to_city:
                    distance_km, price = 0.0, 2500.0
                else:
                    distance_km, price = calculate_delivery_price_for_cities(
                        from_city, to_city, weight, volume, tariff
                    )

                cargo_request.distance_km = distance_km
                cargo_request.estimated_price = price
                cargo_request.save()

                messages.success(request, 'Заявка успешно создана и отправлена на модерацию!')
                return redirect('user:my_profile')

    context = {
        'user': request.user,
        'requests': user_requests,
        'pending_requests': pending_requests,
        'requests_count': pending_requests.count(),
        'shipments': user_shipments,
        'shipments_count': user_shipments.count(),
        'reviews': user_reviews,
        'reviews_count': user_reviews.count(),
        'reviewable_shipments_count': reviewable_shipments.count(),
        'form': form,
        'password_form': password_form,
        'review_form': review_form,
        'active_tab': active_tab,
    }
    return render(request, 'html/profile.html', context)


def _orders_dashboard_redirect(request):
    return_query = request.POST.get('return_query', '').strip()
    base_url = reverse('user:orders_dashboard')
    if return_query:
        return redirect(f'{base_url}?{return_query}')
    return redirect(base_url)


ORDERS_PAGE_SIZE = 10


def _paginate_queryset(request, queryset, page_param):
    page_number = request.GET.get(page_param) or 1
    paginator = Paginator(queryset, ORDERS_PAGE_SIZE)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages or 1)
    return page_obj


def _attach_resource_availability(drivers, vehicles):
    busy_drivers_map = Shipment.get_busy_drivers_map()
    busy_vehicles_map = Shipment.get_busy_vehicles_map()

    for driver in drivers:
        driver.availability_shipment = busy_drivers_map.get(driver.id)
        driver.availability_busy = driver.availability_shipment is not None

    for vehicle in vehicles:
        vehicle.availability_shipment = busy_vehicles_map.get(vehicle.id)
        vehicle.availability_busy = vehicle.availability_shipment is not None

    available_drivers = sum(1 for driver in drivers if not driver.availability_busy)
    available_vehicles = sum(1 for vehicle in vehicles if not vehicle.availability_busy)

    return {
        'available_drivers_count': available_drivers,
        'available_vehicles_count': available_vehicles,
        'busy_drivers_count': len(busy_drivers_map),
        'busy_vehicles_count': len(busy_vehicles_map),
    }


def _filter_orders_querysets(shipments, requests, get_params):
    q = get_params.get('q', '').strip()
    shipment_status = get_params.get('shipment_status', '').strip()
    request_status = get_params.get('request_status', '').strip()

    if shipment_status:
        shipments = shipments.filter(status=shipment_status)

    if request_status == 'active':
        requests = requests.filter(status__in=['pending_review', 'processed'])
    elif request_status and request_status != 'all':
        requests = requests.filter(status=request_status)

    if q:
        request_filters = (
            Q(contact_name__icontains=q)
            | Q(contact_phone__icontains=q)
            | Q(from_city__name__icontains=q)
            | Q(to_city__name__icontains=q)
            | Q(from_address__icontains=q)
            | Q(to_address__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )
        if q.isdigit():
            request_filters |= Q(id=int(q))
        requests = requests.filter(request_filters)

        shipments = shipments.filter(
            Q(tracking_number__icontains=q)
            | Q(from_city__name__icontains=q)
            | Q(to_city__name__icontains=q)
            | Q(from_address__icontains=q)
            | Q(to_address__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(driver__last_name__icontains=q)
            | Q(driver__first_name__icontains=q)
            | Q(vehicle__license_plate__icontains=q)
            | Q(cargo_description__icontains=q)
        )

    return shipments, requests, q, shipment_status, request_status


@login_required(login_url='user:auth')
def orders_dashboard(request):
    shipment_qs = Shipment.objects.select_related(
        'user', 'from_city', 'to_city', 'driver', 'vehicle', 'cargo_request',
    )
    request_qs = CargoRequest.objects.select_related(
        'user', 'from_city', 'to_city', 'reviewed_by',
    )

    if request.user.is_staff:
        shipments = shipment_qs.all()
        requests = request_qs.all()
        drivers = Driver.objects.filter(is_active=True)
        vehicles = Vehicle.objects.filter(is_active=True)
    else:
        shipments = shipment_qs.filter(user=request.user)
        requests = request_qs.filter(user=request.user)
        drivers = Driver.objects.none()
        vehicles = Vehicle.objects.none()

    filter_params = request.GET.copy()
    if 'request_status' not in request.GET:
        filter_params['request_status'] = 'active'

    if request.method == 'POST' and request.user.is_staff:
        action = request.POST.get('action')

        if 'shipment_id' in request.POST:
            shipment = get_object_or_404(Shipment, id=request.POST.get('shipment_id'))
            if action == 'cancel':
                shipment.status = 'canceled'
                shipment.save()
                ShipmentStatusHistory.objects.create(
                    shipment=shipment,
                    status='canceled',
                    comment='Отменено администратором',
                    updated_by=request.user,
                )
                messages.warning(request, f'Отправка {shipment.tracking_number} отменена.')
            elif action == 'change_status':
                new_status = request.POST.get('status')
                if new_status and new_status in dict(Shipment.STATUS_CHOICES):
                    if new_status != shipment.status:
                        shipment.status = new_status
                        shipment.save()
                        ShipmentStatusHistory.objects.create(
                            shipment=shipment,
                            status=new_status,
                            updated_by=request.user,
                        )
                        messages.success(
                            request,
                            f'Статус отправки {shipment.tracking_number} изменён на «{shipment.get_status_display()}».',
                        )
                else:
                    messages.error(request, 'Выберите корректный статус отправки.')

        elif 'request_id' in request.POST:
            cargo_req = get_object_or_404(CargoRequest, id=request.POST.get('request_id'))

            if action == 'cancel':
                cargo_req.status = 'canceled'
                cargo_req.save()
                messages.warning(request, f'Заявка №{cargo_req.id} отклонена.')

            elif action == 'mark_processed':
                if cargo_req.status == 'pending_review':
                    cargo_req.status = 'processed'
                    cargo_req.save()
                    messages.info(request, f'Заявка №{cargo_req.id} взята в обработку.')
                else:
                    messages.error(request, f'Заявка №{cargo_req.id} уже обрабатывается или закрыта.')

            elif action == 'confirm':
                driver_id = request.POST.get('driver_id')
                vehicle_id = request.POST.get('vehicle_id')

                if not driver_id or not vehicle_id:
                    messages.error(request, 'Выберите водителя и транспорт для подтверждения заявки.')
                else:
                    driver = get_object_or_404(Driver, id=driver_id, is_active=True)
                    vehicle = get_object_or_404(Vehicle, id=vehicle_id, is_active=True)
                    try:
                        with transaction.atomic():
                            shipment = cargo_req.confirm(driver, vehicle, request.user)
                        messages.success(
                            request,
                            f'Заявка №{cargo_req.id} подтверждена. '
                            f'Создана отправка {shipment.tracking_number}.',
                        )
                    except ValidationError as exc:
                        messages.error(request, exc.messages[0] if exc.messages else str(exc))
            else:
                messages.error(request, 'Неизвестное действие для заявки.')

        return _orders_dashboard_redirect(request)

    shipments, requests, search_q, shipment_status, request_status = _filter_orders_querysets(
        shipments, requests, filter_params,
    )

    shipments_count = shipments.count()
    requests_count = requests.count()
    shipments_page = _paginate_queryset(request, shipments, 'shipments_page')
    requests_page = _paginate_queryset(request, requests, 'requests_page')

    availability_stats = {}
    if request.user.is_staff:
        availability_stats = _attach_resource_availability(drivers, vehicles)

    pagination_params = filter_params.copy()
    pagination_params.pop('shipments_page', None)
    pagination_params.pop('requests_page', None)

    context = {
        'shipments_page': shipments_page,
        'requests_page': requests_page,
        'drivers': drivers,
        'vehicles': vehicles,
        'shipment_statuses': Shipment.STATUS_CHOICES,
        'request_statuses': CargoRequest.STATUS_CHOICES,
        'search_q': search_q,
        'filter_shipment_status': shipment_status,
        'filter_request_status': request_status,
        'return_query': filter_params.urlencode(),
        'filter_query': pagination_params.urlencode(),
        'shipments_count': shipments_count,
        'requests_count': requests_count,
        **availability_stats,
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

    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{coords_from[1]},{coords_from[0]};{coords_to[1]},{coords_to[0]}?overview=false"
        )
        response = requests.get(url, timeout=4)
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

def track_shipment_api(request):
    tracking_number = request.GET.get('tracking_number', '').strip()
    if not tracking_number:
        return JsonResponse({'error': 'Введите трек-номер'}, status=400)

    shipment = (
        Shipment.objects.select_related('from_city', 'to_city', 'driver', 'vehicle')
        .filter(tracking_number__iexact=tracking_number)
        .first()
    )
    if not shipment:
        return JsonResponse({'error': 'Отправление с таким трек-номером не найдено'}, status=404)

    status_labels = dict(Shipment.STATUS_CHOICES)
    timeline = []
    for entry in shipment.history.order_by('created_at'):
        timeline.append({
            'status': entry.status,
            'label': status_labels.get(entry.status, entry.status),
            'comment': entry.comment,
            'at': timezone.localtime(entry.created_at).strftime('%d.%m.%Y %H:%M'),
        })

    if not timeline or timeline[-1]['status'] != shipment.status:
        timeline.append({
            'status': shipment.status,
            'label': shipment.get_status_display(),
            'comment': '',
            'at': timezone.localtime(shipment.updated_at).strftime('%d.%m.%Y %H:%M'),
            'current': True,
        })
    else:
        timeline[-1]['current'] = True

    progress_steps = [
        {'code': 'new', 'label': 'Принята'},
        {'code': 'confirmed', 'label': 'Подтверждена'},
        {'code': 'in_progress', 'label': 'В пути'},
        {'code': 'delivered', 'label': 'Доставлена'},
    ]
    status_order = [step['code'] for step in progress_steps]
    try:
        current_index = status_order.index(shipment.status)
    except ValueError:
        current_index = -1

    steps = []
    for idx, step in enumerate(progress_steps):
        if shipment.status in ('canceled', 'problem'):
            state = 'done' if idx == 0 else 'pending'
        elif idx < current_index:
            state = 'done'
        elif idx == current_index:
            state = 'active'
        else:
            state = 'pending'
        steps.append({**step, 'state': state})

    return JsonResponse({
        'tracking_number': shipment.tracking_number,
        'status': shipment.status,
        'status_display': shipment.get_status_display(),
        'route': f'{shipment.from_city.name} → {shipment.to_city.name}',
        'from_address': shipment.from_address or '',
        'to_address': shipment.to_address or '',
        'pickup_date': shipment.pickup_date.strftime('%d.%m.%Y'),
        'delivery_date_expected': (
            shipment.delivery_date_expected.strftime('%d.%m.%Y')
            if shipment.delivery_date_expected else None
        ),
        'weight': str(shipment.weight),
        'volume': str(shipment.volume) if shipment.volume else None,
        'price': str(shipment.price) if shipment.price else None,
        'driver': shipment.driver.full_name if shipment.driver else None,
        'vehicle': str(shipment.vehicle) if shipment.vehicle else None,
        'timeline': timeline,
        'steps': steps,
    })


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
            cargo_request.status = 'pending_review'
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


@require_POST
@csrf_protect
def send_verification_code_view(request):
    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse(
            {'error': 'Email обязателен для заполнения.'}, 
            status=400
        )

    try:
        code = str(random.randint(100000, 999999))

        expires_at = timezone.now() + timedelta(minutes=15)

        EmailVerificationCode.objects.create(
            email=email, 
            code=code,
            expires_at=expires_at
        )

        return JsonResponse({
            'message': 'Код подтверждения отправлен! Проверьте вашу почту.'
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'error': f'Произошла внутренняя ошибка сервера. {str(e)}'
        }, status=500)