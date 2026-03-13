import functools
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.demandes.models import Demande, Notification, STATUTS
from apps.techniciens.models import Technicien, SPECIALITES, DISPONIBILITE
from apps.accounts.models import Profil



from django.contrib.auth.decorators import login_required, user_passes_test

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from apps.demandes.models import Paiement, InstructionPaiement

is_admin = lambda u: u.is_staff or u.is_superuser

TYPE_TO_SPEC = {
    'electricite': 'electricien',
    'plomberie':   'plombier',
    'construction':'ingenieur',
    'soudure':     'soudeur',
    'peinture':    'peintre',
    'menuiserie':  'menuisier',
    'surveillance':'surveillance',
}

def admin_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard:home')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username',''), password=request.POST.get('password',''))
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('dashboard:home')
        error = 'Identifiants incorrects ou acces refuse.'
    return render(request, 'dashboard/login.html', {'error': error})

def admin_logout(request):
    logout(request)
    return redirect('dashboard:login')

@admin_required
def home(request):
    stats = {
        'total_demandes':   Demande.objects.count(),
        'en_attente':       Demande.objects.filter(statut='en_attente').count(),
        'en_cours':         Demande.objects.filter(statut__in=['assignee','en_cours']).count(),
        'terminees':        Demande.objects.filter(statut='terminee').count(),
        'total_techniciens':Technicien.objects.filter(actif=True).count(),
        'disponibles':      Technicien.objects.filter(disponibilite='disponible', actif=True).count(),
        'total_clients':    User.objects.filter(is_staff=False).count(),
    }
    return render(request, 'dashboard/home.html', {
        'stats': stats,
        'demandes_recentes': Demande.objects.order_by('-date_creation')[:8],
        'techniciens_dispo': Technicien.objects.filter(disponibilite='disponible', actif=True)[:6],
    })

@admin_required
def demandes(request):
    statut = request.GET.get('statut', '')
    qs = Demande.objects.select_related('client','technicien').order_by('id')
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'dashboard/demandes.html', {'demandes': qs, 'statut_actif': statut})

@admin_required
def demande_detail(request, pk):
    demande = get_object_or_404(Demande, pk=pk)
    specialite = TYPE_TO_SPEC.get(demande.type_travaux, demande.type_travaux)
    techniciens_dispo = Technicien.objects.filter(disponibilite='disponible', actif=True, specialite=specialite)
    tous_techniciens  = Technicien.objects.filter(actif=True, specialite=specialite)
    return render(request, 'dashboard/demande_detail.html', {
        'demande': demande,
        'techniciens_dispo': techniciens_dispo,
        'tous_techniciens': tous_techniciens,
        'statuts': STATUTS,
    })

@admin_required
def assigner_technicien(request, pk):
    demande = get_object_or_404(Demande, pk=pk)
    if request.method == 'POST':
        tech_id = request.POST.get('technicien_id')
        date_intervention = request.POST.get('date_intervention')
        if tech_id:
            tech = get_object_or_404(Technicien, pk=tech_id)
            demande.technicien = tech
            demande.statut = 'assignee'
            if date_intervention:
                demande.date_intervention = date_intervention
            demande.save()
            Notification.objects.create(
                utilisateur=demande.client,
                demande=demande,
                titre='Technicien assigne a votre demande',
                message=f'Bonjour {demande.client.first_name}, {tech.prenom} {tech.nom} ({tech.get_specialite_display()}) a ete assigne. Tel: {tech.telephone}',
            )
            messages.success(request, f'Technicien {tech.nom_complet} assigne !')
        else:
            messages.error(request, 'Veuillez choisir un technicien.')
    return redirect('dashboard:demande_detail', pk=pk)

@admin_required
def update_statut(request, pk):
    demande = get_object_or_404(Demande, pk=pk)
    if request.method == 'POST':
        new_statut = request.POST.get('statut')
        if new_statut:
            demande.statut = new_statut
            demande.save()
            Notification.objects.create(
                utilisateur=demande.client,
                demande=demande,
                titre='Statut mis a jour',
                message=f'Votre demande "{demande.titre}" est maintenant : {demande.get_statut_display()}.',
            )
            messages.success(request, 'Statut mis a jour.')
    return redirect('dashboard:demande_detail', pk=pk)

@admin_required
def techniciens(request):
    return render(request, 'dashboard/techniciens.html', {
        'techniciens': Technicien.objects.all().order_by('specialite','nom'),
    })

@admin_required
def technicien_add(request):
    if request.method == 'POST':
        try:
            t = Technicien(
                nom=request.POST['nom'], prenom=request.POST['prenom'],
                specialite=request.POST['specialite'], telephone=request.POST['telephone'],
                email=request.POST.get('email',''), localite=request.POST['localite'],
                disponibilite=request.POST.get('disponibilite','disponible'),
                experience=request.POST.get('experience', 0),
            )
            if 'photo' in request.FILES:
                t.photo = request.FILES['photo']
            t.save()
            messages.success(request, f'Technicien {t.nom_complet} ajoute !')
            return redirect('dashboard:techniciens')
        except Exception as e:
            messages.error(request, f'Erreur: {e}')
    return render(request, 'dashboard/technicien_form.html', {
        'specialites': SPECIALITES, 'disponibilites': DISPONIBILITE
    })

@admin_required
def technicien_edit(request, pk):
    tech = get_object_or_404(Technicien, pk=pk)
    if request.method == 'POST':
        tech.nom=request.POST['nom']; tech.prenom=request.POST['prenom']
        tech.specialite=request.POST['specialite']; tech.telephone=request.POST['telephone']
        tech.email=request.POST.get('email',''); tech.localite=request.POST['localite']
        tech.disponibilite=request.POST.get('disponibilite','disponible')
        tech.experience=request.POST.get('experience',0); tech.actif='actif' in request.POST
        if 'photo' in request.FILES:
            tech.photo = request.FILES['photo']
        tech.save()
        messages.success(request, f'Technicien {tech.nom_complet} mis a jour !')
        return redirect('dashboard:techniciens')
    return render(request, 'dashboard/technicien_form.html', {
        'tech': tech, 'specialites': SPECIALITES, 'disponibilites': DISPONIBILITE
    })

@admin_required
def clients(request):
    return render(request, 'dashboard/clients.html', {
        'clients': User.objects.filter(is_staff=False).order_by('-date_joined')
    })
    
    



# ─────────────────────────────────────────────
#  Liste des paiements
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiements_list(request):
    qs = Paiement.objects.select_related('client', 'commande').order_by('-created_at')

    filtre_statut = request.GET.get('statut', '')
    filtre_mode   = request.GET.get('mode', '')
    recherche     = request.GET.get('q', '')

    if filtre_statut:
        qs = qs.filter(statut=filtre_statut)
    if filtre_mode:
        qs = qs.filter(mode_paiement=filtre_mode)
    if recherche:
        qs = qs.filter(
            Q(client__username__icontains=recherche) |
            Q(client__first_name__icontains=recherche) |
            Q(client__last_name__icontains=recherche) |
            Q(client__email__icontains=recherche)
        )

    # Stats
    tous = Paiement.objects.all()
    stats = {
        'en_attente':   tous.filter(statut='en_attente').count(),
        'valides':      tous.filter(statut='valide').count(),
        'rejetes':      tous.filter(statut='rejete').count(),
        'total_valide': tous.filter(statut='valide').aggregate(t=Sum('montant'))['t'] or 0,
    }

    paginator = Paginator(qs, 15)
    page      = request.GET.get('page', 1)
    paiements = paginator.get_page(page)

    return render(request, 'dashboard/paiement_list.html', {
        'paiements':      paiements,
        'stats':          stats,
        'filtre_statut':  filtre_statut,
        'filtre_mode':    filtre_mode,
        'recherche':      recherche,
    })


# ─────────────────────────────────────────────
#  Détail d'un paiement
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiement_detail(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    instruction = InstructionPaiement.objects.filter(
        mode_paiement=paiement.mode_paiement, actif=True
    ).first()
    return render(request, 'dashboard/paiement_detail.html', {
        'paiement':    paiement,
        'instruction': instruction,
    })


# ─────────────────────────────────────────────
#  Valider un paiement
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiement_valider(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk, statut='en_attente')
    paiement.valider(request.user)
    messages.success(request, f'Paiement #{pk} validé avec succès.')
    return redirect('dashboard:paiements')


# ─────────────────────────────────────────────
#  Rejeter un paiement
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiement_rejeter(request, pk):
    if request.method == 'POST':
        paiement  = get_object_or_404(Paiement, pk=pk, statut='en_attente')
        note      = request.POST.get('note_admin', '').strip()
        paiement.rejeter(request.user, note=note or None)
        messages.success(request, f'Paiement #{pk} rejeté.')
    return redirect('dashboard:paiements')


# ─────────────────────────────────────────────
#  Configurer les instructions
# ─────────────────────────────────────────────
MODES = [
    ('carte',     'Carte Bancaire',  'credit-card'),
    ('livraison', 'À la Livraison',  'home'),
    ('mobile',    'Mobile Money',    'mobile-alt'),
]

@login_required
@user_passes_test(is_admin)
def instructions_paiement(request):
    instructions = InstructionPaiement.objects.all()

    # Préparer etapes_texte (une étape par ligne) pour chaque instruction
    for inst in instructions:
        inst.etapes_texte = '\n'.join(inst.etapes) if inst.etapes else ''

    return render(request, 'dashboard/instructionpaiement.html', {
        'modes':        MODES,
        'instructions': instructions,
    })


@login_required
@user_passes_test(is_admin)
def instructions_sauvegarder(request, mode):
    if request.method != 'POST':
        return redirect('dashboard:instructions_paiement')

    titre       = request.POST.get('titre', '').strip()
    description = request.POST.get('description', '').strip()
    etapes_raw  = request.POST.get('etapes', '')
    actif       = request.POST.get('actif', '1') == '1'

    # Convertir les lignes en liste
    etapes = [e.strip() for e in etapes_raw.splitlines() if e.strip()]

    InstructionPaiement.objects.update_or_create(
        mode_paiement=mode,
        defaults={
            'titre':       titre,
            'description': description,
            'etapes':      etapes,
            'actif':       actif,
        }
    )
    messages.success(request, f'Instructions "{dict((m[:2] for m in MODES)).get(mode, mode)}" sauvegardées.')
    return redirect('dashboard:instructions_paiement')







from apps.demandes.models import Demande, Paiement
from django.db.models import Count, Sum

stats = {
     # tes stats existantes
    'en_cours':              Demande.objects.filter(statut='en_cours').count(),
    'annulees':              Demande.objects.filter(statut='annulee').count(),
    'paiements_en_attente':  Paiement.objects.filter(statut='en_attente').count(),
}

paiements_recents = Paiement.objects.filter(
    statut='en_attente'
).select_related('client').order_by('-created_at')[:4]


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta, date
import json

from apps.demandes.models import Demande, Paiement

is_admin = lambda u: u.is_staff or u.is_superuser


@login_required
@user_passes_test(is_admin)
def statistiques(request):
    today = timezone.now().date()
    il_y_a_12_mois = today - timedelta(days=365)
    il_y_a_6_mois  = today - timedelta(days=180)

    # ── 1. Demandes par mois (12 derniers mois) ──
    demandes_par_mois_qs = (
        Demande.objects
        .filter(date_creation__date__gte=il_y_a_12_mois)
        .annotate(mois=TruncMonth('date_creation'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
    )
    mois_labels = []
    mois_data   = []
    mois_fr = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
    for row in demandes_par_mois_qs:
        m = row['mois']
        mois_labels.append(f"{mois_fr[m.month - 1]} {m.year}")
        mois_data.append(row['total'])

    # ── 2. Demandes par type de travaux ──
    types_qs = (
        Demande.objects
        .values('type_travaux')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    TYPES_MAP = {
        'electricite':  'Électricité',
        'plomberie':    'Plomberie',
        'construction': 'Construction',
        'soudure':      'Soudure',
        'peinture':     'Peinture',
        'menuiserie':   'Menuiserie',
        'surveillance': 'Surveillance',
        'autre':        'Autre',
    }
    types_labels = [TYPES_MAP.get(r['type_travaux'], r['type_travaux']) for r in types_qs]
    types_data   = [r['total'] for r in types_qs]

    # ── 3. Revenus paiements par mois (6 derniers mois) ──
    revenus_qs = (
        Paiement.objects
        .filter(statut='valide', created_at__date__gte=il_y_a_6_mois)
        .annotate(mois=TruncMonth('created_at'))
        .values('mois')
        .annotate(total=Sum('montant'))
        .order_by('mois')
    )
    rev_labels = []
    rev_data   = []
    for row in revenus_qs:
        m = row['mois']
        rev_labels.append(f"{mois_fr[m.month - 1]} {m.year}")
        rev_data.append(float(row['total'] or 0))

    # ── 4. Taux de complétion ──
    total_dem   = Demande.objects.count() or 1
    terminees   = Demande.objects.filter(statut='terminee').count()
    en_cours    = Demande.objects.filter(statut='en_cours').count()
    en_attente  = Demande.objects.filter(statut='en_attente').count()
    annulees    = Demande.objects.filter(statut='annulee').count()
    taux_completion = round((terminees / total_dem) * 100, 1)

    # ── 5. Techniciens les plus actifs (top 5) ──
    top_tech = (
        Demande.objects
        .filter(technicien__isnull=False)
        .values('technicien__prenom', 'technicien__nom', 'technicien__specialite')
        .annotate(nb=Count('id'), terminees=Count('id', filter=__import__('django.db.models', fromlist=['Q']).Q(statut='terminee')))
        .order_by('-nb')[:5]
    )
    tech_labels = [f"{t['technicien__prenom']} {t['technicien__nom']}" for t in top_tech]
    tech_data   = [t['nb'] for t in top_tech]
    tech_terminees = [t['terminees'] for t in top_tech]

    # ── 6. Demandes par localité (top 8) ──
    localites_qs = (
        Demande.objects
        .values('localite')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )
    loc_labels = [r['localite'] for r in localites_qs]
    loc_data   = [r['total'] for r in localites_qs]

    # ── 7. Délai moyen d'intervention (par mois) ──
    # Délai = date_intervention - date_creation (pour les demandes terminées avec date_intervention)
    delai_qs = (
        Demande.objects
        .filter(statut='terminee', date_intervention__isnull=False, date_creation__date__gte=il_y_a_6_mois)
        .annotate(mois=TruncMonth('date_creation'))
        .values('mois')
        .annotate(nb=Count('id'))
        .order_by('mois')
    )
    delai_labels = []
    delai_data   = []
    for row in delai_qs:
        m = row['mois']
        delai_labels.append(f"{mois_fr[m.month - 1]}")
        # Calcul approximatif côté Python
        dems = Demande.objects.filter(
            statut='terminee',
            date_intervention__isnull=False,
            date_creation__month=m.month,
            date_creation__year=m.year,
        )
        delais = [(d.date_intervention - d.date_creation.date()).days for d in dems if d.date_intervention]
        delai_data.append(round(sum(delais) / len(delais), 1) if delais else 0)

    # ── 8. Heatmap : demandes par jour de la semaine × heure ──
    heatmap_data = []
    jours = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
    for jour_idx in range(7):
        for heure in range(0, 24, 2):
            nb = Demande.objects.filter(
                date_creation__week_day=(jour_idx + 2) % 7 + 1,
                date_creation__hour__gte=heure,
                date_creation__hour__lt=heure + 2,
            ).count()
            heatmap_data.append({'x': heure, 'y': jour_idx, 'v': nb})

    # ── KPIs rapides ──
    ce_mois = Demande.objects.filter(
        date_creation__month=today.month,
        date_creation__year=today.year
    ).count()
    mois_precedent = Demande.objects.filter(
        date_creation__month=(today.replace(day=1) - timedelta(days=1)).month,
        date_creation__year=(today.replace(day=1) - timedelta(days=1)).year
    ).count()
    evolution = round(((ce_mois - mois_precedent) / max(mois_precedent, 1)) * 100, 1)

    revenus_mois = Paiement.objects.filter(
        statut='valide',
        created_at__month=today.month,
        created_at__year=today.year
    ).aggregate(t=Sum('montant'))['t'] or 0

    return render(request, 'dashboard/statistiques.html', {
        # Line chart
        'mois_labels':      json.dumps(mois_labels),
        'mois_data':        json.dumps(mois_data),
        # Types
        'types_labels':     json.dumps(types_labels),
        'types_data':       json.dumps(types_data),
        # Revenus
        'rev_labels':       json.dumps(rev_labels),
        'rev_data':         json.dumps(rev_data),
        # Completion
        'taux_completion':  taux_completion,
        'terminees':        terminees,
        'en_cours':         en_cours,
        'en_attente':       en_attente,
        'annulees':         annulees,
        'total_dem':        total_dem,
        # Techniciens
        'tech_labels':      json.dumps(tech_labels),
        'tech_data':        json.dumps(tech_data),
        'tech_terminees':   json.dumps(tech_terminees),
        'top_tech':         list(top_tech),
        # Localités
        'loc_labels':       json.dumps(loc_labels),
        'loc_data':         json.dumps(loc_data),
        # Délai
        'delai_labels':     json.dumps(delai_labels),
        'delai_data':       json.dumps(delai_data),
        # Heatmap
        'heatmap_data':     json.dumps(heatmap_data),
        # KPIs
        'ce_mois':          ce_mois,
        'evolution':        evolution,
        'revenus_mois':     revenus_mois,
    })
    
    
    
# ─────────────────────────────────────────────
#  Modifier un paiement (admin)
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiement_modifier(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:paiement_detail', pk=pk)

    paiement = get_object_or_404(Paiement, pk=pk)

    # Champs modifiables
    statut          = request.POST.get('statut', paiement.statut)
    montant         = request.POST.get('montant', paiement.montant)
    mode_paiement   = request.POST.get('mode_paiement', paiement.mode_paiement)
    fournisseur     = request.POST.get('fournisseur_mobile', paiement.fournisseur_mobile or '')
    numero_mobile   = request.POST.get('numero_mobile', paiement.numero_mobile or '')
    note_admin      = request.POST.get('note_admin', paiement.note_admin or '').strip()

    paiement.statut         = statut
    paiement.mode_paiement  = mode_paiement
    paiement.note_admin     = note_admin or None

    try:
        paiement.montant = float(montant)
    except (ValueError, TypeError):
        pass

    if mode_paiement == 'mobile':
        paiement.fournisseur_mobile = fournisseur or None
        paiement.numero_mobile      = numero_mobile or None

    # Si l'admin change le statut manuellement vers validé/rejeté, on enregistre qui l'a fait
    if statut in ('valide', 'rejete') and not paiement.valide_par:
        from django.utils import timezone
        paiement.valide_par      = request.user
        paiement.date_validation = timezone.now()

    paiement.save()
    messages.success(request, f'Paiement #{pk} modifié avec succès.')
    return redirect('dashboard:paiement_detail', pk=pk)


# ─────────────────────────────────────────────
#  Supprimer un paiement (admin)
# ─────────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def paiement_supprimer(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:paiement_detail', pk=pk)

    paiement = get_object_or_404(Paiement, pk=pk)
    paiement.delete()
    messages.success(request, f'Paiement #{pk} supprimé définitivement.')
    return redirect('dashboard:paiements')





"""
Ajout dans apps/dashboard/views_paiements.py

Vue : notifier_paiement
- L'admin envoie une notification au client pour lui demander de procéder au paiement
- Crée une Notification dans la base avec type 'paiement_requis'
- Redirige vers le détail du paiement avec message de succès
"""

# ─────────────────────────────────────────────
#  Notifier le client — ajouter dans views_paiements.py
# ─────────────────────────────────────────────
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages as django_messages

# Import ton modèle Notification (déjà dans apps.demandes)
from apps.demandes.models import Paiement, InstructionPaiement, Notification

is_admin = lambda u: u.is_staff or u.is_superuser


@login_required
@user_passes_test(is_admin)
def paiement_notifier(request, pk):
    """
    POST /dashboard/paiements/<pk>/notifier/
    Envoie une notification au client pour lui demander de régler son paiement.
    """
    if request.method != 'POST':
        return redirect('dashboard:paiement_detail', pk=pk)

    paiement = get_object_or_404(Paiement, pk=pk)
    message_custom = request.POST.get('message', '').strip()

    # Message par défaut si l'admin ne saisit rien
    instruction = InstructionPaiement.objects.filter(
        mode_paiement=paiement.mode_paiement, actif=True
    ).first()

    mode_label = {
        'carte': 'Carte Bancaire',
        'livraison': 'À la Livraison',
        'mobile': 'Mobile Money',
    }.get(paiement.mode_paiement, paiement.mode_paiement)

    if not message_custom:
        if instruction:
            message_custom = (
                f"Votre paiement pour la demande #{paiement.commande_id} est en attente. "
                f"Mode choisi : {mode_label}. "
                f"{instruction.description}"
            )
        else:
            message_custom = (
                f"Votre paiement pour la demande #{paiement.commande_id} est en attente. "
                f"Veuillez procéder au règlement via {mode_label}."
            )

    # Créer la notification pour le client
    Notification.objects.create(
        utilisateur=paiement.client,
        type='paiement_requis',          # type custom — voir note ci-dessous
        titre='Action requise : Paiement',
        message=message_custom,
        lien=f'/demandes/{paiement.commande_id}/' if paiement.commande_id else None,
        paiement=paiement,               # FK optionnelle — voir note
    )

    django_messages.success(
        request,
        f'Notification envoyée à {paiement.client.get_full_name() or paiement.client.username}.'
    )
    return redirect('dashboard:paiement_detail', pk=pk)
@login_required
@user_passes_test(is_admin)
def client_view_readonly(request, client_pk):
    from django.contrib.auth.models import User
    from apps.demandes.models import Demande, Paiement, Notification

    client = get_object_or_404(User, pk=client_pk, is_staff=False)

    demandes      = Demande.objects.filter(client=client).order_by('-date_creation')
    paiements     = Paiement.objects.filter(client=client).order_by('-created_at')
    notifications = Notification.objects.filter(utilisateur=client).order_by('-date')

    return render(request, 'dashboard/client_view_readonly.html', {
        'client':              client,
        'demandes':            demandes,
        'paiements':           paiements,
        'notifications':       notifications,
        'nb_demandes':         demandes.count(),
        'nb_paiements':        paiements.count(),
        'nb_notifs_non_lues':  notifications.filter(lue=False).count(),
    })

# ─────────────────────────────────────────────────────────────────────────────
#  NOTE : Si ton modèle Notification n'a pas encore ces champs, voici
#  les champs à ajouter dans apps/demandes/models.py → classe Notification :
#
#    titre   = models.CharField(max_length=255, default='Notification')
#    type    = models.CharField(max_length=50, default='info')
#    lien    = models.CharField(max_length=500, null=True, blank=True)
#    paiement= models.ForeignKey('Paiement', null=True, blank=True,
#                on_delete=models.SET_NULL, related_name='notifications')
#
#  Puis : python manage.py makemigrations && python manage.py migrate
# ─────────────────────────────────────────────────────────────────────────────