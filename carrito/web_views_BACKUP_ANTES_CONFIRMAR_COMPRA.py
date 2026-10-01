from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Carrito


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
