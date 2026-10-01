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
        "carrito_web:mi-carrito"
    )
