# ── Remplace ENTIÈREMENT apps/core/views.py ──

from django.shortcuts import render, redirect
from django.contrib import messages
from apps.techniciens.models import Technicien, SPECIALITES
from apps.core.models import ContactMessage


def accueil(request):
    techniciens = Technicien.objects.filter(actif=True, disponibilite='disponible')
    return render(request, 'core/accueil.html', {
        'techniciens': techniciens,
        'specialites': SPECIALITES,
        'total_techniciens': Technicien.objects.filter(actif=True).count(),
    })


def services(request):
    return render(request, 'core/services.html')


def a_propos(request):
    return render(request, 'core/a_propos.html')


def contact(request):
    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        email       = request.POST.get('email', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        if nom and email and commentaire:
            ContactMessage.objects.create(
                nom=nom,
                email=email,
                commentaire=commentaire,
            )
            messages.success(request, 'Message envoyé ! Nous vous répondrons bientôt.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

        return redirect('core:contact')

    return render(request, 'core/contact.html')


def surveillance(request):
    techniciens = Technicien.objects.filter(actif=True, specialite='surveillance')
    return render(request, 'core/surveillance.html', {'techniciens': techniciens})