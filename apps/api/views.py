from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.demandes.models import Demande, Notification
from apps.techniciens.models import Technicien
from apps.accounts.models import Profil
from .serializers import (
    DemandeSerializer, DemandeCreateSerializer,
    NotificationSerializer, TechnicienSerializer,
    RegisterSerializer, UserSerializer
)

# ══ AUTH ══════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Inscription — crée un compte et retourne le token"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Compte cree avec succes !'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Connexion — retourne le token"""
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })
    return Response({'error': 'Identifiants incorrects.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def api_logout(request):
    """Deconnexion — supprime le token"""
    try:
        request.user.auth_token.delete()
    except:
        pass
    return Response({'message': 'Deconnecte avec succes.'})

@api_view(['GET'])
def api_me(request):
    """Profil de l utilisateur connecte"""
    return Response(UserSerializer(request.user).data)

# ══ DEMANDES ══════════════════════════════════════════════

class DemandeListCreate(generics.ListCreateAPIView):
    """GET: mes demandes | POST: creer une demande"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemandeCreateSerializer
        return DemandeSerializer

    def get_queryset(self):
        return Demande.objects.filter(client=self.request.user).order_by('id')

    def perform_create(self, serializer):
        demande = serializer.save(client=self.request.user)
        Notification.objects.create(
            utilisateur=self.request.user,
            demande=demande,
            titre='Demande soumise',
            message=f'Votre demande "{demande.titre}" a ete soumise avec succes.',
        )

class DemandeDetail(generics.RetrieveAPIView):
    """GET: detail d une demande"""
    serializer_class   = DemandeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Demande.objects.filter(client=self.request.user)

# ══ NOTIFICATIONS ══════════════════════════════════════════

class NotificationList(generics.ListAPIView):
    """GET: mes notifications"""
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(utilisateur=self.request.user)

@api_view(['GET'])
def notif_count(request):
    """GET: nombre de notifications non lues"""
    count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    return Response({'count': count})

@api_view(['POST'])
def mark_notifs_read(request):
    """POST: marquer toutes les notifications comme lues"""
    Notification.objects.filter(utilisateur=request.user, lue=False).update(lue=True)
    return Response({'message': 'Notifications marquees comme lues.'})

# ══ TECHNICIENS ════════════════════════════════════════════

class TechnicienList(generics.ListAPIView):
    """GET: liste des techniciens (filtrable par ?specialite=electricien)"""
    serializer_class   = TechnicienSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Technicien.objects.filter(actif=True)
        specialite = self.request.query_params.get('specialite')
        disponible = self.request.query_params.get('disponible')
        if specialite:
            qs = qs.filter(specialite=specialite)
        if disponible:
            qs = qs.filter(disponibilite='disponible')
        return qs
