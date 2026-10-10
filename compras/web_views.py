from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Compra
from .services import pagar_compra


@login_required
def detalle_compra_web(request, compra_id):
    """
    Muestra el resumen de una compra perteneciente
    al usuario autenticado.

    La consulta no modifica stock ni cambia
    el estado de la compra.
    """

    compra = get_object_or_404(
        Compra.objects
        .select_related("usuario")
        .prefetch_related(
            "detalles__tipo_entrada__evento",
            "detalles__entradas",
        ),
        pk=compra_id,
        usuario=request.user,
    )

    return render(
        request,
        "compras/detalle_compra.html",
        {
            "compra": compra,
            "detalles": compra.detalles.all(),
        },
    )


@login_required
def pagar_compra_web(request, compra_id):
    """
    Confirma desde la interfaz web el pago
    de una compra del usuario autenticado.

    Solo acepta POST.

    La lógica transaccional real permanece
    centralizada en services.pagar_compra().
    """

    if request.method != "POST":
        return redirect(
            "compras_web:detalle-compra",
            compra_id=compra_id,
        )

    compra = get_object_or_404(
        Compra,
        pk=compra_id,
        usuario=request.user,
    )

    try:
        pagar_compra(compra.pk)

    except ValidationError as error:
        for mensaje in error.messages:
            messages.error(
                request,
                mensaje,
            )

        return redirect(
            "compras_web:detalle-compra",
            compra_id=compra.pk,
        )

    messages.success(
        request,
        (
            f"Compra #{compra.pk} pagada correctamente. "
            "Las entradas fueron generadas."
        ),
    )

    return redirect(
        "compras_web:detalle-compra",
        compra_id=compra.pk,
    )


# ============================================================
# MIS COMPRAS - INTERFAZ WEB
# ============================================================

@login_required
def mis_compras_web(request):
    """
    Muestra exclusivamente el historial de compras
    pertenecientes al usuario autenticado.

    La vista es de solo lectura:
    - No modifica stock.
    - No cambia estados.
    - No permite consultar compras de otros usuarios.
    """

    compras = (
        Compra.objects
        .filter(usuario=request.user, oculta_en_historial=False)
        .prefetch_related(
            "detalles__tipo_entrada__evento",
            "detalles__entradas",
        )
        .order_by("-creada_en")
    )

    return render(
        request,
        "compras/mis_compras.html",
        {
            "compras": compras,
        },
    )

# ============================================================
# OCULTAR COMPRA DEL HISTORIAL PERSONAL
# ============================================================

@login_required
def ocultar_compra_web(request, compra_id):
    """
    Oculta una compra del historial visible del propietario.

    No elimina la compra ni modifica pagos,
    stock o entradas emitidas.
    """

    if request.method != "POST":
        return redirect("compras_web:mis-compras")

    compra = get_object_or_404(
        Compra,
        pk=compra_id,
        usuario=request.user,
    )

    if not compra.oculta_en_historial:
        compra.oculta_en_historial = True
        compra.save(update_fields=["oculta_en_historial"])

        messages.success(
            request,
            f"Compra #{compra.pk} retirada de Mis compras. El registro se conserva.",
        )

    return redirect("compras_web:mis-compras")
