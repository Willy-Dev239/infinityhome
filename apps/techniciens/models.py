from django.db import models

SPECIALITES = [
    ('electricien',  'Electricien'),
    ('plombier',     'Plombier'),
    ('ingenieur',    'Ingenieur en construction'),
    ('soudeur',      'Soudeur'),
    ('peintre',      'Peintre'),
    ('menuisier',    'Menuisier'),
    ('surveillance', 'Camera de surveillance'),
]

DISPONIBILITE = [
    ('disponible', 'Disponible'),
    ('occupe',     'Occupe'),
    ('conge',      'En conge'),
]

class Technicien(models.Model):
    nom          = models.CharField(max_length=100)
    prenom       = models.CharField(max_length=100)
    specialite   = models.CharField(max_length=30, choices=SPECIALITES)
    telephone    = models.CharField(max_length=20)
    email        = models.EmailField(blank=True)
    localite     = models.CharField(max_length=200)
    disponibilite= models.CharField(max_length=20, choices=DISPONIBILITE, default='disponible')
    photo        = models.ImageField(upload_to='techniciens/', blank=True, null=True)
    experience   = models.IntegerField(default=0)
    actif        = models.BooleanField(default=True)
    date_ajout   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['specialite', 'nom']

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.get_specialite_display()}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
