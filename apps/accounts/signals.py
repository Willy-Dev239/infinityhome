# ── apps/accounts/signals.py ──
# Auto-assigne le groupe localité quand un Profil est sauvegardé
 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from apps.accounts.models import Profil
 
 
@receiver(post_save, sender=Profil)
def assigner_groupe_localite(sender, instance, **kwargs):
    localite = instance.localite.strip() if instance.localite else 'Autre'
    group_name = f"Localité : {localite}"
    group, _ = Group.objects.get_or_create(name=group_name)
 
    # Retire des anciens groupes localité
    old_groups = instance.user.groups.filter(name__startswith="Localité : ")
    instance.user.groups.remove(*old_groups)
    # Ajoute au nouveau
    instance.user.groups.add(group)