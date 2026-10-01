from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Carrito
from .services import confirmar_carrito


@login_required
def mi_carrito_web(request):
    """
    Muestra el carrito persistente del usuario autenticado
    mediante la interfaz web.

    Si el usuario todavía no posee carrito, se crea
    automáticamente.

    Consultar el carrito NO modifica el stock.
    """

    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
    )

    carrito = (
        Carrito.objects
        .select_related("usuario")
        .prefetch_related(
            "items__tipo_entrada__evento",
        )
        .get(pk=carrito.pk)
    )

    items = carrito.items.all()

    total = sum(
        item.subtotal
        for item in items
    )

    cantidad_total = sum(
        item.cantidad
        for item in items
    )

    contexto = {
        "carrito": carrito,
        "items": items,
        "total": total,
        "cantidad_total": cantidad_total,
    }

    return render(
        request,
        "carrito/mi_carrito.html",
        contexto,
    )


@login_required
def confirmar_carrito_web(request):
    """
    Convierte el carrito del usuario autenticado
    en una Compra PENDIENTE.

    Esta vista solamente acepta POST.

    IMPORTANTE:
    confirmar el carrito NO descuenta stock.
    El descuento definitivo se realizará posteriormente
    al confirmar el pago.
    """

    if request.method != "POST":
        return redirect(
            "carrito_web:mi-carrito"
        )

    try:
        compra = confirmar_carrito(
            request.user
        )

    except ValidationError as error:
        for mensaje in error.messages:
            messages.error(
                request,
                mensaje,
            )

        return redirect(
            "carrito_web:mi-carrito"
        )

    messages.success(
        request,
        (
            f"Compra #{compra.pk} creada correctamente. "
            "Ahora puedes continuar con la confirmación del pago."
        ),
    )

    return redirect(
        "compras_web:detalle-compra",
        compra_id=compra.pk,
    )



# ============================================================
# ACTUALIZAR CANTIDAD DE UN ITEM - INTERFAZ WEB
# ============================================================

@login_required
def actualizar_item_web(request, item_id):
    """
    Actualiza la cantidad de un item del carrito desde
    la interfaz web.

    Esta operación NO descuenta stock.
    """

    if request.method != "POST":
        return redirect(
            "carrito_web:mi-carrito"
        )

    from .models import ItemCarrito

    try:
        item = (
            ItemCarrito.objects
            .select_related(
                "carrito",
                "tipo_entrada",
            )
            .get(
                pk=item_id,
                carrito__usuario=request.user,
            )
        )

    except ItemCarrito.DoesNotExist:
        messages.error(
            request,
            "La entrada solicitada no existe en tu carrito.",
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    accion = request.POST.get(
        "accion",
        "",
    ).strip().lower()

    cantidad_actual = item.cantidad

    if accion == "aumentar":
        nueva_cantidad = cantidad_actual + 1

    elif accion == "disminuir":
        nueva_cantidad = cantidad_actual - 1

    else:
        messages.error(
            request,
            "La operación solicitada no es válida.",
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    if nueva_cantidad < 1:
        messages.warning(
            request,
            "La cantidad mínima es 1. Usa Eliminar para quitar la entrada.",
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    if nueva_cantidad > item.tipo_entrada.stock_disponible:
        messages.warning(
            request,
            (
                "No puedes seleccionar más entradas "
                "que el stock disponible."
            ),
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    item.cantidad = nueva_cantidad

    try:
        item.full_clean()
        item.save(
            update_fields=[
                "cantidad",
                "actualizado_en",
            ]
        )

    except ValidationError as error:
        for mensaje in error.messages:
            messages.error(
                request,
                mensaje,
            )

    return redirect(
        "carrito_web:mi-carrito"
    )


# ============================================================
# ELIMINAR ITEM - INTERFAZ WEB
# ============================================================

@login_required
def eliminar_item_web(request, item_id):
    """
    Elimina un item perteneciente al carrito del usuario.

    Eliminar del carrito NO modifica el stock.
    """

    if request.method != "POST":
        return redirect(
            "carrito_web:mi-carrito"
        )

    from .models import ItemCarrito

    try:
        item = ItemCarrito.objects.get(
            pk=item_id,
            carrito__usuario=request.user,
        )

    except ItemCarrito.DoesNotExist:
        messages.error(
            request,
            "La entrada solicitada no existe en tu carrito.",
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    nombre_entrada = item.tipo_entrada.nombre

    item.delete()

    messages.success(
        request,
        f"{nombre_entrada} fue eliminada del carrito.",
    )

    return redirect(
        "carrito_web:mi-carrito"
    )
