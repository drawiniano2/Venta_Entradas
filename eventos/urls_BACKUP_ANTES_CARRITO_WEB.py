from django.urls import path

from .views import detalle_evento, inicio


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
    # DETALLE PUBLICO DEL EVENTO
    # ========================================================
    path(
        "eventos/<int:pk>/",
        detalle_evento,
        name="detalle",
    ),
]
