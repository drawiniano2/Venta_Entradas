from django.urls import path

from .web_views import (
    actualizar_item_web,
    confirmar_carrito_web,
    eliminar_item_web,
    mi_carrito_web,
)


app_name = "carrito_web"


urlpatterns = [
    # ========================================================
    # MI CARRITO
    # ========================================================
    path(
        "",
        mi_carrito_web,
        name="mi-carrito",
    ),

    # ========================================================
    # ACTUALIZAR CANTIDAD
    # ========================================================
    path(
        "items/<int:item_id>/actualizar/",
        actualizar_item_web,
        name="actualizar-item",
    ),

    # ========================================================
    # ELIMINAR ITEM
    # ========================================================
    path(
        "items/<int:item_id>/eliminar/",
        eliminar_item_web,
        name="eliminar-item",
    ),

    # ========================================================
    # CONFIRMAR CARRITO
    # ========================================================
    path(
        "confirmar/",
        confirmar_carrito_web,
        name="confirmar-carrito",
    ),
]
