from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/',      views.api_register,       name='api-register'),
    path('auth/login/',         views.api_login,          name='api-login'),
    path('auth/logout/',        views.api_logout,         name='api-logout'),
    path('auth/me/',            views.api_me,             name='api-me'),

    # Demandes
    path('demandes/',           views.DemandeListCreate.as_view(), name='api-demandes'),
    path('demandes/<int:pk>/',  views.DemandeDetail.as_view(),     name='api-demande-detail'),

    # Notifications
    path('notifications/',      views.NotificationList.as_view(),  name='api-notifications'),
    path('notifications/count/',views.notif_count,                 name='api-notif-count'),
    path('notifications/read/', views.mark_notifs_read,            name='api-notif-read'),

    # Techniciens
    path('techniciens/',        views.TechnicienList.as_view(),    name='api-techniciens'),
]
