from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Usuario

from .models import Entrada


@transaction.atomic
def validar_entrada(codigo, organizador):
    """
    Valida una entrada mediante su UUID.

    Reglas de negocio:
    - El usuario debe tener rol ORGANIZADOR.
    - La entrada debe existir.
    - El organizador solo puede validar entradas
      pertenecientes a sus propios eventos.
    - La entrada debe encontrarse en estado VALIDA.
    - Una entrada utilizada no puede utilizarse nuevamente.
    - La operación se ejecuta dentro de una transacción
      y bloquea temporalmente la fila de la entrada.
    """

    if organizador.rol != Usuario.Rol.ORGANIZADOR:
        raise ValidationError(
            "Solo un usuario ORGANIZADOR puede validar entradas."
        )

    try:
        entrada = (
            Entrada.objects
            .select_for_update()
            .select_related(
                "detalle_compra",
                "detalle_compra__compra",
                "detalle_compra__tipo_entrada",
                "detalle_compra__tipo_entrada__evento",
                "detalle_compra__tipo_entrada__evento__organizador",
            )
            .get(
                codigo=codigo,
            )
        )

    except Entrada.DoesNotExist as error:
        raise ValidationError(
            "La entrada indicada no existe."
        ) from error

    evento = (
        entrada
        .detalle_compra
        .tipo_entrada
        .evento
    )

    if evento.organizador_id != organizador.id:
        raise ValidationError(
            "No tienes autorización para validar "
            "entradas de este evento."
        )

    if entrada.estado == Entrada.Estado.UTILIZADA:
        raise ValidationError(
            "Esta entrada ya fue utilizada."
        )

    if entrada.estado == Entrada.Estado.ANULADA:
        raise ValidationError(
            "Esta entrada se encuentra anulada."
        )

    if entrada.estado != Entrada.Estado.VALIDA:
        raise ValidationError(
            "La entrada no se encuentra disponible "
            "para validación."
        )

    entrada.estado = Entrada.Estado.UTILIZADA
    entrada.utilizada_en = timezone.now()

    entrada.full_clean()

    entrada.save(
        update_fields=[
            "estado",
            "utilizada_en",
        ]
    )

    return entrada
