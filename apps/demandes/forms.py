# demandes/forms.py

from django import forms
from .models import Demande

class DemandeForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ['type_travaux', 'urgence', 'titre', 'description', 'localite', 'adresse', 'photo']
        widgets = {
            'type_travaux': forms.Select(attrs={'class': 'form-control'}),
            'urgence': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Ex: Fuite d eau dans la cuisine'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Décrivez le problème en détail...'}),
            'localite': forms.TextInput(attrs={'placeholder': 'Ex: Bujumbura, Rohero'}),
            'adresse': forms.TextInput(attrs={'placeholder': 'Ex: Avenue Muyinga, N°12'}),
            'photo': forms.ClearableFileInput(),
        }