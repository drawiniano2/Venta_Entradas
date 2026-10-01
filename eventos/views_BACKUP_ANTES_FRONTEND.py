from django.shortcuts import render

from .models import Evento


def inicio(request):
    """
    Portada pública del sistema de venta de entradas.

    Muestra únicamente eventos publicados y activos.
    Se recuperan también el recinto y los tipos de entrada
    para evitar consultas innecesarias desde la plantilla.
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
