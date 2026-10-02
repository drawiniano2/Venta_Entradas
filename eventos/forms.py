from django import forms

from .models import Evento, Recinto, TipoEntrada


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



class TipoEntradaForm(forms.ModelForm):
    """
    Formulario web para crear y editar tipos de entrada
    pertenecientes a los eventos del organizador.
    """

    class Meta:
        model = TipoEntrada

        fields = [
            "nombre",
            "descripcion",
            "precio",
            "stock_total",
            "stock_disponible",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Ej: General, VIP, Platea",
                }
            ),

            "descripcion": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Descripción opcional",
                }
            ),

            "precio": forms.NumberInput(
                attrs={
                    "class": "campo",
                    "min": "0",
                    "step": "1",
                }
            ),

            "stock_total": forms.NumberInput(
                attrs={
                    "class": "campo",
                    "min": "0",
                }
            ),

            "stock_disponible": forms.NumberInput(
                attrs={
                    "class": "campo",
                    "min": "0",
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "check",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        stock_total = cleaned_data.get("stock_total")
        stock_disponible = cleaned_data.get("stock_disponible")

        if (
            stock_total is not None
            and stock_disponible is not None
            and stock_disponible > stock_total
        ):
            self.add_error(
                "stock_disponible",
                "El stock disponible no puede superar "
                "el stock total.",
            )

        return cleaned_data

# ============================================================
# FORMULARIO DE RECINTO
# ============================================================

class RecintoForm(forms.ModelForm):
    """
    Formulario web para crear recintos desde
    el panel del organizador.
    """

    class Meta:
        model = Recinto

        fields = [
            "nombre",
            "direccion",
            "ciudad",
            "capacidad",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Nombre del recinto",
                }
            ),

            "direccion": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Dirección del recinto",
                }
            ),

            "ciudad": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Ciudad",
                }
            ),

            "capacidad": forms.NumberInput(
                attrs={
                    "class": "campo",
                    "min": "1",
                    "placeholder": "Capacidad máxima",
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "check",
                }
            ),
        }

    def clean_capacidad(self):
        capacidad = self.cleaned_data.get("capacidad")

        if capacidad is not None and capacidad < 1:
            raise forms.ValidationError(
                "La capacidad debe ser mayor que cero."
            )

        return capacidad
