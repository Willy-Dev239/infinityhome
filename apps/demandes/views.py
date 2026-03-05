from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Demande, Notification, TYPES_TRAVAUX


# demandes/views.py

from django.shortcuts import render, redirect
from .forms import DemandeForm

@login_required
def nouvelle_demande(request):
    if request.method == 'POST':
        form = DemandeForm(request.POST, request.FILES)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.client = request.user
            demande.save()
            messages.success(request, "✅ Votre demande a été créée avec succès ! Un technicien vous sera assigné rapidement.")
            return redirect('demandes:mes_demandes')
        else:
            messages.error(request, "❌ Erreur dans le formulaire. Veuillez vérifier les champs.")
    else:
        form = DemandeForm()
    
    return render(request, 'demandes/nouvelle_demande.html', {'form': form})
# @login_required
# def nouvelle_demande(request):
#     if request.method == 'POST':
#         demande = Demande.objects.create(
#             client=request.user,
#             type_travaux=request.POST['type_travaux'],
#             titre=request.POST['titre'],
#             description=request.POST['description'],
#             localite=request.POST['localite'],
#             adresse=request.POST['adresse'],
#             urgence=request.POST.get('urgence', 'normale'),
#         )
#         if 'photo' in request.FILES:
#             demande.photo = request.FILES['photo']
#             demande.save()
#         # Notifier le client
#         Notification.objects.create(
#             utilisateur=request.user,
#             demande=demande,
#             titre='Demande soumise avec succes',
#             message=f'Votre demande "{demande.titre}" a ete soumise. Un technicien vous sera assigne bientot.',
#         )
#         messages.success(request, 'Demande soumise avec succes !')
#         return redirect('demandes:mes_demandes')
#     return render(request, 'demandes/nouvelle_demande.html', {'types': TYPES_TRAVAUX})

@login_required
def mes_demandes(request):
    demandes = Demande.objects.filter(client=request.user).order_by('id')
    return render(request, 'demandes/mes_demandes.html', {'demandes': demandes})

@login_required
def detail_demande(request, pk):
    demande = get_object_or_404(Demande, pk=pk, client=request.user)
    return render(request, 'demandes/detail_demande.html', {'demande': demande})

@login_required
def notifications(request):
    notifs = Notification.objects.filter(utilisateur=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'demandes/notifications.html', {'notifications': notifs})

@login_required
def notif_count(request):
    count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    return JsonResponse({'count': count})
