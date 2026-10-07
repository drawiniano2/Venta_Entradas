import uuid

from django.db import models

from compras.models import DetalleCompra


class Entrada(models.Model):
    """
    Entrada individual emitida después de confirmar el pago.

    Cada unidad comprada genera una Entrada independiente
    identificada mediante un UUID único.
    """

    class Estado(models.TextChoices):
        VALIDA = "VALIDA", "Válida"
        UTILIZADA = "UTILIZADA", "Utilizada"
        ANULADA = "ANULADA", "Anulada"

    codigo = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    detalle_compra = models.ForeignKey(
        DetalleCompra,
        on_delete=models.PROTECT,
        related_name="entradas",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.VALIDA,
    )

    emitida_en = models.DateTimeField(
        auto_now_add=True,
    )

    utilizada_en = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Permite retirar entradas antiguas de "Mis entradas"
    # sin eliminarlas de la base de datos.
    # Conserva UUID, compra, estado y trazabilidad.
    oculta_usuario = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ("-emitida_en",)
        verbose_name = "entrada"
        verbose_name_plural = "entradas"

    def __str__(self):
        return f"{self.codigo} - {self.estado}"
