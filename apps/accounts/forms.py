from django import forms
from django.contrib.auth.models import User

class InscriptionForm(forms.ModelForm):
    password  = forms.CharField(widget=forms.PasswordInput, min_length=6, label='Mot de passe')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmer le mot de passe')
    telephone = forms.CharField(max_length=20, label='Telephone')
    localite  = forms.CharField(max_length=200, label='Localite')

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email']
        labels = {
            'first_name': 'Prenom',
            'last_name':  'Nom',
            'username':   'Nom utilisateur',
            'email':      'Email',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email obligatoire.')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Cet email est deja utilise.')
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            from apps.accounts.models import Profil
            Profil.objects.create(
                user=user,
                telephone=self.cleaned_data.get('telephone', ''),
                localite=self.cleaned_data.get('localite', ''),
            )
        return user
