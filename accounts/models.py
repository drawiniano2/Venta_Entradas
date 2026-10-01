from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario personalizado del sistema de venta de entradas.

    Hereda los campos estándar de Django y agrega el rol
    utilizado para controlar los permisos de la API.
    """

    class Rol(models.TextChoices):
        ESPECTADOR = "ESPECTADOR", "Espectador"
        ORGANIZADOR = "ORGANIZADOR", "Organizador"

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ESPECTADOR,
    )

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
