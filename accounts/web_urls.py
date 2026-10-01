from django.urls import path

from .views import (
    login_web,
    logout_web,
    registro_web,
)


app_name = "accounts_web"


urlpatterns = [
    # ========================================================
    # REGISTRO DE USUARIO
    # ========================================================
    path(
        "registro/",
        registro_web,
        name="registro",
    ),

    # ========================================================
    # INICIO DE SESION
    # ========================================================
    path(
        "login/",
        login_web,
        name="login",
    ),

    # ========================================================
    # CIERRE DE SESION
    # ========================================================
    path(
        "logout/",
        logout_web,
        name="logout",
    ),
]
