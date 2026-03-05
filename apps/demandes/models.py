from django.db import models
from django.contrib.auth.models import User
from apps.techniciens.models import Technicien

TYPES_TRAVAUX = [
    ('electricite',  'Electricite'),
    ('plomberie',    'Plomberie'),
    ('construction', 'Construction'),
    ('soudure',      'Soudure'),
    ('peinture',     'Peinture'),
    ('menuiserie',   'Menuiserie'),
    ('surveillance', 'Camera de surveillance'),
    ('autre',        'Autre'),
]

URGENCES = [
    ('normale',  'Normale'),
    ('urgente',  'Urgente'),
    ('critique', 'Critique'),
]

STATUTS = [
    ('en_attente', 'En attente'),
    ('assignee',   'Assignee'),
    ('en_cours',   'En cours'),
    ('terminee',   'Terminee'),
    ('annulee',    'Annulee'),
]

class Demande(models.Model):
    client       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes')
    type_travaux = models.CharField(max_length=30, choices=TYPES_TRAVAUX)
    titre        = models.CharField(max_length=200)
    description  = models.TextField()
    localite     = models.CharField(max_length=200)
    adresse      = models.TextField()
    urgence      = models.CharField(max_length=20, choices=URGENCES, default='normale')
    statut       = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    technicien   = models.ForeignKey(Technicien, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes')
    photo        = models.ImageField(upload_to='demandes/', blank=True, null=True)
    notes_admin  = models.TextField(blank=True)
    date_creation    = models.DateTimeField(auto_now_add=True)
    date_modification= models.DateTimeField(auto_now=True)
    date_intervention= models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"#{self.id} - {self.titre} ({self.client.username})"

    STATUTS = STATUTS

class Notification(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    demande     = models.ForeignKey(Demande, on_delete=models.CASCADE, null=True, blank=True)
    titre       = models.CharField(max_length=200)
    message     = models.TextField()
    lue         = models.BooleanField(default=False)
    date        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"
