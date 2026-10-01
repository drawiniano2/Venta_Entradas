from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Compra
from .serializers import CompraSerializer
from .services import cancelar_compra, pagar_compra


class CompraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API de compras del usuario autenticado.

    Operaciones disponibles:
    - GET /api/compras/
    - GET /api/compras/{id}/
    - POST /api/compras/{id}/pagar/
    - POST /api/compras/{id}/cancelar/

    El usuario solamente puede consultar y operar
    sobre sus propias compras.
    """

    serializer_class = CompraSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Limita las compras al usuario autenticado.

        select_related y prefetch_related reducen consultas
        adicionales al serializar los detalles.
        """

        return (
            Compra.objects
            .filter(usuario=self.request.user)
            .select_related("usuario")
            .prefetch_related(
                "detalles__tipo_entrada__evento"
            )
        )

    @action(
        detail=True,
        methods=("post",),
        url_path="pagar",
    )
    def pagar(self, request, pk=None):
        """
        Confirma el pago mediante el servicio transaccional.
        """

        compra = self.get_object()

        try:
            compra = pagar_compra(compra.pk)
        except DjangoValidationError as error:
            raise ValidationError(
                {"detail": error.messages}
            ) from error

        serializer = self.get_serializer(compra)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=("post",),
        url_path="cancelar",
    )
    def cancelar(self, request, pk=None):
        """
        Cancela una compra pagada mediante el servicio
        transaccional y repone el stock correspondiente.
        """

        compra = self.get_object()

        try:
            compra = cancelar_compra(compra.pk)
        except DjangoValidationError as error:
            raise ValidationError(
                {"detail": error.messages}
            ) from error

        serializer = self.get_serializer(compra)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
