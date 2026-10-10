from django.core.exceptions import ValidationError
from django.db import transaction

from compras.models import Compra, DetalleCompra
from eventos.models import TipoEntrada

from .models import Carrito


@transaction.atomic
def confirmar_carrito(usuario):
    """
    Convierte el carrito del usuario en una Compra PENDIENTE.

    Reglas:
    - El usuario debe tener un carrito.
    - El carrito debe contener al menos un item.
    - Se comprueba nuevamente el stock disponible.
    - Confirmar el carrito NO descuenta stock.
    - El precio se copia desde TipoEntrada al DetalleCompra.
    - El total se calcula en el servidor.
    - Los items se eliminan solamente después de crear
      correctamente la compra y sus detalles.

    El descuento definitivo de stock ocurre posteriormente
    mediante pagar_compra().
    """

    try:
        carrito = (
            Carrito.objects
            .select_for_update()
            .prefetch_related(
                "items__tipo_entrada",
                "items__asiento__locacion",
            )
            .get(usuario=usuario)
        )
    except Carrito.DoesNotExist as error:
        raise ValidationError(
            "El usuario no tiene un carrito."
        ) from error

    items = list(carrito.items.all())

    if not items:
        raise ValidationError(
            "No se puede confirmar un carrito vacío."
        )

    # --------------------------------------------------------
    # Validamos nuevamente cantidades y stock.
    #
    # IMPORTANTE:
    # aquí solamente comprobamos disponibilidad.
    # NO descontamos stock.
    # --------------------------------------------------------
    cantidades_por_tipo = {}

    for item in items:
        if item.cantidad < 1:
            raise ValidationError(
                "Todos los items deben tener una cantidad mayor que cero."
            )

        tipo_id = item.tipo_entrada_id

        cantidades_por_tipo[tipo_id] = (
            cantidades_por_tipo.get(tipo_id, 0) + item.cantidad
        )

    tipos_bloqueados = {
        tipo.pk: tipo
        for tipo in TipoEntrada.objects
        .select_for_update()
        .filter(pk__in=sorted(cantidades_por_tipo))
        .order_by("pk")
    }

    for tipo_id, cantidad_total in cantidades_por_tipo.items():
        tipo = tipos_bloqueados.get(tipo_id)

        if tipo is None or not tipo.activo:
            raise ValidationError(
                "Uno de los tipos de entrada no est? disponible."
            )

        if cantidad_total > tipo.stock_disponible:
            raise ValidationError(
                f"Stock insuficiente para '{tipo.nombre}'. "
                f"Disponible: {tipo.stock_disponible}. "
                f"Solicitado: {cantidad_total}."
            )

    # --------------------------------------------------------
    # Validacion de asientos y modalidad del evento.
    asientos_seleccionados = set()

    for item in items:
        tipo = tipos_bloqueados[item.tipo_entrada_id]
        modalidad = tipo.evento.modalidad_entrada

        if modalidad == "UBICACION":
            if item.asiento_id is None or item.cantidad != 1:
                raise ValidationError(
                    "Cada entrada con ubicacion requiere un asiento y cantidad 1."
                )

            if item.asiento_id in asientos_seleccionados:
                raise ValidationError(
                    "Hay un asiento repetido en el carrito."
                )

            asientos_seleccionados.add(item.asiento_id)
            asiento = item.asiento
            locacion = asiento.locacion

            if (
                locacion.evento_id != tipo.evento_id
                or locacion.tipo_entrada_id != tipo.pk
            ):
                raise ValidationError(
                    "El asiento no corresponde al evento y tipo de entrada."
                )

            if not asiento.activo or not locacion.activo:
                raise ValidationError(
                    "Uno de los asientos no esta activo."
                )

        elif item.asiento_id is not None:
            raise ValidationError(
                "Una entrada general no debe tener asiento."
            )

    if asientos_seleccionados:
        ocupados = DetalleCompra.objects.filter(
            asiento_id__in=asientos_seleccionados,
            compra__estado=Compra.Estado.PAGADO,
        ).exists()

        if ocupados:
            raise ValidationError(
                "Uno de los asientos seleccionados ya fue vendido."
            )
    # Creamos la compra inicialmente como PENDIENTE.
    # El total se establecerá desde los detalles reales.
    # --------------------------------------------------------
    compra = Compra.objects.create(
        usuario=usuario,
        estado=Compra.Estado.PENDIENTE,
        total=0,
    )

    # --------------------------------------------------------
    # Copiamos cada item del carrito al detalle de compra.
    #
    # precio_unitario queda congelado como precio histórico.
    # --------------------------------------------------------
    detalles = []

    for item in items:
        detalles.append(
            DetalleCompra(
                compra=compra,
                tipo_entrada=tipos_bloqueados[item.tipo_entrada_id],
                asiento=item.asiento,
                cantidad=item.cantidad,
                precio_unitario=tipos_bloqueados[item.tipo_entrada_id].precio,
            )
        )

    DetalleCompra.objects.bulk_create(detalles)

    # --------------------------------------------------------
    # Calculamos el total desde los detalles recién creados.
    # Nunca aceptamos el total enviado por el cliente.
    # --------------------------------------------------------
    compra.total = compra.calcular_total()

    if compra.total <= 0:
        raise ValidationError(
            "El total de la compra debe ser mayor que cero."
        )

    compra.save(
        update_fields=[
            "total",
            "actualizada_en",
        ]
    )

    # --------------------------------------------------------
    # La conversión terminó correctamente.
    # Vaciamos los items, pero mantenemos el Carrito para que
    # siga siendo el carrito persistente 1:1 del usuario.
    # --------------------------------------------------------
    carrito.items.all().delete()

    return compra
