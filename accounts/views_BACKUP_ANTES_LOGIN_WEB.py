from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de autenticación.

    Valida las credenciales del usuario y devuelve:
    - access token
    - refresh token
    - información básica del usuario

    El token incluye el rol ESPECTADOR u ORGANIZADOR
    como claim personalizado.
    """

    serializer_class = CustomTokenObtainPairSerializer
