from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from carrito.models import Carrito, ItemCarrito

from .models import Evento, TipoEntrada


def inicio(request):
    """
    Portada pública del sistema de venta de entradas.

    Muestra eventos que se encuentran publicados y activos.
    También carga el recinto, organizador y tipos de entrada
    necesarios para presentar la información en pantalla.
    """

    eventos = (
        Evento.objects
        .filter(
            estado=Evento.Estado.PUBLICADO,
            activo=True,
        )
        .select_related(
            "recinto",
            "organizador",
        )
        .prefetch_related(
            "tipos_entrada",
        )
        .order_by("fecha_inicio")[:6]
    )

    contexto = {
        "eventos": eventos,
    }

    return render(
        request,
        "eventos/inicio.html",
        contexto,
    )


def detalle_evento(request, pk):
    """
    Muestra la ficha pública de un evento.

    Solo permite visualizar eventos que estén publicados
    y activos. También carga el recinto, organizador y
    tipos de entrada asociados al evento.
    """

    evento = get_object_or_404(
        Evento.objects
        .select_related(
            "recinto",
            "organizador",
        )
        .prefetch_related(
            "tipos_entrada",
        ),
        pk=pk,
        estado=Evento.Estado.PUBLICADO,
        activo=True,
    )

    tipos_entrada = evento.tipos_entrada.filter(
        activo=True,
    ).order_by("precio")

    contexto = {
        "evento": evento,
        "tipos_entrada": tipos_entrada,
    }

    return render(
        request,
        "eventos/detalle.html",
        contexto,
    )


@login_required
@require_POST
def agregar_al_carrito_web(request, tipo_entrada_id):
    """
    Agrega una entrada al carrito desde la interfaz web.

    Esta operación:
    - requiere un usuario autenticado;
    - utiliza el carrito persistente del usuario;
    - valida que el tipo de entrada esté activo;
    - valida que exista stock disponible;
    - NO descuenta stock;
    - si el tipo ya existe en el carrito, aumenta su cantidad.
    """

    tipo_entrada = get_object_or_404(
        TipoEntrada.objects.select_related("evento"),
        pk=tipo_entrada_id,
        activo=True,
        evento__estado=Evento.Estado.PUBLICADO,
        evento__activo=True,
    )

    if tipo_entrada.stock_disponible < 1:
        messages.error(
            request,
            "Esta entrada se encuentra agotada.",
        )

        return redirect(
            "eventos:detalle",
            pk=tipo_entrada.evento_id,
        )

    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
    )

    item = ItemCarrito.objects.filter(
        carrito=carrito,
        tipo_entrada=tipo_entrada,
    ).first()

    if item is not None:

        nueva_cantidad = item.cantidad + 1

        if nueva_cantidad > tipo_entrada.stock_disponible:
            messages.warning(
                request,
                "No puedes agregar más unidades. "
                "Has alcanzado el stock disponible.",
            )

            return redirect(
                "eventos:detalle",
                pk=tipo_entrada.evento_id,
            )

        item.cantidad = nueva_cantidad
        item.full_clean()
        item.save()

    else:

        item = ItemCarrito(
            carrito=carrito,
            tipo_entrada=tipo_entrada,
            cantidad=1,
        )

        item.full_clean()
        item.save()

    messages.success(
        request,
        f"{tipo_entrada.nombre} fue agregada al carrito.",
    )

    return redirect(
        "eventos:detalle",
        pk=tipo_entrada.evento_id,
    )
