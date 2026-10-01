from django.urls import path

from .views import (
    agregar_al_carrito_web,
    detalle_evento,
    inicio,
    panel_organizador,
)


app_name = "eventos"


urlpatterns = [
    # ========================================================
    # PORTADA PUBLICA
    # ========================================================
    path(
        "",
        inicio,
        name="inicio",
    ),

    # ========================================================
    # PANEL PRIVADO DEL ORGANIZADOR
    # ========================================================
    path(
        "organizador/",
        panel_organizador,
        name="panel_organizador",
    ),

    # ========================================================
    # DETALLE PUBLICO DEL EVENTO
    # ========================================================
    path(
        "eventos/<int:pk>/",
        detalle_evento,
        name="detalle",
    ),

    # ========================================================
    # PANEL PRIVADO DEL ORGANIZADOR
    # ========================================================
    path(
        "organizador/",
        panel_organizador,
        name="panel-organizador",
    ),

    # ========================================================
    # CARRITO - INTERFAZ WEB
    # ========================================================
    path(
        "carrito/agregar/<int:tipo_entrada_id>/",
        agregar_al_carrito_web,
        name="agregar_al_carrito",
    ),
]


