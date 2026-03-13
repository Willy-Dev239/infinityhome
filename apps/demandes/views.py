from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Demande, Notification, Paiement, InstructionPaiement, TYPES_TRAVAUX
from .forms import DemandeForm


# ─────────────────────────────────────────────
#  Nouvelle demande
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
#  Mes demandes
# ─────────────────────────────────────────────
@login_required
def mes_demandes(request):
    demandes = Demande.objects.filter(client=request.user).order_by('-date_creation')
    return render(request, 'demandes/mes_demandes.html', {'demandes': demandes})


# ─────────────────────────────────────────────
#  Détail d'une demande
# ─────────────────────────────────────────────
@login_required
def detail_demande(request, pk):
    demande = get_object_or_404(Demande, pk=pk, client=request.user)

    # Paiement existant pour cette demande
    paiement = Paiement.objects.filter(
        commande=demande,
        client=request.user
    ).order_by('-created_at').first()

    # Notification de paiement non lue envoyée par l'admin
    notif_paiement = Notification.objects.filter(
        utilisateur=request.user,
        demande=demande,
        titre='Action requise : Paiement',
        lue=False,
    ).order_by('-date').first()

    return render(request, 'demandes/detail_demande.html', {
        'demande':        demande,
        'paiement':       paiement,
        'notif_paiement': notif_paiement,
    })


# ─────────────────────────────────────────────
#  Notifications
# ─────────────────────────────────────────────
@login_required
def notifications(request):
    notifs = Notification.objects.filter(utilisateur=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'demandes/notifications.html', {'notifications': notifs})


@login_required
def notif_count(request):
    count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    return JsonResponse({'count': count})


# ─────────────────────────────────────────────
#  API : Marquer une notification comme lue
# ─────────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def notif_marquer_lue(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, utilisateur=request.user)
    notif.lue = True
    notif.save(update_fields=['lue'])
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
#  API : Instructions d'un mode de paiement
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def get_instructions(request, mode_paiement):
    try:
        instruction = InstructionPaiement.objects.get(mode_paiement=mode_paiement, actif=True)
        return JsonResponse({
            'success': True,
            'data': {
                'mode':        instruction.mode_paiement,
                'titre':       instruction.titre,
                'description': instruction.description,
                'etapes':      instruction.etapes,
            }
        })
    except InstructionPaiement.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Aucune instruction disponible pour le mode "{mode_paiement}".'
        }, status=404)


# ─────────────────────────────────────────────
#  API : Toutes les instructions actives
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def get_toutes_instructions(request):
    instructions = InstructionPaiement.objects.filter(actif=True)
    data = [{
        'mode':        i.mode_paiement,
        'titre':       i.titre,
        'description': i.description,
        'etapes':      i.etapes,
    } for i in instructions]
    return JsonResponse({'success': True, 'data': data})


# ─────────────────────────────────────────────
#  API : Créer un paiement
# ─────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def creer_paiement(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON invalide.'}, status=400)

    for field in ['client_id', 'mode_paiement', 'montant']:
        if field not in body:
            return JsonResponse({'success': False, 'message': f'Champ requis manquant : {field}'}, status=400)

    mode = body.get('mode_paiement')
    if mode not in ['carte', 'livraison', 'mobile']:
        return JsonResponse({'success': False, 'message': 'mode_paiement invalide.'}, status=400)

    if mode == 'mobile' and (not body.get('fournisseur_mobile') or not body.get('numero_mobile')):
        return JsonResponse({'success': False, 'message': 'fournisseur_mobile et numero_mobile sont requis.'}, status=400)

    try:
        from django.contrib.auth.models import User
        client = User.objects.get(pk=body['client_id'])
    except Exception:
        return JsonResponse({'success': False, 'message': 'Client introuvable.'}, status=404)

    paiement = Paiement.objects.create(
        client=client,
        commande_id=body.get('commande_id'),
        mode_paiement=mode,
        montant=body['montant'],
        devise=body.get('devise', 'BIF'),
        fournisseur_mobile=body.get('fournisseur_mobile'),
        numero_mobile=body.get('numero_mobile'),
        derniers_chiffres_carte=body.get('derniers_chiffres_carte'),
        nom_titulaire_carte=body.get('nom_titulaire_carte'),
        statut='en_attente',
    )

    return JsonResponse({
        'success': True,
        'message': 'Paiement enregistré avec succès.',
        'data': {
            'paiement_id': paiement.pk,
            'statut':      paiement.statut,
            'mode':        paiement.mode_paiement,
            'montant':     str(paiement.montant),
            'devise':      paiement.devise,
            'created_at':  paiement.created_at.isoformat(),
        }
    }, status=201)


# ─────────────────────────────────────────────
#  API : Statut d'un paiement
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def statut_paiement(request, paiement_id):
    paiement = get_object_or_404(Paiement, pk=paiement_id)
    return JsonResponse({
        'success': True,
        'data': {
            'paiement_id':     paiement.pk,
            'statut':          paiement.statut,
            'statut_label':    paiement.get_statut_display(),
            'mode_paiement':   paiement.mode_paiement,
            'montant':         str(paiement.montant),
            'devise':          paiement.devise,
            'note_admin':      paiement.note_admin,
            'date_validation': paiement.date_validation.isoformat() if paiement.date_validation else None,
        }
    })
    
    
# ══════════════════════════════════════════════════════════════
# AJOUTER dans apps/demandes/views.py
# ══════════════════════════════════════════════════════════════

from django.utils import timezone


@login_required
@require_http_methods(["POST"])
def soumettre_bordereau(request):
    """
    POST /demandes/api/paiements/bordereau/
    Le client soumet son bordereau de preuve de paiement.
    Accepte multipart/form-data (pour la photo).
    """
    paiement_id      = request.POST.get('paiement_id')
    numero_bordereau = request.POST.get('numero_bordereau', '').strip()
    nom_expediteur   = request.POST.get('nom_expediteur', '').strip()
    date_virement    = request.POST.get('date_virement', '').strip()
    photo_recu       = request.FILES.get('photo_recu')

    # Validation
    if not paiement_id:
        return JsonResponse({'success': False, 'message': 'Paiement introuvable.'}, status=400)
    if not numero_bordereau:
        return JsonResponse({'success': False, 'message': 'Le numéro de bordereau est requis.'}, status=400)
    if not nom_expediteur:
        return JsonResponse({'success': False, 'message': "Le nom de l'expéditeur est requis."}, status=400)
    if not date_virement:
        return JsonResponse({'success': False, 'message': 'La date du virement est requise.'}, status=400)

    # Récupérer le paiement (appartient au client connecté)
    paiement = get_object_or_404(Paiement, pk=paiement_id, client=request.user)

    # Mettre à jour le paiement
    paiement.numero_bordereau             = numero_bordereau
    paiement.nom_expediteur               = nom_expediteur
    paiement.date_virement                = date_virement
    paiement.bordereau_soumis             = True
    paiement.date_soumission_bordereau    = timezone.now()
    if photo_recu:
        paiement.photo_recu = photo_recu
    paiement.save()

    # Notifier l'admin via une notification interne
    # (facultatif — dépend de ton système de notif admin)
    # On crée une notification pour le staff
    from django.contrib.auth.models import User
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        Notification.objects.create(
            utilisateur=admin,
            demande=paiement.commande,
            titre='Bordereau reçu — à vérifier',
            message=(
                f"{paiement.client.get_full_name() or paiement.client.username} "
                f"a soumis un bordereau pour le paiement #{paiement.pk} "
                f"(Demande #{paiement.commande_id}). "
                f"N° bordereau : {numero_bordereau}."
            ),
        )

    return JsonResponse({
        'success': True,
        'message': 'Bordereau soumis avec succès.',
    })


# ══════════════════════════════════════════════════════════════
# AJOUTER dans apps/demandes/urls.py
# ══════════════════════════════════════════════════════════════
# path('api/paiements/bordereau/', views.soumettre_bordereau, name='soumettre_bordereau'),