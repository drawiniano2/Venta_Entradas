from django.urls import path

from .views import inicio


app_name = "eventos"


urlpatterns = [
    path(
        "",
        inicio,
        name="inicio",
    ),
]
