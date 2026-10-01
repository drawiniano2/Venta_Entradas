from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario de registro público del sistema.

    Reglas:
    - Permite crear únicamente usuarios ESPECTADOR.
    - El rol no se recibe desde el navegador.
    - Utiliza las validaciones de contraseña de Django.
    - Comprueba que el correo electrónico no esté registrado.
    """

    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "correo@ejemplo.cl",
                "autocomplete": "email",
            }
        ),
    )

    class Meta:
        model = Usuario

        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Elige un nombre de usuario",
                    "autocomplete": "username",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Tu nombre",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Tu apellido",
                    "autocomplete": "family-name",
                }
            ),
        }

    def clean_email(self):
        """
        Evita registrar dos cuentas con el mismo correo.
        """

        email = self.cleaned_data["email"].strip().lower()

        if Usuario.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta asociada a este correo electrónico."
            )

        return email

    def save(self, commit=True):
        """
        Fuerza el rol ESPECTADOR desde el servidor.

        Aunque alguien manipule el HTML del navegador,
        no puede registrarse públicamente como ORGANIZADOR.
        """

        usuario = super().save(commit=False)

        usuario.email = self.cleaned_data["email"]
        usuario.rol = Usuario.Rol.ESPECTADOR

        if commit:
            usuario.save()

        return usuario
