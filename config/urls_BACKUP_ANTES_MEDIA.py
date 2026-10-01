from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    # ========================================================
    # SITIO PUBLICO
    # ========================================================
    path(
        "",
        include("eventos.urls"),
    ),

    # ========================================================
    # ADMINISTRACIÓN DJANGO
    # ========================================================
    path(
        "admin/",
        admin.site.urls,
    ),

    # ========================================================
    # AUTENTICACIÓN JWT
    # ========================================================
    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    # ========================================================
    # COMPRAS
    # ========================================================
    path(
        "api/compras/",
        include("compras.urls"),
    ),

    # ========================================================
    # CARRITO
    # ========================================================
    path(
        "api/carrito/",
        include("carrito.urls"),
    ),

    # ========================================================
    # OPENAPI / SWAGGER
    # ========================================================
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]



