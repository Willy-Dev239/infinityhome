from django.db import models
from django.contrib.auth.models import User

class Profil(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    telephone = models.CharField(max_length=20, blank=True)
    localite  = models.CharField(max_length=200, blank=True)
    adresse   = models.TextField(blank=True)
    photo     = models.ImageField(upload_to='profils/', blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"
