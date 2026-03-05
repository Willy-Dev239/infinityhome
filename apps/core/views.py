from django.shortcuts import render
from apps.techniciens.models import Technicien, SPECIALITES

def accueil(request):
    techniciens = Technicien.objects.filter(actif=True, disponibilite='disponible')
    return render(request, 'core/accueil.html', {
        'techniciens': techniciens,
        'specialites': SPECIALITES,
    })

def services(request):
    return render(request, 'core/services.html')

def a_propos(request):
    return render(request, 'core/a_propos.html')

def contact(request):
    from django.contrib import messages
    if request.method == 'POST':
        messages.success(request, 'Message envoye ! Nous vous repondrons bientot.')
    return render(request, 'core/contact.html')

def surveillance(request):
    techniciens = Technicien.objects.filter(actif=True, specialite='surveillance')
    return render(request, 'core/surveillance.html', {'techniciens': techniciens})
