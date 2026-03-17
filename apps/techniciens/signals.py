# ── apps/techniciens/signals.py ──
# Auto-assigne le groupe spécialité quand un Technicien est sauvegardé
# (uniquement si le technicien a un User Django associé)
 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from apps.techniciens.models import Technicien, SPECIALITES
 
 
@receiver(post_save, sender=Technicien)
def assigner_groupe_specialite(sender, instance, **kwargs):
    if not (hasattr(instance, 'user') and instance.user):
        return
    label = dict(SPECIALITES).get(instance.specialite, instance.specialite)
    group_name = f"Spécialité : {label}"
    group, _ = Group.objects.get_or_create(name=group_name)
 
    old_groups = instance.user.groups.filter(name__startswith="Spécialité : ")
    instance.user.groups.remove(*old_groups)
    instance.user.groups.add(group)