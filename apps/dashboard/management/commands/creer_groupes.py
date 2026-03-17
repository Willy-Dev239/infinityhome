# ── apps/dashboard/management/commands/creer_groupes.py ──
# Crée la structure de dossiers :
#   apps/dashboard/management/__init__.py
#   apps/dashboard/management/commands/__init__.py
#   apps/dashboard/management/commands/creer_groupes.py
#
# Puis lance : python manage.py creer_groupes

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.accounts.models import Profil
from apps.techniciens.models import Technicien, SPECIALITES


LOCALITES = [
    'Bujumbura', 'Gitega', 'Ngozi', 'Rumonge', 'Bururi',
    'Kayanza', 'Muyinga', 'Kirundo', 'Makamba', 'Muramvya',
    'Bubanza', 'Cibitoke', 'Cankuzo', 'Ruyigi', 'Rutana',
    'Autre',
]


class Command(BaseCommand):
    help = 'Crée les groupes Django par localité (clients) et par spécialité (techniciens)'

    def handle(self, *args, **kwargs):
        created = 0
        updated_clients = 0
        updated_tech = 0

        # ─── 1. Groupes par localité ───
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Groupes localités ──'))
        for loc in LOCALITES:
            group_name = f"Localité : {loc}"
            group, was_created = Group.objects.get_or_create(name=group_name)
            if was_created:
                created += 1
                self.stdout.write(f"  ✔ Créé  : {group_name}")
            else:
                self.stdout.write(f"  · Existe : {group_name}")

        # ─── 2. Groupes par spécialité ───
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Groupes spécialités ──'))
        for code, label in SPECIALITES:
            group_name = f"Spécialité : {label}"
            group, was_created = Group.objects.get_or_create(name=group_name)
            if was_created:
                created += 1
                self.stdout.write(f"  ✔ Créé  : {group_name}")
            else:
                self.stdout.write(f"  · Existe : {group_name}")

        # ─── 3. Assigner les clients à leur groupe localité ───
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Assignation clients → localité ──'))
        for profil in Profil.objects.select_related('user').all():
            localite = profil.localite.strip() if profil.localite else 'Autre'
            # Cherche le groupe le plus proche
            group_name = f"Localité : {localite}"
            group = Group.objects.filter(name=group_name).first()
            if not group:
                group_name = "Localité : Autre"
                group = Group.objects.get_or_create(name=group_name)[0]

            # Retire des anciens groupes localité, ajoute au nouveau
            old_loc_groups = profil.user.groups.filter(name__startswith="Localité : ")
            profil.user.groups.remove(*old_loc_groups)
            profil.user.groups.add(group)
            updated_clients += 1
            self.stdout.write(f"  {profil.user.username} → {group_name}")

        # ─── 4. Assigner les techniciens à leur groupe spécialité ───
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Assignation techniciens → spécialité ──'))
        for tech in Technicien.objects.all():
            # Trouve le label de la spécialité
            label = dict(SPECIALITES).get(tech.specialite, tech.specialite)
            group_name = f"Spécialité : {label}"
            group = Group.objects.filter(name=group_name).first()
            if not group:
                group, _ = Group.objects.get_or_create(name=group_name)

            # Si le technicien a un user Django associé
            if hasattr(tech, 'user') and tech.user:
                old_spec_groups = tech.user.groups.filter(name__startswith="Spécialité : ")
                tech.user.groups.remove(*old_spec_groups)
                tech.user.groups.add(group)
                updated_tech += 1
                self.stdout.write(f"  {tech.nom_complet} → {group_name}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ {tech.nom_complet} : pas de compte User associé")
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n✔ Terminé — {created} groupes créés, '
            f'{updated_clients} clients assignés, '
            f'{updated_tech} techniciens assignés.'
        ))