from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import InscriptionForm

def inscription(request):
    next_url = request.GET.get('next', '/')
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compte cree avec succes ! Connectez-vous.')
            return redirect('accounts:connexion')
    else:
        form = InscriptionForm()
    return render(request, 'accounts/inscription.html', {'form': form})

def connexion(request):
    next_url = request.GET.get('next', '/')
    if request.user.is_authenticated:
        return redirect(next_url)
    error = None
    if request.method == 'POST':
        next_url = request.POST.get('next', '/')
        user = authenticate(
            request,
            username=request.POST.get('username', ''),
            password=request.POST.get('password', '')
        )
        if user:
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name or user.username} !')
            return redirect(next_url)
        error = 'Identifiants incorrects.'
    return render(request, 'accounts/connexion.html', {'error': error, 'next': next_url})

def deconnexion(request):
    logout(request)
    messages.info(request, 'Vous etes deconnecte.')
    return redirect('core:accueil')

def profil(request):
    if not request.user.is_authenticated:
        return redirect('accounts:connexion')
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.save()
        p = user.profil
        p.telephone = request.POST.get('telephone', p.telephone)
        p.localite  = request.POST.get('localite', p.localite)
        p.adresse   = request.POST.get('adresse', p.adresse)
        if 'photo' in request.FILES:
            p.photo = request.FILES['photo']
        p.save()
        messages.success(request, 'Profil mis a jour !')
        return redirect('accounts:profil')
    return render(request, 'accounts/profil.html')
