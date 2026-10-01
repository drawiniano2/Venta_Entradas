from django import template


register = template.Library()


@register.filter
def clp(value):
    """
    Formatea un valor numerico como peso chileno.

    Ejemplo:
        25000 -> 25.000
        1250000 -> 1.250.000
    """
    try:
        numero = int(value)
    except (TypeError, ValueError):
        return value

    return f"{numero:,}".replace(",", ".")
