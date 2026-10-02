from django.urls import path

from .views import (
    agregar_al_carrito_web,
    detalle_evento,
    editar_evento,
    editar_tipo_entrada,
    eliminar_evento,
    eliminar_tipo_entrada,
    inicio,
    nuevo_evento,
    nuevo_recinto,
    nuevo_tipo_entrada,
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
    # GESTION DE EVENTOS - ORGANIZADOR
    # ========================================================
    path(
        "organizador/eventos/nuevo/",
        nuevo_evento,
        name="nuevo_evento",
    ),

    path(
        "organizador/eventos/<int:pk>/editar/",
        editar_evento,
        name="editar_evento",
    ),

    path(
        "organizador/eventos/<int:pk>/eliminar/",
        eliminar_evento,
        name="eliminar_evento",
    ),

    # ========================================================
    # GESTION DE RECINTOS - ORGANIZADOR
    # ========================================================

    path(
        "organizador/recintos/nuevo/",
        nuevo_recinto,
        name="nuevo_recinto",
    ),

    # ========================================================
    # GESTION DE TIPOS DE ENTRADA - ORGANIZADOR
    # ========================================================
    path(
        "organizador/eventos/<int:evento_pk>/entradas/nueva/",
        nuevo_tipo_entrada,
        name="nuevo_tipo_entrada",
    ),

    path(
        "organizador/entradas/<int:pk>/editar/",
        editar_tipo_entrada,
        name="editar_tipo_entrada",
    ),

    path(
        "organizador/entradas/<int:pk>/eliminar/",
        eliminar_tipo_entrada,
        name="eliminar_tipo_entrada",
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
    # CARRITO - INTERFAZ WEB
    # ========================================================
    path(
        "carrito/agregar/<int:tipo_entrada_id>/",
        agregar_al_carrito_web,
        name="agregar_al_carrito",
    ),
]

