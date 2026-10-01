import io

import qrcode

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Entrada


@login_required
def mis_entradas_web(request):
    """
    Muestra las entradas pertenecientes al usuario autenticado.

    La relación con el usuario se obtiene mediante:
    Entrada -> DetalleCompra -> Compra -> Usuario.

    Un usuario nunca puede visualizar las entradas
    pertenecientes a otro comprador.
    """

    entradas = (
        Entrada.objects
        .filter(
            detalle_compra__compra__usuario=request.user,
        )
        .select_related(
            "detalle_compra",
            "detalle_compra__compra",
            "detalle_compra__tipo_entrada",
            "detalle_compra__tipo_entrada__evento",
        )
        .order_by("-emitida_en")
    )

    contexto = {
        "entradas": entradas,
        "total_entradas": entradas.count(),
    }

    return render(
        request,
        "entradas/mis_entradas.html",
        contexto,
    )


@login_required
def detalle_entrada_web(request, codigo):
    """
    Muestra una entrada individual.

    Se utiliza el UUID público de la entrada en lugar
    del ID incremental de la base de datos.

    También se valida que la entrada pertenezca
    al usuario autenticado.
    """

    entrada = get_object_or_404(
        Entrada.objects.select_related(
            "detalle_compra",
            "detalle_compra__compra",
            "detalle_compra__tipo_entrada",
            "detalle_compra__tipo_entrada__evento",
        ),
        codigo=codigo,
        detalle_compra__compra__usuario=request.user,
    )

    return render(
        request,
        "entradas/detalle_entrada.html",
        {
            "entrada": entrada,
        },
    )


@login_required
def qr_entrada_web(request, codigo):
    """
    Genera dinámicamente el código QR de una entrada.

    El QR contiene el UUID único de la entrada.
    Solo el propietario autenticado puede solicitarlo.
    """

    entrada = get_object_or_404(
        Entrada,
        codigo=codigo,
        detalle_compra__compra__usuario=request.user,
    )

    contenido_qr = str(
        entrada.codigo
    )

    imagen_qr = qrcode.make(
        contenido_qr
    )

    buffer = io.BytesIO()

    imagen_qr.save(
        buffer,
        format="PNG",
    )

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png",
    )
