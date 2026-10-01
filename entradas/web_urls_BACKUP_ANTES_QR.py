from django.urls import path

from .web_views import (
    detalle_entrada_web,
    mis_entradas_web,
)


app_name = "entradas_web"


urlpatterns = [
    path(
        "",
        mis_entradas_web,
        name="mis-entradas",
    ),

    path(
        "<uuid:codigo>/",
        detalle_entrada_web,
        name="detalle-entrada",
    ),
]
