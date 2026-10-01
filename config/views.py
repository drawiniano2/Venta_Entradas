from django.shortcuts import render


def error_404(request, exception):
    """
    Página personalizada para rutas inexistentes.
    Permite al usuario regresar al inicio del sitio.
    """
    return render(
        request,
        "404.html",
        status=404,
    )
