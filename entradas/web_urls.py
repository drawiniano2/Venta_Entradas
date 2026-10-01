from django.urls import path

from .web_views import (
    detalle_entrada_web,
    mis_entradas_web,
    qr_entrada_web,
    validar_entrada_web,
)


app_name = "entradas_web"


urlpatterns = [
    # ========================================================
    # LISTADO DE ENTRADAS DEL USUARIO
    # ========================================================
    path(
        "",
        mis_entradas_web,
        name="mis-entradas",
    ),

    # ========================================================
    # VALIDADOR DE ENTRADAS PARA ORGANIZADORES
    # ========================================================
    path(
        "validar/",
        validar_entrada_web,
        name="validar-entrada",
    ),

    # ========================================================
    # QR INDIVIDUAL DE UNA ENTRADA
    # ========================================================
    path(
        "<uuid:codigo>/qr/",
        qr_entrada_web,
        name="qr-entrada",
    ),

    # ========================================================
    # DETALLE INDIVIDUAL DE UNA ENTRADA
    # ========================================================
    path(
        "<uuid:codigo>/",
        detalle_entrada_web,
        name="detalle-entrada",
    ),
]
