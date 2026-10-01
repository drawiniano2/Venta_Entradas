from django.urls import path

from .views import (
    login_web,
    logout_web,
)


app_name = "accounts_web"


urlpatterns = [
    path(
        "login/",
        login_web,
        name="login",
    ),

    path(
        "logout/",
        logout_web,
        name="logout",
    ),
]
