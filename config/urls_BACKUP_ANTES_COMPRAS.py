from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
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
