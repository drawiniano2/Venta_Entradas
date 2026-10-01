from rest_framework import serializers

from .models import Evento, Recinto, TipoEntrada


class RecintoSerializer(serializers.ModelSerializer):
    """Serializer REST para recintos."""

    class Meta:
        model = Recinto
        fields = [
            "id",
            "nombre",
            "direccion",
            "ciudad",
            "capacidad",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "creado_en",
            "actualizado_en",
        ]


class EventoSerializer(serializers.ModelSerializer):
    """Serializer REST para eventos."""

    recinto_nombre = serializers.CharField(
        source="recinto.nombre",
        read_only=True,
    )

    organizador_username = serializers.CharField(
        source="organizador.username",
        read_only=True,
    )

    class Meta:
        model = Evento
        fields = [
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "fecha_inicio",
            "fecha_fin",
            "recinto",
            "recinto_nombre",
            "organizador",
            "organizador_username",
            "estado",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "organizador",
            "organizador_username",
            "creado_en",
            "actualizado_en",
        ]

    def validate(self, attrs):
        fecha_inicio = attrs.get(
            "fecha_inicio",
            getattr(self.instance, "fecha_inicio", None),
        )

        fecha_fin = attrs.get(
            "fecha_fin",
            getattr(self.instance, "fecha_fin", None),
        )

        if (
            fecha_inicio is not None
            and fecha_fin is not None
            and fecha_fin <= fecha_inicio
        ):
            raise serializers.ValidationError(
                {
                    "fecha_fin": (
                        "La fecha de término debe ser posterior "
                        "a la fecha de inicio."
                    )
                }
            )

        return attrs


class TipoEntradaSerializer(serializers.ModelSerializer):
    """Serializer REST para tipos de entrada."""

    evento_nombre = serializers.CharField(
        source="evento.nombre",
        read_only=True,
    )

    class Meta:
        model = TipoEntrada
        fields = [
            "id",
            "evento",
            "evento_nombre",
            "nombre",
            "descripcion",
            "precio",
            "stock_total",
            "stock_disponible",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "evento_nombre",
            "creado_en",
            "actualizado_en",
        ]

    def validate(self, attrs):
        stock_total = attrs.get(
            "stock_total",
            getattr(self.instance, "stock_total", None),
        )

        stock_disponible = attrs.get(
            "stock_disponible",
            getattr(self.instance, "stock_disponible", None),
        )

        if (
            stock_total is not None
            and stock_disponible is not None
            and stock_disponible > stock_total
        ):
            raise serializers.ValidationError(
                {
                    "stock_disponible": (
                        "El stock disponible no puede superar "
                        "el stock total."
                    )
                }
            )

        return attrs
