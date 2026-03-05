from rest_framework import serializers
from django.contrib.auth.models import User
from apps.demandes.models import Demande, Notification
from apps.techniciens.models import Technicien
from apps.accounts.models import Profil

class ProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Profil
        fields = ['telephone', 'localite', 'adresse']

class UserSerializer(serializers.ModelSerializer):
    profil = ProfilSerializer(read_only=True)
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profil']

class TechnicienSerializer(serializers.ModelSerializer):
    specialite_display   = serializers.CharField(source='get_specialite_display', read_only=True)
    disponibilite_display= serializers.CharField(source='get_disponibilite_display', read_only=True)
    class Meta:
        model  = Technicien
        fields = ['id', 'nom', 'prenom', 'nom_complet', 'specialite', 'specialite_display',
                  'telephone', 'email', 'localite', 'disponibilite', 'disponibilite_display',
                  'experience', 'photo']

class DemandeSerializer(serializers.ModelSerializer):
    technicien    = TechnicienSerializer(read_only=True)
    statut_display= serializers.CharField(source='get_statut_display', read_only=True)
    type_display  = serializers.CharField(source='get_type_travaux_display', read_only=True)
    urgence_display= serializers.CharField(source='get_urgence_display', read_only=True)
    client_nom    = serializers.CharField(source='client.get_full_name', read_only=True)

    class Meta:
        model  = Demande
        fields = ['id', 'titre', 'description', 'type_travaux', 'type_display',
                  'localite', 'adresse', 'urgence', 'urgence_display',
                  'statut', 'statut_display', 'technicien', 'client_nom',
                  'date_creation', 'date_intervention', 'photo']
        read_only_fields = ['statut', 'technicien', 'date_creation']

class DemandeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Demande
        fields = ['type_travaux', 'titre', 'description', 'localite', 'adresse', 'urgence', 'photo']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'titre', 'message', 'lue', 'date']

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)
    telephone = serializers.CharField(max_length=20)
    localite  = serializers.CharField(max_length=200)

    class Meta:
        model  = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'telephone', 'localite']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est deja utilise.'})
        return data

    def create(self, validated_data):
        telephone = validated_data.pop('telephone')
        localite  = validated_data.pop('localite')
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        Profil.objects.create(user=user, telephone=telephone, localite=localite)
        return user



