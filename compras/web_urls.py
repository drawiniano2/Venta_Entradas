from django.urls import path

from .web_views import (
    detalle_compra_web,
    mis_compras_web,
    pagar_compra_web,
)


app_name = "compras_web"


urlpatterns = [
    # ========================================================
    # MIS COMPRAS
    # ========================================================
    path(
        "",
        mis_compras_web,
        name="mis-compras",
    ),

    # ========================================================
    # DETALLE DE COMPRA
    # ========================================================
    path(
        "<int:compra_id>/",
        detalle_compra_web,
        name="detalle-compra",
    ),

    # ========================================================
    # PAGAR COMPRA
    # ========================================================
    path(
        "<int:compra_id>/pagar/",
        pagar_compra_web,
        name="pagar-compra",
    ),
]
