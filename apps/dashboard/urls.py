from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                        views.home,              name='home'),
    path('login/',                  views.admin_login,       name='login'),
    path('logout/',                 views.admin_logout,      name='logout'),
    path('demandes/',               views.demandes,          name='demandes'),
    path('demandes/<int:pk>/',      views.demande_detail,    name='demande_detail'),
    path('demandes/<int:pk>/assigner/', views.assigner_technicien, name='assigner'),
    path('demandes/<int:pk>/statut/',   views.update_statut,      name='update_statut'),
    path('techniciens/',            views.techniciens,       name='techniciens'),
    path('techniciens/ajouter/',    views.technicien_add,    name='technicien_add'),
    path('techniciens/<int:pk>/modifier/', views.technicien_edit, name='technicien_edit'),
    path('clients/',                views.clients,           name='clients'),
    
    path('paiements/',                          views.paiements_list,          name='paiements'),
path('paiements/<int:pk>/',                 views.paiement_detail,         name='paiement_detail'),
path('paiements/<int:pk>/valider/',         views.paiement_valider,        name='paiement_valider'),
path('paiements/<int:pk>/rejeter/',         views.paiement_rejeter,        name='paiement_rejeter'),
path('paiements/instructions/',             views.instructions_paiement,   name='instructions_paiement'),
path('paiements/instructions/<str:mode>/',  views.instructions_sauvegarder, name='instructions_sauvegarder'),
 path('paiements/<int:pk>/modifier/',        views.paiement_modifier,      name='paiement_modifier'),
 path('paiements/<int:pk>/notifier/',        views.paiement_notifier,      name='paiement_notifier'),
    path('paiements/<int:pk>/supprimer/',       views.paiement_supprimer,     name='paiement_supprimer'),
path('clients/<int:client_pk>/voir/', views.client_view_readonly, name='client_view_readonly'),

path('statistiques/', views.statistiques, name='statistiques'),
]
