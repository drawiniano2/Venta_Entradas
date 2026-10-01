from django.urls import path

from .views import (
    AgregarItemCarritoView,
    ConfirmarCarritoView,
    EliminarItemCarritoView,
    MiCarritoView,
    ModificarItemCarritoView,
)


app_name = "carrito"


urlpatterns = [
    # ========================================================
    # MI CARRITO
    # ========================================================
    path(
        "",
        MiCarritoView.as_view(),
        name="mi-carrito",
    ),

    # ========================================================
    # ITEMS DEL CARRITO
    # ========================================================
    path(
        "items/",
        AgregarItemCarritoView.as_view(),
        name="agregar-item",
    ),

    path(
        "items/<int:pk>/",
        ModificarItemCarritoView.as_view(),
        name="modificar-item",
    ),

    path(
        "items/<int:pk>/eliminar/",
        EliminarItemCarritoView.as_view(),
        name="eliminar-item",
    ),

    # ========================================================
    # CONFIRMAR CARRITO
    # ========================================================
    path(
        "confirmar/",
        ConfirmarCarritoView.as_view(),
        name="confirmar-carrito",
    ),
]
