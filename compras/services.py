from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from entradas.models import Entrada
from eventos.models import TipoEntrada

from .models import Compra


@transaction.atomic
def pagar_compra(compra_id):
    """
    Confirma una compra de forma atómica.

    Reglas:
    - Solo una compra PENDIENTE puede pagarse.
    - Bloquea las filas de stock involucradas.
    - Comprueba nuevamente el stock real.
    - Descuenta stock solamente al pagar.
    - Genera una Entrada con UUID por cada unidad comprada.
    - Marca finalmente la compra como PAGADO.

    Si ocurre cualquier error, toda la operación se revierte.
    """

    compra = (
        Compra.objects
        .select_for_update()
        .prefetch_related("detalles")
        .get(pk=compra_id)
    )

    if compra.estado != Compra.Estado.PENDIENTE:
        raise ValidationError(
            "Solo una compra PENDIENTE puede pasar a PAGADO."
        )

    detalles = list(compra.detalles.all())

    if not detalles:
        raise ValidationError(
            "No se puede pagar una compra sin detalles."
        )

    # El total se calcula siempre desde los detalles reales
    # de la compra. No se confía en un total proporcionado
    # externamente por el cliente.
    total_calculado = compra.calcular_total()

    if total_calculado <= 0:
        raise ValidationError(
            "El total de la compra debe ser mayor que cero."
        )

    compra.total = total_calculado
    compra.save(
        update_fields=[
            "total",
            "actualizada_en",
        ]
    )

    # Bloqueamos los tipos de entrada en un orden estable
    # para reducir el riesgo de bloqueos cruzados.
    tipo_ids = sorted(
        {detalle.tipo_entrada_id for detalle in detalles}
    )

    tipos_bloqueados = {
        tipo.pk: tipo
        for tipo in TipoEntrada.objects
        .select_for_update()
        .filter(pk__in=tipo_ids)
        .order_by("pk")
    }

    # Primero validamos TODO el stock.
    # No modificamos nada hasta saber que todos los detalles
    # pueden ser procesados.
    for detalle in detalles:
        tipo = tipos_bloqueados.get(detalle.tipo_entrada_id)

        if tipo is None:
            raise ValidationError(
                "Uno de los tipos de entrada ya no está disponible."
            )

        if detalle.cantidad > tipo.stock_disponible:
            raise ValidationError(
                (
                    f"Stock insuficiente para '{tipo.nombre}'. "
                    f"Disponible: {tipo.stock_disponible}. "
                    f"Solicitado: {detalle.cantidad}."
                )
            )

    # Una vez validado todo, descontamos el stock.
    for detalle in detalles:
        tipo = tipos_bloqueados[detalle.tipo_entrada_id]

        tipo.stock_disponible -= detalle.cantidad
        tipo.save(
            update_fields=["stock_disponible", "actualizado_en"]
        )

    # Generamos una entrada individual por cada unidad comprada.
    entradas_nuevas = []

    for detalle in detalles:
        for _ in range(detalle.cantidad):
            entradas_nuevas.append(
                Entrada(
                    detalle_compra=detalle,
                    estado=Entrada.Estado.VALIDA,
                )
            )

    Entrada.objects.bulk_create(entradas_nuevas)

    compra.estado = Compra.Estado.PAGADO
    compra.pagada_en = timezone.now()
    compra.save(
        update_fields=[
            "estado",
            "pagada_en",
            "actualizada_en",
        ]
    )

    return compra


@transaction.atomic
def cancelar_compra(compra_id):
    """
    Cancela una compra PAGADA de forma atómica.

    Reglas:
    - Solo una compra PAGADA puede cancelarse.
    - Repone exactamente el stock descontado.
    - Anula las entradas emitidas.
    - Marca la compra como CANCELADO.
    - Toda la operación se ejecuta dentro de una transacción.
    """

    compra = (
        Compra.objects
        .select_for_update()
        .prefetch_related("detalles__entradas")
        .get(pk=compra_id)
    )

    if compra.estado != Compra.Estado.PAGADO:
        raise ValidationError(
            "Solo una compra PAGADA puede ser cancelada."
        )

    detalles = list(compra.detalles.all())

    tipo_ids = sorted(
        {detalle.tipo_entrada_id for detalle in detalles}
    )

    tipos_bloqueados = {
        tipo.pk: tipo
        for tipo in TipoEntrada.objects
        .select_for_update()
        .filter(pk__in=tipo_ids)
        .order_by("pk")
    }

    # Reponemos el stock de cada detalle comprado.
    for detalle in detalles:
        tipo = tipos_bloqueados.get(detalle.tipo_entrada_id)

        if tipo is None:
            raise ValidationError(
                "No fue posible localizar uno de los tipos de entrada."
            )

        nuevo_stock = tipo.stock_disponible + detalle.cantidad

        if nuevo_stock > tipo.stock_total:
            raise ValidationError(
                (
                    f"No se puede reponer el stock de '{tipo.nombre}' "
                    "porque superaría el stock total."
                )
            )

        tipo.stock_disponible = nuevo_stock
        tipo.save(
            update_fields=["stock_disponible", "actualizado_en"]
        )

    # Las entradas emitidas dejan de ser válidas.
    Entrada.objects.filter(
        detalle_compra__compra=compra
    ).update(
        estado=Entrada.Estado.ANULADA
    )

    compra.estado = Compra.Estado.CANCELADO
    compra.cancelada_en = timezone.now()
    compra.save(
        update_fields=[
            "estado",
            "cancelada_en",
            "actualizada_en",
        ]
    )

    return compra

