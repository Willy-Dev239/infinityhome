from django.urls import path
from . import views

app_name = 'demandes'

urlpatterns = [
    path('nouvelle/',         views.nouvelle_demande, name='nouvelle_demande'),
    path('mes-demandes/',     views.mes_demandes,     name='mes_demandes'),
    path('<int:pk>/',         views.detail_demande,   name='detail_demande'),
    path('notifications/',    views.notifications,    name='notifications'),
    path('api/notif-count/',  views.notif_count,      name='notif_count'),
    
    path('api/paiements/bordereau/', views.soumettre_bordereau, name='soumettre_bordereau'),
    
       # ── Paiements ──
    path('api/paiements/creer/',                    views.creer_paiement,          name='creer_paiement'),
    path('api/paiements/<int:paiement_id>/statut/', views.statut_paiement,         name='statut_paiement'),
    path('api/paiements/instructions/',             views.get_toutes_instructions, name='toutes_instructions'), 
    path('api/paiements/instructions/<str:mode>/', views.get_instructions,         name='instructions_mode'),
    
]

    