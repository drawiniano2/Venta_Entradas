from django.shortcuts import render

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
