from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('',              views.accueil,      name='accueil'),
    path('services/',     views.services,     name='services'),
    path('a-propos/',     views.a_propos,     name='a_propos'),
    path('contact/',      views.contact,      name='contact'),
    path('surveillance/', views.surveillance, name='surveillance'),
]
