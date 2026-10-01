from django.core.exceptions import ValidationError
from django.db import transaction

from compras.models import Compra, DetalleCompra

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
                "items__tipo_entrada"
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
    for item in items:
        if item.cantidad < 1:
            raise ValidationError(
                "Todos los items deben tener una cantidad mayor que cero."
            )

        if item.cantidad > item.tipo_entrada.stock_disponible:
            raise ValidationError(
                (
                    f"Stock insuficiente para "
                    f"'{item.tipo_entrada.nombre}'. "
                    f"Disponible: "
                    f"{item.tipo_entrada.stock_disponible}. "
                    f"Solicitado: {item.cantidad}."
                )
            )

    # --------------------------------------------------------
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
                tipo_entrada=item.tipo_entrada,
                cantidad=item.cantidad,
                precio_unitario=item.tipo_entrada.precio,
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
