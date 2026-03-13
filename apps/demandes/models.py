from django.db import models
from django.contrib.auth.models import User
from apps.techniciens.models import Technicien
from django.utils import timezone

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
    titre   = models.CharField(max_length=255, default='Notification')
    type    = models.CharField(max_length=50, default='info')
    lien    = models.CharField(max_length=500, null=True, blank=True)
    paiement= models.ForeignKey('Paiement', null=True, blank=True,
               on_delete=models.SET_NULL, related_name='notifications')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"




class Paiement(models.Model):

    MODE_CHOICES = [
        ('carte', 'Carte Bancaire'),
        ('livraison', 'À la Livraison'),
        ('mobile', 'Mobile Money'),
    ]

    FOURNISSEUR_CHOICES = [
        ('lumicash', 'Lumicash'),
        ('ecocash', 'Ecocash'),
        (None, 'N/A'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]

    # Relations
    client = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name='Client'
    )
    commande = models.ForeignKey(
        'demandes.Demande',
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name='Demande',
        null=True, blank=True
    )

    # Infos paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        verbose_name='Mode de paiement'
    )
    fournisseur_mobile = models.CharField(
        max_length=20,
        choices=[('lumicash', 'Lumicash'), ('ecocash', 'Ecocash')],
        null=True, blank=True,
        verbose_name='Fournisseur mobile'
    )
    numero_mobile = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name='Numéro mobile'
    )
    # Pour carte bancaire (jamais stocker le CVV !)
    derniers_chiffres_carte = models.CharField(
        max_length=4,
        null=True, blank=True,
        verbose_name='4 derniers chiffres carte'
    )
    nom_titulaire_carte = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name='Nom du titulaire'
    )

    # ── Preuve de paiement (bordereau) ──
    numero_bordereau = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name='Numéro de bordereau'
    )
    photo_recu = models.ImageField(
        upload_to='paiements/recus/',
        null=True, blank=True,
        verbose_name='Photo du reçu'
    )
    date_virement = models.DateField(
        null=True, blank=True,
        verbose_name='Date du virement'
    )
    nom_expediteur = models.CharField(
        max_length=150, null=True, blank=True,
        verbose_name="Nom de l'expéditeur"
    )
    bordereau_soumis = models.BooleanField(
        default=False,
        verbose_name='Bordereau soumis par le client'
    )
    date_soumission_bordereau = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de soumission du bordereau'
    )

    # Montant
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Montant (BIF)'
    )
    devise = models.CharField(max_length=5, default='BIF')

    # Statut & gestion admin
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name='Statut'
    )
    note_admin = models.TextField(
        null=True, blank=True,
        verbose_name='Note de l\'admin'
    )
    valide_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paiements_valides',
        verbose_name='Validé par',
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'paiements'
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement #{self.pk} - {self.client} - {self.montant} {self.devise}"

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save()

    def rejeter(self, user, note=None):
        self.statut = 'rejete'
        self.valide_par = user
        self.date_validation = timezone.now()
        if note:
            self.note_admin = note
        self.save()

    @property
    def statut_badge_color(self):
        colors = {
            'en_attente': 'orange',
            'valide': 'green',
            'rejete': 'red',
            'annule': 'gray',
        }
        return colors.get(self.statut, 'gray')


class InstructionPaiement(models.Model):
    """
    Instructions configurables par l'admin pour chaque mode de paiement.
    Exemple: pour 'livraison', l'admin écrit les étapes à suivre.
    """
    mode_paiement = models.CharField(
        max_length=20,
        choices=Paiement.MODE_CHOICES,
        unique=True,
        verbose_name='Mode de paiement'
    )
    titre = models.CharField(max_length=200, verbose_name='Titre')
    description = models.TextField(verbose_name='Description générale')
    etapes = models.JSONField(
        default=list,
        verbose_name='Étapes (liste)',
        help_text='Liste des étapes sous forme de tableau JSON. Ex: ["Étape 1...", "Étape 2..."]'
    )
    actif = models.BooleanField(default=True, verbose_name='Actif')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instructions_paiement'
        verbose_name = 'Instruction de paiement'
        verbose_name_plural = 'Instructions de paiement'

    def __str__(self):
        return f"Instructions - {self.get_mode_paiement_display()}"