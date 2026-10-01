from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from eventos.models import TipoEntrada


class Compra(models.Model):
    """
    Compra realizada por un usuario.

    La compra comienza como PENDIENTE.
    El stock se descontará únicamente cuando la compra
    pase correctamente al estado PAGADO.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        CANCELADO = "CANCELADO", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="compras",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    creada_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizada_en = models.DateTimeField(
        auto_now=True,
    )

    pagada_en = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelada_en = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-creada_en",)
        verbose_name = "compra"
        verbose_name_plural = "compras"

    def calcular_total(self):
        """
        Calcula el total real de la compra a partir de sus detalles.

        No confía en un total recibido desde el cliente.
        Utiliza el precio_unitario histórico almacenado
        en cada DetalleCompra.
        """

        return sum(
            (
                detalle.subtotal
                for detalle in self.detalles.all()
            ),
            0,
        )

    def __str__(self):
        return (
            f"Compra #{self.pk} - "
            f"{self.usuario.username} - "
            f"{self.estado}"
        )


class DetalleCompra(models.Model):
    """
    Línea individual de una compra.

    precio_unitario guarda el precio histórico pagado.
    De esta manera una modificación posterior en TipoEntrada
    no altera compras realizadas anteriormente.
    """

    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    tipo_entrada = models.ForeignKey(
        TipoEntrada,
        on_delete=models.PROTECT,
        related_name="detalles_compra",
    )

    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "detalle de compra"
        verbose_name_plural = "detalles de compra"
        constraints = [
            models.UniqueConstraint(
                fields=("compra", "tipo_entrada"),
                name="detalle_unico_tipo_entrada_por_compra",
            ),
        ]

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return (
            f"Compra #{self.compra_id} - "
            f"{self.tipo_entrada.nombre} x {self.cantidad}"
        )

