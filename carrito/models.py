from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from eventos.models import Asiento, TipoEntrada


class Carrito(models.Model):
    """
    Carrito o reserva temporal persistente del usuario.

    La relación OneToOne garantiza que cada usuario tenga
    como máximo un carrito persistente.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrito",
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarrito(models.Model):
    """
    Tipo de entrada y cantidad solicitada dentro del carrito.

    IMPORTANTE:
    crear o modificar este registro NO descuenta stock.
    El descuento se realizará al confirmar una compra PAGADA.
    """

    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="items",
    )

    tipo_entrada = models.ForeignKey(
        TipoEntrada,
        on_delete=models.PROTECT,
        related_name="items_carrito",
    )

    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.PROTECT,
        related_name="items_carrito",
        null=True,
        blank=True,
    )

    cantidad = models.PositiveIntegerField()

    agregado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "ítem de carrito"
        verbose_name_plural = "ítems de carrito"
        constraints = [
            # Para eventos con entrada GENERAL:
            # un tipo de entrada aparece una sola vez por carrito
            # y la cantidad se acumula en ese mismo item.
            models.UniqueConstraint(
                fields=("carrito", "tipo_entrada"),
                condition=models.Q(asiento__isnull=True),
                name="item_general_unico_por_carrito",
            ),

            # Para eventos con UBICACION:
            # un asiento concreto solo puede aparecer una vez
            # dentro del mismo carrito.
            models.UniqueConstraint(
                fields=("carrito", "asiento"),
                condition=models.Q(asiento__isnull=False),
                name="asiento_unico_por_carrito",
            ),
        ]

    def clean(self):
        """
        Valida la cantidad solicitada sin modificar el stock.
        """

        if self.cantidad < 1:
            raise ValidationError(
                {"cantidad": "La cantidad debe ser mayor que cero."}
            )

        if self.tipo_entrada_id:
            if self.cantidad > self.tipo_entrada.stock_disponible:
                raise ValidationError(
                    {
                        "cantidad": (
                            "La cantidad solicitada supera "
                            "el stock disponible."
                        )
                    }
                )

    @property
    def subtotal(self):
        return self.tipo_entrada.precio * self.cantidad

    def __str__(self):
        return (
            f"{self.carrito.usuario.username} - "
            f"{self.tipo_entrada.nombre} x {self.cantidad}"
        )
