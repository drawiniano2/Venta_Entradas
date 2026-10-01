from django.urls import path

from .web_views import (
    detalle_compra_web,
    pagar_compra_web,
)


app_name = "compras_web"


urlpatterns = [
    path(
        "<int:compra_id>/",
        detalle_compra_web,
        name="detalle-compra",
    ),

    path(
        "<int:compra_id>/pagar/",
        pagar_compra_web,
        name="pagar-compra",
    ),
]
