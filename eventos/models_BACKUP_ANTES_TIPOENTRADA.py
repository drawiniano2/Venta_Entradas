from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Recinto(models.Model):
    """
    Lugar físico donde se realiza un evento.

    El recinto se mantiene separado de Evento para evitar
    duplicar información como dirección, ciudad y capacidad.
    """

    nombre = models.CharField(
        max_length=150,
        unique=True,
    )

    direccion = models.CharField(
        max_length=200,
    )

    ciudad = models.CharField(
        max_length=100,
    )

    capacidad = models.PositiveIntegerField()

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("nombre",)
        verbose_name = "recinto"
        verbose_name_plural = "recintos"

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"


class Evento(models.Model):
    """
    Evento o concierto publicado en el sistema.

    Cada evento pertenece a un recinto y a un usuario
    organizador.
    """

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PUBLICADO = "PUBLICADO", "Publicado"
        CANCELADO = "CANCELADO", "Cancelado"
        FINALIZADO = "FINALIZADO", "Finalizado"

    nombre = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField()

    fecha_inicio = models.DateTimeField()

    fecha_fin = models.DateTimeField()

    recinto = models.ForeignKey(
        Recinto,
        on_delete=models.PROTECT,
        related_name="eventos",
    )

    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("fecha_inicio",)
        verbose_name = "evento"
        verbose_name_plural = "eventos"

    def clean(self):
        """
        Validaciones de negocio del evento.
        """

        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError(
                    {
                        "fecha_fin": (
                            "La fecha de término debe ser posterior "
                            "a la fecha de inicio."
                        )
                    }
                )

        if self.organizador_id:
            if self.organizador.rol != "ORGANIZADOR":
                raise ValidationError(
                    {
                        "organizador": (
                            "El usuario seleccionado debe tener "
                            "rol ORGANIZADOR."
                        )
                    }
                )

    def __str__(self):
        return f"{self.nombre} - {self.fecha_inicio:%d-%m-%Y}"
