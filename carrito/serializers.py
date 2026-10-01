from rest_framework import serializers

from eventos.models import TipoEntrada

from .models import Carrito, ItemCarrito


class ItemCarritoSerializer(serializers.ModelSerializer):
    """
    Representa un tipo de entrada agregado al carrito.

    La cantidad puede modificarse mientras no supere
    el stock actualmente disponible.

    IMPORTANTE:
    agregar o modificar un item NO descuenta stock.
    """

    tipo_entrada_nombre = serializers.CharField(
        source="tipo_entrada.nombre",
        read_only=True,
    )

    evento_nombre = serializers.CharField(
        source="tipo_entrada.evento.nombre",
        read_only=True,
    )

    precio_unitario = serializers.DecimalField(
        source="tipo_entrada.precio",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = ItemCarrito
        fields = (
            "id",
            "tipo_entrada",
            "tipo_entrada_nombre",
            "evento_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "agregado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "id",
            "tipo_entrada_nombre",
            "evento_nombre",
            "precio_unitario",
            "subtotal",
            "agregado_en",
            "actualizado_en",
        )

    def validate_cantidad(self, value):
        """
        Impide cantidades menores a 1.
        """

        if value < 1:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor que cero."
            )

        return value

    def validate(self, attrs):
        """
        Comprueba el stock disponible sin descontarlo.
        """

        tipo_entrada = attrs.get("tipo_entrada")

        if tipo_entrada is None and self.instance is not None:
            tipo_entrada = self.instance.tipo_entrada

        cantidad = attrs.get("cantidad")

        if cantidad is None and self.instance is not None:
            cantidad = self.instance.cantidad

        if tipo_entrada is not None and cantidad is not None:
            if cantidad > tipo_entrada.stock_disponible:
                raise serializers.ValidationError(
                    {
                        "cantidad": (
                            "La cantidad solicitada supera "
                            "el stock disponible."
                        )
                    }
                )

        return attrs


class CarritoSerializer(serializers.ModelSerializer):
    """
    Representa el carrito persistente del usuario
    junto con todos sus items.
    """

    usuario_username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    items = ItemCarritoSerializer(
        many=True,
        read_only=True,
    )

    total = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = (
            "id",
            "usuario",
            "usuario_username",
            "items",
            "total",
            "creado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "id",
            "usuario",
            "usuario_username",
            "items",
            "total",
            "creado_en",
            "actualizado_en",
        )

    def get_total(self, obj):
        """
        Calcula el total actual del carrito desde sus items.
        """

        return sum(
            (
                item.subtotal
                for item in obj.items.all()
            ),
            0,
        )
