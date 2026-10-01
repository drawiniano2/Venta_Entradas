from django import forms

from .models import Evento, Recinto


class EventoForm(forms.ModelForm):
    """
    Formulario web para crear y editar eventos
    desde el panel del organizador.
    """

    class Meta:
        model = Evento
        fields = [
            "nombre",
            "descripcion",
            "imagen",
            "fecha_inicio",
            "fecha_fin",
            "recinto",
            "estado",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Nombre del evento",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "campo",
                    "rows": 5,
                    "placeholder": "Descripción del evento",
                }
            ),
            "imagen": forms.ClearableFileInput(
                attrs={
                    "class": "campo",
                    "accept": "image/*",
                }
            ),
            "fecha_inicio": forms.DateTimeInput(
                attrs={
                    "class": "campo",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "fecha_fin": forms.DateTimeInput(
                attrs={
                    "class": "campo",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "recinto": forms.Select(
                attrs={"class": "campo"}
            ),
            "estado": forms.Select(
                attrs={"class": "campo"}
            ),
            "activo": forms.CheckboxInput(
                attrs={"class": "check"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["recinto"].queryset = (
            Recinto.objects
            .filter(activo=True)
            .order_by("nombre")
        )

        self.fields["fecha_inicio"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

        self.fields["fecha_fin"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

    def clean(self):
        cleaned_data = super().clean()

        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if (
            fecha_inicio
            and fecha_fin
            and fecha_fin <= fecha_inicio
        ):
            self.add_error(
                "fecha_fin",
                "La fecha de término debe ser posterior "
                "a la fecha de inicio.",
            )

        return cleaned_data
