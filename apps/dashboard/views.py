import functools
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.demandes.models import Demande, Notification, STATUTS
from apps.techniciens.models import Technicien, SPECIALITES, DISPONIBILITE
from apps.accounts.models import Profil

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
