from django.shortcuts import render, redirect
from django.contrib import messages
from transport.models import Service, PortfolioProject, Testimonial
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
            return redirect('home')
    else:
        form = CargoRequestForm()

    context = {
        'services': Service.objects.filter(is_active=True)[:6],
        'featured_projects': PortfolioProject.objects.filter(is_featured=True)[:3],
        'testimonials': Testimonial.objects.filter(is_published=True)[:3],
        'cargo_form': form,
    }
    return render(request, 'html/home.html', context)