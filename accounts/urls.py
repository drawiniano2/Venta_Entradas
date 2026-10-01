from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    login_web,
    logout_web,
    registro_web,
)


app_name = "accounts"


urlpatterns = [
    # ========================================================
    # AUTENTICACION WEB - REGISTRO
    # ========================================================
    path(
        "registro/",
        registro_web,
        name="registro_web",
    ),

    # ========================================================
    # AUTENTICACION WEB - INICIO DE SESION
    # ========================================================
    path(
        "login/",
        login_web,
        name="login_web",
    ),

    # ========================================================
    # AUTENTICACION WEB - CIERRE DE SESION
    # ========================================================
    path(
        "logout/",
        logout_web,
        name="logout_web",
    ),

    # ========================================================
    # AUTENTICACION API - JWT
    # ========================================================
    path(
        "token/",
        CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
