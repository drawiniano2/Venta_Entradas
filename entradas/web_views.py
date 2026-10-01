import io

import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Usuario

from .models import Entrada
from .services import validar_entrada


@login_required
def mis_entradas_web(request):
    """
    Muestra las entradas pertenecientes al usuario autenticado.
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
    Muestra una entrada individual utilizando su UUID.

    Solo el propietario autenticado puede visualizar
    esta entrada.
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


@login_required
def validar_entrada_web(request):
    """
    Permite a un ORGANIZADOR validar una entrada.

    GET:
    muestra el formulario de validación.

    POST:
    recibe el UUID y utiliza el servicio
    transaccional validar_entrada().
    """

    if request.user.rol != Usuario.Rol.ORGANIZADOR:

        messages.error(
            request,
            "Solo los organizadores pueden acceder al validador.",
        )

        return redirect(
            "eventos:inicio"
        )

    entrada = None

    if request.method == "POST":

        codigo = request.POST.get(
            "codigo",
            "",
        ).strip()

        if not codigo:

            messages.error(
                request,
                "Debes ingresar el código UUID de la entrada.",
            )

        else:

            try:

                entrada = validar_entrada(
                    codigo=codigo,
                    organizador=request.user,
                )

            except ValidationError as error:

                for mensaje in error.messages:

                    messages.error(
                        request,
                        mensaje,
                    )

            else:

                messages.success(
                    request,
                    "Entrada validada correctamente.",
                )

    return render(
        request,
        "entradas/validar_entrada.html",
        {
            "entrada": entrada,
        },
    )
