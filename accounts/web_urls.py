from django.urls import path

from .views import (
    cambiar_rol_usuario,
    eliminar_usuario,
    gestion_usuarios,
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
    # GESTION DE USUARIOS - ADMINISTRADOR
    # ========================================================
    path(
        "administracion/usuarios/",
        gestion_usuarios,
        name="gestion_usuarios",
    ),

    path(
        "administracion/usuarios/<int:pk>/rol/",
        cambiar_rol_usuario,
        name="cambiar_rol_usuario",
    ),

    path(
        "administracion/usuarios/<int:pk>/eliminar/",
        eliminar_usuario,
        name="eliminar_usuario",
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
