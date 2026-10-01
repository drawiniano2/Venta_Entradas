from rest_framework import serializers

from .models import Compra, DetalleCompra


class DetalleCompraSerializer(serializers.ModelSerializer):
    """
    Representa una línea de una compra.

    El precio_unitario corresponde al precio histórico almacenado
    al momento de crear la compra.
    """

    tipo_entrada_nombre = serializers.CharField(
        source="tipo_entrada.nombre",
        read_only=True,
    )

    evento_nombre = serializers.CharField(
        source="tipo_entrada.evento.nombre",
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = DetalleCompra
        fields = (
            "id",
            "tipo_entrada",
            "tipo_entrada_nombre",
            "evento_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "creado_en",
        )

        read_only_fields = (
            "id",
            "tipo_entrada",
            "tipo_entrada_nombre",
            "evento_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "creado_en",
        )


class CompraSerializer(serializers.ModelSerializer):
    """
    Representa una compra y sus detalles.

    El estado no puede modificarse directamente desde la API.
    Los cambios PENDIENTE -> PAGADO y PAGADO -> CANCELADO
    deben pasar por los servicios transaccionales.
    """

    usuario_username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    detalles = DetalleCompraSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Compra
        fields = (
            "id",
            "usuario",
            "usuario_username",
            "estado",
            "total",
            "creada_en",
            "actualizada_en",
            "pagada_en",
            "cancelada_en",
            "detalles",
        )

        read_only_fields = (
            "id",
            "usuario",
            "usuario_username",
            "estado",
            "total",
            "creada_en",
            "actualizada_en",
            "pagada_en",
            "cancelada_en",
            "detalles",
        )
