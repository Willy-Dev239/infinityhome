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
]
