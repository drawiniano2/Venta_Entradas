from django.urls import path

from .web_views import mi_carrito_web


app_name = "carrito_web"


urlpatterns = [
    path(
        "",
        mi_carrito_web,
        name="mi-carrito",
    ),
]
