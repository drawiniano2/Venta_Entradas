from django.shortcuts import get_object_or_404, render

from .models import Evento


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
