from rest_framework.routers import DefaultRouter

from .api_views import (
    EventoViewSet,
    RecintoViewSet,
    TipoEntradaViewSet,
)


# ============================================================
# ROUTER PRINCIPAL DE LA API DE EVENTOS
# ============================================================

router = DefaultRouter()

router.register(
    "recintos",
    RecintoViewSet,
    basename="recinto",
)

router.register(
    "eventos",
    EventoViewSet,
    basename="evento",
)

router.register(
    "tipos-entrada",
    TipoEntradaViewSet,
    basename="tipo-entrada",
)


# ============================================================
# URLS GENERADAS AUTOMATICAMENTE POR DRF
# ============================================================

urlpatterns = router.urls
