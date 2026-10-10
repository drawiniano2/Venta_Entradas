from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from entradas.models import Entrada
from eventos.models import TipoEntrada, Asiento

from .models import Compra, DetalleCompra


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

    # Bloqueamos los asientos antes de comprobar ventas.
    asiento_ids = sorted({
        detalle.asiento_id
        for detalle in detalles
        if detalle.asiento_id is not None
    })

    asientos_bloqueados = []

    if asiento_ids:
        asientos_bloqueados = list(
            Asiento.objects.select_related("locacion")
            .select_for_update(of=("self",))
            .filter(pk__in=asiento_ids)
            .order_by("pk")
        )

        if len(asientos_bloqueados) != len(asiento_ids):
            raise ValidationError(
                "Uno de los asientos ya no existe."
            )

        asientos_vendidos = DetalleCompra.objects.filter(
            asiento_id__in=asiento_ids,
            compra__estado=Compra.Estado.PAGADO,
        ).exclude(compra_id=compra.pk).exists()

        if asientos_vendidos:
            raise ValidationError(
                "Uno de los asientos ya fue vendido."
            )

    # Validamos modalidad, asientos y stock agrupado.
    cantidades_por_tipo = {}
    asientos_en_compra = set()

    asientos_por_id = {
        asiento.pk: asiento
        for asiento in asientos_bloqueados
    }

    for detalle in detalles:
        tipo = tipos_bloqueados.get(detalle.tipo_entrada_id)

        if tipo is None or not tipo.activo:
            raise ValidationError(
                "Uno de los tipos de entrada no est? disponible."
            )

        if detalle.cantidad < 1:
            raise ValidationError(
                "La cantidad debe ser mayor que cero."
            )

        modalidad = tipo.evento.modalidad_entrada

        if modalidad == "UBICACION":
            if detalle.asiento_id is None or detalle.cantidad != 1:
                raise ValidationError(
                    "Cada entrada con ubicaci?n requiere un asiento y cantidad 1."
                )

            if detalle.asiento_id in asientos_en_compra:
                raise ValidationError(
                    "La compra contiene un asiento repetido."
                )

            asientos_en_compra.add(detalle.asiento_id)

            asiento = asientos_por_id.get(detalle.asiento_id)

            if asiento is None:
                raise ValidationError(
                    "Uno de los asientos no existe."
                )

            locacion = asiento.locacion

            if (
                locacion.evento_id != tipo.evento_id
                or locacion.tipo_entrada_id != tipo.pk
            ):
                raise ValidationError(
                    "El asiento no corresponde al evento o tipo de entrada."
                )

            if not asiento.activo or not locacion.activo:
                raise ValidationError(
                    "Uno de los asientos o ubicaciones est? inactivo."
                )

        elif modalidad == "GENERAL":
            if detalle.asiento_id is not None:
                raise ValidationError(
                    "Una entrada general no debe tener asiento."
                )

        else:
            raise ValidationError(
                "Modalidad de entrada no reconocida."
            )

        tipo_id = detalle.tipo_entrada_id
        cantidades_por_tipo[tipo_id] = (
            cantidades_por_tipo.get(tipo_id, 0) + detalle.cantidad
        )

    for tipo_id, cantidad_total in cantidades_por_tipo.items():
        tipo = tipos_bloqueados[tipo_id]

        if cantidad_total > tipo.stock_disponible:
            raise ValidationError(
                f"Stock insuficiente para '{tipo.nombre}'. "
                f"Disponible: {tipo.stock_disponible}. "
                f"Solicitado: {cantidad_total}."
            )

    # Descontamos una sola vez por tipo de entrada.
    for tipo_id, cantidad_total in cantidades_por_tipo.items():
        tipo = tipos_bloqueados[tipo_id]

        tipo.stock_disponible -= cantidad_total

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

    # Agrupamos las cantidades por tipo de entrada.
    cantidades_por_tipo = {}

    for detalle in detalles:
        if detalle.cantidad < 1:
            raise ValidationError(
                "La cantidad de un detalle no es valida."
            )

        tipo_id = detalle.tipo_entrada_id

        cantidades_por_tipo[tipo_id] = (
            cantidades_por_tipo.get(tipo_id, 0) + detalle.cantidad
        )

    # Validamos toda la reposicion antes de actualizar stock.
    for tipo_id, cantidad_total in cantidades_por_tipo.items():
        tipo = tipos_bloqueados.get(tipo_id)

        if tipo is None:
            raise ValidationError(
                "No fue posible localizar uno de los tipos de entrada."
            )

        if tipo.stock_disponible + cantidad_total > tipo.stock_total:
            raise ValidationError(
                f"No se puede reponer el stock de '{tipo.nombre}' "
                "porque superaria el stock total."
            )

    # Reponemos una sola vez por tipo de entrada.
    for tipo_id, cantidad_total in cantidades_por_tipo.items():
        tipo = tipos_bloqueados[tipo_id]
        tipo.stock_disponible += cantidad_total
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
