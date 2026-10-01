from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Evento, Recinto, TipoEntrada
from .serializers import (
    EventoSerializer,
    RecintoSerializer,
    TipoEntradaSerializer,
)


class EsOrganizadorOAdministrador(permissions.BasePermission):
    """
    Lectura para usuarios autenticados.
    Escritura para ORGANIZADOR o administrador.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_staff
            or getattr(request.user, "rol", None) == "ORGANIZADOR"
        )


class RecintoViewSet(viewsets.ModelViewSet):
    """CRUD REST de recintos."""

    serializer_class = RecintoSerializer
    permission_classes = (EsOrganizadorOAdministrador,)
    queryset = Recinto.objects.all().order_by("nombre")

    # Filtros declarativos mediante django-filter.
    filterset_fields = {
        "ciudad": ["exact", "icontains"],
        "activo": ["exact"],
    }


class EventoViewSet(viewsets.ModelViewSet):
    """CRUD REST de eventos."""

    serializer_class = EventoSerializer
    permission_classes = (EsOrganizadorOAdministrador,)

    # Permite filtrar eventos desde la API y Swagger.
    filterset_fields = {
        "estado": ["exact"],
        "activo": ["exact"],
        "recinto": ["exact"],
    }

    def get_queryset(self):
        queryset = (
            Evento.objects
            .select_related("recinto", "organizador")
            .prefetch_related("tipos_entrada")
            .all()
        )

        user = self.request.user

        if user.is_staff:
            return queryset

        if getattr(user, "rol", None) == "ORGANIZADOR":
            return queryset.filter(organizador=user)

        return queryset.filter(
            estado=Evento.Estado.PUBLICADO,
            activo=True,
        )

    def perform_create(self, serializer):
        user = self.request.user

        if getattr(user, "rol", None) != "ORGANIZADOR":
            raise PermissionDenied(
                "Para crear eventos debes utilizar "
                "una cuenta ORGANIZADOR."
            )

        serializer.save(organizador=user)


class TipoEntradaViewSet(viewsets.ModelViewSet):
    """CRUD REST de tipos de entrada."""

    serializer_class = TipoEntradaSerializer
    permission_classes = (EsOrganizadorOAdministrador,)

    # Permite filtrar tipos de entrada mediante django-filter.
    filterset_fields = {
        "evento": ["exact"],
        "activo": ["exact"],
        "precio": ["exact", "gte", "lte"],
    }

    def get_queryset(self):
        queryset = (
            TipoEntrada.objects
            .select_related(
                "evento",
                "evento__organizador",
            )
            .all()
        )

        user = self.request.user

        if user.is_staff:
            return queryset

        if getattr(user, "rol", None) == "ORGANIZADOR":
            return queryset.filter(
                evento__organizador=user
            )

        return queryset.filter(
            evento__estado=Evento.Estado.PUBLICADO,
            evento__activo=True,
            activo=True,
        )

    def perform_create(self, serializer):
        evento = serializer.validated_data["evento"]
        user = self.request.user

        if (
            not user.is_staff
            and evento.organizador_id != user.id
        ):
            raise PermissionDenied(
                "No puedes crear entradas para "
                "eventos de otro organizador."
            )

        serializer.save()

    def perform_update(self, serializer):
        evento = serializer.validated_data.get(
            "evento",
            serializer.instance.evento,
        )

        user = self.request.user

        if (
            not user.is_staff
            and evento.organizador_id != user.id
        ):
            raise PermissionDenied(
                "No puedes modificar entradas de "
                "otro organizador."
            )

        serializer.save()



