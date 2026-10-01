from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from compras.serializers import CompraSerializer

from .models import Carrito, ItemCarrito
from .serializers import CarritoSerializer, ItemCarritoSerializer
from .services import confirmar_carrito


class MiCarritoView(APIView):
    """
    Permite al usuario autenticado consultar su carrito.

    Si todavía no existe un carrito para el usuario,
    se crea automáticamente.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        carrito, _ = Carrito.objects.get_or_create(
            usuario=request.user
        )

        carrito = (
            Carrito.objects
            .select_related("usuario")
            .prefetch_related(
                "items__tipo_entrada__evento"
            )
            .get(pk=carrito.pk)
        )

        serializer = CarritoSerializer(carrito)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class AgregarItemCarritoView(APIView):
    """
    Agrega un tipo de entrada al carrito del usuario.

    Si el tipo de entrada ya existe en el carrito,
    no se crea una segunda fila: se informa el error.

    Agregar al carrito NO descuenta stock.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        carrito, _ = Carrito.objects.get_or_create(
            usuario=request.user
        )

        serializer = ItemCarritoSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        try:
            item = serializer.save(
                carrito=carrito
            )
        except IntegrityError as error:
            raise ValidationError(
                {
                    "detail": (
                        "Este tipo de entrada ya está "
                        "agregado al carrito."
                    )
                }
            ) from error

        serializer_salida = ItemCarritoSerializer(item)

        return Response(
            serializer_salida.data,
            status=status.HTTP_201_CREATED,
        )


class ModificarItemCarritoView(APIView):
    """
    Modifica la cantidad de un item perteneciente
    al carrito del usuario autenticado.

    La modificación NO descuenta stock.
    """

    permission_classes = (IsAuthenticated,)

    def patch(self, request, pk):
        try:
            item = (
                ItemCarrito.objects
                .select_related(
                    "carrito",
                    "tipo_entrada",
                    "tipo_entrada__evento",
                )
                .get(
                    pk=pk,
                    carrito__usuario=request.user,
                )
            )
        except ItemCarrito.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "El item solicitado no existe "
                        "en su carrito."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ItemCarritoSerializer(
            item,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        return Response(
            ItemCarritoSerializer(item).data,
            status=status.HTTP_200_OK,
        )


class EliminarItemCarritoView(APIView):
    """
    Elimina un item del carrito del usuario autenticado.

    Como el carrito no reserva stock físicamente,
    eliminar un item no modifica el stock.
    """

    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk):
        try:
            item = ItemCarrito.objects.get(
                pk=pk,
                carrito__usuario=request.user,
            )
        except ItemCarrito.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "El item solicitado no existe "
                        "en su carrito."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ConfirmarCarritoView(APIView):
    """
    Convierte el carrito del usuario autenticado
    en una Compra PENDIENTE.

    Confirmar el carrito:
    - valida nuevamente el stock;
    - copia el precio histórico;
    - calcula el total en el servidor;
    - vacía los items del carrito;
    - NO descuenta stock;
    - NO genera entradas.

    El descuento y la generación de entradas ocurren
    posteriormente al pagar la compra.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            compra = confirmar_carrito(
                request.user
            )
        except DjangoValidationError as error:
            raise ValidationError(
                {
                    "detail": error.messages
                }
            ) from error

        serializer = CompraSerializer(compra)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )
