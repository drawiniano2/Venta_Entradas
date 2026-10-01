from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializa la información básica de los usuarios del sistema.
    """

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
        )
        read_only_fields = ("id",)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Genera los tokens JWT e incorpora el rol del usuario
    como claim personalizado.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Claims personalizados.
        token["username"] = user.username
        token["rol"] = user.rol

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Información adicional entregada al iniciar sesión.
        data["usuario"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "rol": self.user.rol,
        }

        return data
