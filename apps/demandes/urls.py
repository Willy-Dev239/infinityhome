from django.urls import path
from . import views

app_name = 'demandes'

urlpatterns = [
    path('nouvelle/',         views.nouvelle_demande, name='nouvelle_demande'),
    path('mes-demandes/',     views.mes_demandes,     name='mes_demandes'),
    path('<int:pk>/',         views.detail_demande,   name='detail_demande'),
    path('notifications/',    views.notifications,    name='notifications'),
    path('api/notif-count/',  views.notif_count,      name='notif_count'),
]
    