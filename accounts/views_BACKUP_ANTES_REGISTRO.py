from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer


# ============================================================
# AUTENTICACION API - JWT
# ============================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de autenticacion JWT de la API.

    Valida las credenciales del usuario y devuelve:
    - access token
    - refresh token
    - informacion basica del usuario

    El token incluye el rol ESPECTADOR u ORGANIZADOR
    como claim personalizado.
    """

    serializer_class = CustomTokenObtainPairSerializer


# ============================================================
# AUTENTICACION WEB - SESION DJANGO
# ============================================================

def login_web(request):
    """
    Inicia una sesion web utilizando el mismo Usuario
    personalizado utilizado por la API JWT.

    JWT continua siendo el mecanismo de autenticacion
    de la API. Esta vista se utiliza solamente para
    la interfaz HTML del sitio.
    """

    if request.user.is_authenticated:
        return redirect("eventos:inicio")

    siguiente = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        formulario = AuthenticationForm(
            request=request,
            data=request.POST,
        )

        if formulario.is_valid():
            usuario = formulario.get_user()

            login(
                request,
                usuario,
            )

            messages.success(
                request,
                f"Bienvenido, {usuario.username}.",
            )

            if siguiente:
                return redirect(siguiente)

            return redirect("eventos:inicio")

    else:
        formulario = AuthenticationForm(
            request=request,
        )

    contexto = {
        "formulario": formulario,
        "next": siguiente,
    }

    return render(
        request,
        "accounts/login.html",
        contexto,
    )


def logout_web(request):
    """
    Cierra exclusivamente la sesion web Django.
    """

    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "Sesion cerrada correctamente.",
        )

    return redirect("eventos:inicio")
