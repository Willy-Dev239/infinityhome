from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Paiement, InstructionPaiement


# ─────────────────────────────────────────────
#  INLINE pour voir les paiements d'un client
# ─────────────────────────────────────────────
class PaiementInlineAdmin(admin.TabularInline):
    model = Paiement
    extra = 0
    readonly_fields = ('mode_paiement', 'montant', 'devise', 'statut_colore', 'created_at')
    fields = ('mode_paiement', 'montant', 'devise', 'statut_colore', 'created_at')
    can_delete = False

    def statut_colore(self, obj):
        colors = {
            'en_attente': '#F59E0B',
            'valide': '#10B981',
            'rejete': '#EF4444',
            'annule': '#6B7280',
        }
        labels = dict(Paiement.STATUT_CHOICES)
        color = colors.get(obj.statut, '#6B7280')
        label = labels.get(obj.statut, obj.statut)
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600">{}</span>',
            color, label
        )
    statut_colore.short_description = 'Statut'


# ─────────────────────────────────────────────
#  ADMIN PRINCIPAL PAIEMENT
# ─────────────────────────────────────────────
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client_link', 'mode_badge', 'montant_affiche',
        'statut_badge', 'fournisseur_mobile', 'created_at', 'actions_rapides'
    )
    list_filter = ('statut', 'mode_paiement', 'fournisseur_mobile', 'devise', 'created_at')
    search_fields = ('client__nom', 'client__prenom', 'client__email', 'numero_mobile', 'id')
    readonly_fields = (
        'created_at', 'updated_at', 'valide_par', 'date_validation',
        'instructions_mode', 'statut_badge'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('👤 Client & Commande', {
            'fields': ('client', 'commande')
        }),
        ('💳 Détails du paiement', {
            'fields': (
                'mode_paiement', 'montant', 'devise',
                'fournisseur_mobile', 'numero_mobile',
                'derniers_chiffres_carte', 'nom_titulaire_carte',
            )
        }),
        ('📋 Instructions pour ce mode', {
            'fields': ('instructions_mode',),
            'classes': ('collapse',),
        }),
        ('✅ Statut & Validation', {
            'fields': ('statut', 'statut_badge', 'note_admin', 'valide_par', 'date_validation')
        }),
        ('🕒 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['valider_paiements', 'rejeter_paiements', 'mettre_en_attente']

    # ── Colonnes personnalisées ──

    def client_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.client.pk])
        return format_html('<a href="{}">{}</a>', url, obj.client.get_full_name() or obj.client.username)
    client_link.short_description = 'Client'

    def mode_badge(self, obj):
        styles = {
            'carte':    ('💳', '#3B82F6', '#EFF6FF'),
            'livraison':('🏠', '#8B5CF6', '#F5F3FF'),
            'mobile':   ('📱', '#10B981', '#ECFDF5'),
        }
        icon, color, bg = styles.get(obj.mode_paiement, ('?', '#6B7280', '#F3F4F6'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600">{} {}</span>',
            bg, color, icon, obj.get_mode_paiement_display()
        )
    mode_badge.short_description = 'Mode'

    def montant_affiche(self, obj):
        return format_html(
            '<strong style="color:#1a1a2e">{:,.0f} {}</strong>',
            obj.montant, obj.devise
        )
    montant_affiche.short_description = 'Montant'

    def statut_badge(self, obj):
        colors = {
            'en_attente': ('#F59E0B', '#FFFBEB'),
            'valide':     ('#10B981', '#ECFDF5'),
            'rejete':     ('#EF4444', '#FEF2F2'),
            'annule':     ('#6B7280', '#F3F4F6'),
        }
        color, bg = colors.get(obj.statut, ('#6B7280', '#F3F4F6'))
        label = dict(Paiement.STATUT_CHOICES).get(obj.statut, obj.statut)
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">{}</span>',
            bg, color, label
        )
    statut_badge.short_description = 'Statut'

    def actions_rapides(self, obj):
        if obj.statut == 'en_attente':
            valider_url = reverse('admin:paiements_valider', args=[obj.pk])
            rejeter_url = reverse('admin:paiements_rejeter', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background:#10B981;color:white;padding:3px 10px;border-radius:5px;margin-right:4px;text-decoration:none;font-size:11px">✓ Valider</a>'
                '<a href="{}" style="background:#EF4444;color:white;padding:3px 10px;border-radius:5px;text-decoration:none;font-size:11px">✗ Rejeter</a>',
                valider_url, rejeter_url
            )
        return format_html(
            '<span style="color:#6B7280;font-size:12px">—</span>'
        )
    actions_rapides.short_description = 'Actions'

    def instructions_mode(self, obj):
        """Affiche les instructions configurées pour ce mode de paiement."""
        try:
            instruction = InstructionPaiement.objects.get(mode_paiement=obj.mode_paiement)
            etapes_html = ''.join([
                f'<li style="margin:6px 0;padding:6px 12px;background:#f8fafc;border-left:3px solid #3B82F6;border-radius:3px">{e}</li>'
                for e in instruction.etapes
            ])
            return format_html(
                '<div style="background:#f0f9ff;padding:16px;border-radius:8px;border:1px solid #bae6fd">'
                '<strong style="color:#0369a1">{}</strong><br>'
                '<p style="color:#374151;margin:8px 0">{}</p>'
                '<ol style="margin:0;padding-left:20px">{}</ol>'
                '</div>',
                instruction.titre, instruction.description,
                format_html(''.join([
                    f'<li style="margin:6px 0;padding:6px 12px;background:#f8fafc;border-left:3px solid #3B82F6;border-radius:3px">{e}</li>'
                    for e in instruction.etapes
                ]))
            )
        except InstructionPaiement.DoesNotExist:
            return format_html(
                '<span style="color:#9CA3AF">Aucune instruction configurée pour ce mode. '
                '<a href="{}">Configurer maintenant →</a></span>',
                reverse('admin:paiements_instructionpaiement_add')
            )
    instructions_mode.short_description = 'Instructions (mode actuel)'

    # ── Actions groupées ──

    @admin.action(description='✅ Valider les paiements sélectionnés')
    def valider_paiements(self, request, queryset):
        count = 0
        for p in queryset.filter(statut='en_attente'):
            p.valider(request.user)
            count += 1
        self.message_user(request, f'{count} paiement(s) validé(s) avec succès.')

    @admin.action(description='❌ Rejeter les paiements sélectionnés')
    def rejeter_paiements(self, request, queryset):
        count = 0
        for p in queryset.filter(statut='en_attente'):
            p.rejeter(request.user)
            count += 1
        self.message_user(request, f'{count} paiement(s) rejeté(s).')

    @admin.action(description='⏳ Remettre en attente')
    def mettre_en_attente(self, request, queryset):
        queryset.update(statut='en_attente')
        self.message_user(request, 'Paiements remis en attente.')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('<int:pk>/valider/', self.admin_site.admin_view(self.valider_view), name='paiements_valider'),
            path('<int:pk>/rejeter/', self.admin_site.admin_view(self.rejeter_view), name='paiements_rejeter'),
        ]
        return custom + urls

    def valider_view(self, request, pk):
        paiement = Paiement.objects.get(pk=pk)
        paiement.valider(request.user)
        self.message_user(request, f'Paiement #{pk} validé avec succès.')
        return HttpResponseRedirect(reverse('admin:paiements_paiement_changelist'))

    def rejeter_view(self, request, pk):
        paiement = Paiement.objects.get(pk=pk)
        paiement.rejeter(request.user)
        self.message_user(request, f'Paiement #{pk} rejeté.')
        return HttpResponseRedirect(reverse('admin:paiements_paiement_changelist'))


# ─────────────────────────────────────────────
#  ADMIN INSTRUCTIONS DE PAIEMENT
# ─────────────────────────────────────────────
@admin.register(InstructionPaiement)
class InstructionPaiementAdmin(admin.ModelAdmin):
    list_display = ('mode_paiement_badge', 'titre', 'nb_etapes', 'actif', 'updated_at')
    list_editable = ('actif',)
    readonly_fields = ('updated_at', 'apercu_etapes')

    fieldsets = (
        ('Mode de paiement', {
            'fields': ('mode_paiement', 'actif')
        }),
        ('Contenu', {
            'fields': ('titre', 'description', 'etapes'),
            'description': (
                'Le champ "Étapes" doit être un tableau JSON. Exemple :<br>'
                '<code>["Rendez-vous au siège InfinityHome (Avenue X, Bujumbura)", '
                '"Présentez votre numéro de commande", '
                '"Effectuez le paiement en espèces à la caisse"]</code>'
            )
        }),
        ('Aperçu', {
            'fields': ('apercu_etapes',),
            'classes': ('collapse',),
        }),
        ('Date de modification', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    def mode_paiement_badge(self, obj):
        styles = {
            'carte':    ('💳', '#3B82F6', '#EFF6FF'),
            'livraison':('🏠', '#8B5CF6', '#F5F3FF'),
            'mobile':   ('📱', '#10B981', '#ECFDF5'),
        }
        icon, color, bg = styles.get(obj.mode_paiement, ('?', '#6B7280', '#F3F4F6'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600">{} {}</span>',
            bg, color, icon, obj.get_mode_paiement_display()
        )
    mode_paiement_badge.short_description = 'Mode'

    def nb_etapes(self, obj):
        n = len(obj.etapes)
        return format_html('<strong>{}</strong> étape(s)', n)
    nb_etapes.short_description = 'Étapes'

    def apercu_etapes(self, obj):
        if not obj.etapes:
            return 'Aucune étape définie.'
        items = ''.join([
            f'<li style="margin:8px 0;padding:8px 14px;background:#f8fafc;border-left:3px solid #3B82F6;border-radius:3px">'
            f'<strong>Étape {i+1} :</strong> {e}</li>'
            for i, e in enumerate(obj.etapes)
        ])
        return format_html(
            '<div style="background:#f0f9ff;padding:16px;border-radius:8px;border:1px solid #bae6fd">'
            '<strong style="color:#0369a1">📋 {}</strong>'
            '<ol style="margin-top:10px;padding-left:20px">{}</ol></div>',
            obj.titre, format_html(items)
        )
    apercu_etapes.short_description = 'Aperçu'