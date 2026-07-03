from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count
from transport.models import Testimonial, City
from transport.forms import CargoRequestForm


def home(request):
    if request.method == 'POST':
        form = CargoRequestForm(request.POST)
        if form.is_valid():
            cargo_request = form.save(commit=False)
            if request.user.is_authenticated:
                cargo_request.user = request.user

            cargo_request.save()

            messages.success(request, 'Ваша заявка успешно отправлена! Менеджер свяжется с вами в ближайшее время.')
            return redirect('main:home')
    else:
        form = CargoRequestForm()

    published_testimonials = Testimonial.objects.filter(is_published=True).order_by('-created_at')
    testimonials_stats = published_testimonials.aggregate(
        avg_rating=Avg('rating'),
        total=Count('id'),
    )
    avg_rating = testimonials_stats.get('avg_rating') or 0

    context = {
        'testimonials': published_testimonials[:6],
        'testimonials_stats': testimonials_stats,
        'testimonials_avg_rounded': round(avg_rating),
        'cities': City.objects.filter(is_active=True).order_by('name'),
        'cargo_form': form,
    }
    return render(request, 'html/home.html', context)


def page_not_found(request, exception):
    return render(request, 'html/404.html', status=404)


def server_error(request):
    return render(request, 'html/500.html', status=500)


def permission_denied(request, exception):
    return render(request, 'html/403.html', status=403)


def bad_request(request, exception):
    return render(request, 'html/400.html', status=400)