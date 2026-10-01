from django.conf import settings
from django.conf.urls.static import static
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
    # ADMINISTRACION DJANGO
    # ========================================================
    path(
        "admin/",
        admin.site.urls,
    ),

    # ========================================================
    # AUTENTICACION WEB
    # ========================================================
    path(
        "",
        include("accounts.web_urls"),
    ),

    # ========================================================
    # AUTENTICACION JWT
    # ========================================================
    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    # ========================================================
    # MIS ENTRADAS - INTERFAZ WEB
    # ========================================================
    path(
        "mis-entradas/",
        include("entradas.web_urls"),
    ),

    # ========================================================
    # COMPRAS - INTERFAZ WEB
    # ========================================================
    path(
        "compras/",
        include("compras.web_urls"),
    ),

    # ========================================================
    # COMPRAS - API REST
    # ========================================================
    path(
        "api/compras/",
        include("compras.urls"),
    ),

    # ========================================================
    # CARRITO - INTERFAZ WEB
    # ========================================================
    path(
        "carrito/",
        include("carrito.web_urls"),
    ),

    # ========================================================
    # CARRITO - API REST
    # ========================================================
    path(
        "api/carrito/",
        include("carrito.urls"),
    ),

    # ========================================================
    # EVENTOS / RECINTOS / TIPOS DE ENTRADA - API REST
    # ========================================================
    path(
        "api/",
        include("eventos.api_urls"),
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


# ============================================================
# ARCHIVOS MEDIA EN DESARROLLO
# ============================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )







# ============================================================
# ERROR 404 PERSONALIZADO
# ============================================================

handler404 = "config.views.error_404"
