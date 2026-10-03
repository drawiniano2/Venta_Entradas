from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from carrito.models import Carrito, ItemCarrito
from compras.models import Compra

from .forms import EventoForm, RecintoForm, TipoEntradaForm
from .models import Asiento, Evento, TipoEntrada


def inicio(request):
    """
    Portada publica del sistema de venta de entradas.

    Muestra exclusivamente eventos publicados y activos.

    Permite buscar por:
    - nombre del evento;
    - descripcion del evento;
    - nombre del recinto;
    - ciudad del recinto;
    - direccion del recinto.

    La busqueda no distingue entre mayusculas y minusculas.
    """

    consulta = request.GET.get(
        "q",
        "",
    ).strip()

    eventos = (
        Evento.objects
        .filter(
            estado=Evento.Estado.PUBLICADO,
            activo=True,
        )
        .select_related(
            "recinto",
            "organizador",
        )
        .prefetch_related(
            "tipos_entrada",
        )
    )

    if consulta:
        eventos = eventos.filter(
            Q(nombre__icontains=consulta)
            | Q(descripcion__icontains=consulta)
            | Q(recinto__nombre__icontains=consulta)
            | Q(recinto__ciudad__icontains=consulta)
            | Q(recinto__direccion__icontains=consulta)
        )

    # Cantidad total de eventos encontrados.
    cantidad_resultados = eventos.count()

    eventos = eventos.order_by(
        "fecha_inicio"
    )

    # Ciudades disponibles obtenidas automaticamente desde
    # los eventos publicados y activos.
    ciudades = (
        Evento.objects
        .filter(
            estado=Evento.Estado.PUBLICADO,
            activo=True,
        )
        .exclude(
            recinto__ciudad__isnull=True,
        )
        .exclude(
            recinto__ciudad="",
        )
        .values_list(
            "recinto__ciudad",
            flat=True,
        )
        .distinct()
        .order_by(
            "recinto__ciudad"
        )
    )
    contexto = {
        "eventos": eventos,
        "consulta": consulta,
        "cantidad_resultados": cantidad_resultados,
        "ciudades": ciudades,
    }

    return render(
        request,
        "eventos/inicio.html",
        contexto,
    )


def detalle_evento(request, pk):
    """
    Muestra la ficha pública de un evento.

    Solo permite visualizar eventos que estén publicados
    y activos. También carga el recinto, organizador y
    tipos de entrada asociados al evento.
    """

    evento = get_object_or_404(
        Evento.objects
        .select_related(
            "recinto",
            "organizador",
        )
        .prefetch_related(
            "tipos_entrada",
            "locaciones__tipo_entrada",
            "locaciones__asientos",
        ),
        pk=pk,
        estado=Evento.Estado.PUBLICADO,
        activo=True,
    )

    tipos_entrada = evento.tipos_entrada.filter(
        activo=True,
    ).order_by("precio")

    locaciones = evento.locaciones.filter(
        activo=True,
    ).select_related(
        "tipo_entrada",
    ).prefetch_related(
        "asientos",
    ).order_by(
        "orden",
        "nombre",
    )

    # --------------------------------------------------------
    # Asientos que ya pertenecen a una compra PAGADA.
    #
    # No modificamos f?sicamente el modelo Asiento.
    # La ocupaci?n se obtiene desde la compra real, por lo que
    # una compra cancelada deja de considerar ocupado el asiento.
    # --------------------------------------------------------

    asientos_vendidos = set(
        Asiento.objects.filter(
            locacion__evento=evento,
            detalles_compra__compra__estado=Compra.Estado.PAGADO,
        ).values_list(
            "pk",
            flat=True,
        )
    )

    # Marcamos cada asiento para simplificar la plantilla.
    # Este atributo existe solamente durante esta respuesta web;
    # no modifica la base de datos.
    for locacion in locaciones:
        for asiento in locacion.asientos.all():
            asiento.vendido = asiento.pk in asientos_vendidos

    contexto = {
        "evento": evento,
        "tipos_entrada": tipos_entrada,
        "locaciones": locaciones,
        "asientos_vendidos": asientos_vendidos,
    }

    return render(
        request,
        "eventos/detalle.html",
        contexto,
    )


@login_required
@require_POST
def agregar_al_carrito_web(request, tipo_entrada_id):
    """
    Agrega una entrada al carrito desde la interfaz web.

    EVENTO GENERAL:
    - agrega el tipo de entrada;
    - si ya existe, aumenta la cantidad.

    EVENTO CON UBICACION:
    - exige un asiento;
    - valida que el asiento pertenezca al mismo evento;
    - valida que corresponda al tipo de entrada seleccionado;
    - cada asiento se guarda como un item independiente;
    - la cantidad siempre es 1.

    Agregar al carrito NO descuenta stock.
    """

    tipo_entrada = get_object_or_404(
        TipoEntrada.objects.select_related("evento"),
        pk=tipo_entrada_id,
        activo=True,
        evento__estado=Evento.Estado.PUBLICADO,
        evento__activo=True,
    )

    evento = tipo_entrada.evento

    if tipo_entrada.stock_disponible < 1:
        messages.error(
            request,
            "Esta entrada se encuentra agotada.",
        )
        return redirect(
            "eventos:detalle",
            pk=evento.pk,
        )

    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
    )

    # ========================================================
    # EVENTO CON UBICACION / ASIENTO
    # ========================================================

    if evento.modalidad_entrada == Evento.ModalidadEntrada.UBICACION:

        asiento_id = request.POST.get("asiento_id")

        if not asiento_id:
            messages.error(
                request,
                "Debes seleccionar un asiento.",
            )
            return redirect(
                "eventos:detalle",
                pk=evento.pk,
            )

        asiento = get_object_or_404(
            Asiento.objects.select_related(
                "locacion",
                "locacion__evento",
                "locacion__tipo_entrada",
            ),
            pk=asiento_id,
            activo=True,
            locacion__activo=True,
            locacion__evento=evento,
            locacion__tipo_entrada=tipo_entrada,
        )

        # --------------------------------------------------------
        # BLOQUEO DE ASIENTO YA VENDIDO
        #
        # La interfaz ya marca visualmente los asientos vendidos,
        # pero esta comprobacion protege tambien el backend frente
        # a una peticion POST manual o una pagina desactualizada.
        # --------------------------------------------------------

        asiento_vendido = asiento.detalles_compra.filter(
            compra__estado=Compra.Estado.PAGADO,
        ).exists()

        if asiento_vendido:
            messages.error(
                request,
                f"El asiento {asiento.codigo} ya fue vendido.",
            )
            return redirect(
                "eventos:detalle",
                pk=evento.pk,
            )

        if ItemCarrito.objects.filter(
            carrito=carrito,
            asiento=asiento,
        ).exists():
            messages.warning(
                request,
                f"El asiento {asiento.codigo} ya esta en tu carrito.",
            )
            return redirect(
                "carrito_web:mi-carrito"
            )

        item = ItemCarrito(
            carrito=carrito,
            tipo_entrada=tipo_entrada,
            asiento=asiento,
            cantidad=1,
        )

        item.full_clean()
        item.save()

        messages.success(
            request,
            (
                f"{tipo_entrada.nombre} - asiento "
                f"{asiento.codigo} fue agregado al carrito."
            ),
        )

        return redirect(
            "carrito_web:mi-carrito"
        )

    # ========================================================
    # EVENTO GENERAL / LIBRE
    # ========================================================

    item = ItemCarrito.objects.filter(
        carrito=carrito,
        tipo_entrada=tipo_entrada,
        asiento__isnull=True,
    ).first()

    if item is not None:

        nueva_cantidad = item.cantidad + 1

        if nueva_cantidad > tipo_entrada.stock_disponible:
            messages.warning(
                request,
                "No puedes agregar mas unidades. "
                "Has alcanzado el stock disponible.",
            )
            return redirect(
                "eventos:detalle",
                pk=evento.pk,
            )

        item.cantidad = nueva_cantidad
        item.full_clean()
        item.save(
            update_fields=[
                "cantidad",
                "actualizado_en",
            ]
        )

    else:

        item = ItemCarrito(
            carrito=carrito,
            tipo_entrada=tipo_entrada,
            asiento=None,
            cantidad=1,
        )

        item.full_clean()
        item.save()

    messages.success(
        request,
        f"{tipo_entrada.nombre} fue agregada al carrito.",
    )

    return redirect(
        "carrito_web:mi-carrito"
    )


# ============================================================
# PANEL WEB DEL ORGANIZADOR
# ============================================================

@login_required
def panel_organizador(request):
    """
    Panel privado para usuarios con rol ORGANIZADOR.

    Seguridad:
    - requiere autenticacion;
    - solo permite usuarios ORGANIZADOR;
    - cada organizador visualiza exclusivamente sus eventos;
    - no entrega acceso al panel tecnico de administracion.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para acceder al panel de organizador.",
        )

        return redirect(
            "eventos:inicio"
        )

    eventos = (
        Evento.objects
        .filter(
            organizador=request.user,
        )
        .select_related(
            "recinto",
        )
        .prefetch_related(
            "tipos_entrada",
        )
        .order_by(
            "-fecha_inicio"
        )
    )

    contexto = {
        "eventos": eventos,
    }

    return render(
        request,
        "eventos/panel_organizador.html",
        contexto,
    )






# ============================================================
# CREAR EVENTO - PANEL ORGANIZADOR
# ============================================================

@login_required
def nuevo_evento(request):
    """
    Permite al ORGANIZADOR crear un evento propio.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para crear eventos.",
        )
        return redirect("eventos:inicio")

    if request.method == "POST":
        form = EventoForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            evento = form.save(commit=False)
            evento.organizador = request.user
            evento.full_clean()
            evento.save()

            messages.success(
                request,
                "Evento creado correctamente.",
            )

            return redirect(
                "eventos:panel_organizador"
            )
    else:
        form = EventoForm()

    return render(
        request,
        "eventos/evento_form.html",
        {
            "form": form,
            "titulo": "Nuevo evento",
            "texto_boton": "CREAR EVENTO",
        },
    )


# ============================================================
# EDITAR EVENTO - PANEL ORGANIZADOR
# ============================================================

@login_required
def editar_evento(request, pk):
    """
    Permite al ORGANIZADOR editar exclusivamente
    uno de sus propios eventos.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar eventos.",
        )
        return redirect("eventos:inicio")

    evento = get_object_or_404(
        Evento,
        pk=pk,
        organizador=request.user,
    )

    if request.method == "POST":
        form = EventoForm(
            request.POST,
            request.FILES,
            instance=evento,
        )

        if form.is_valid():
            evento = form.save(commit=False)
            evento.organizador = request.user
            evento.full_clean()
            evento.save()

            messages.success(
                request,
                "Evento actualizado correctamente.",
            )

            return redirect(
                "eventos:panel_organizador"
            )
    else:
        form = EventoForm(
            instance=evento
        )

    return render(
        request,
        "eventos/evento_form.html",
        {
            "form": form,
            "evento": evento,
            "tipos_entrada": evento.tipos_entrada.all(),
            "titulo": "Gestionar evento",
            "texto_boton": "GUARDAR CAMBIOS",
        },
    )



# ============================================================
# CREAR TIPO DE ENTRADA - ORGANIZADOR
# ============================================================

@login_required
def nuevo_tipo_entrada(request, evento_pk):
    """
    Permite al ORGANIZADOR crear un tipo de entrada
    exclusivamente para uno de sus propios eventos.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar entradas.",
        )
        return redirect("eventos:inicio")

    evento = get_object_or_404(
        Evento,
        pk=evento_pk,
        organizador=request.user,
    )

    if request.method == "POST":
        form = TipoEntradaForm(request.POST)

        if form.is_valid():
            tipo_entrada = form.save(commit=False)
            tipo_entrada.evento = evento
            tipo_entrada.full_clean()
            tipo_entrada.save()

            messages.success(
                request,
                "Tipo de entrada creado correctamente.",
            )

            return redirect(
                "eventos:editar_evento",
                pk=evento.pk,
            )
    else:
        form = TipoEntradaForm()

    return render(
        request,
        "eventos/tipo_entrada_form.html",
        {
            "form": form,
            "evento": evento,
            "titulo": "Nuevo tipo de entrada",
            "texto_boton": "CREAR TIPO DE ENTRADA",
        },
    )


# ============================================================
# EDITAR TIPO DE ENTRADA - ORGANIZADOR
# ============================================================

@login_required
@require_POST
def eliminar_evento(request, pk):
    """
    Permite al ORGANIZADOR eliminar uno de sus eventos
    solamente cuando no posee compras asociadas.

    Si existe historial de compras, el evento se conserva
    para proteger la integridad de los datos.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para eliminar eventos.",
        )
        return redirect("eventos:inicio")

    evento = get_object_or_404(
        Evento,
        pk=pk,
        organizador=request.user,
    )

    tiene_compras = TipoEntrada.objects.filter(
        evento=evento,
        detalles_compra__isnull=False,
    ).exists()

    if tiene_compras:
        messages.error(
            request,
            (
                "No se puede eliminar este evento porque posee "
                "compras asociadas. Puedes cancelarlo o dejarlo "
                "inactivo para conservar el historial."
            ),
        )

        return redirect(
            "eventos:editar_evento",
            pk=evento.pk,
        )

    nombre_evento = evento.nombre

    evento.delete()

    messages.success(
        request,
        f'Evento "{nombre_evento}" eliminado correctamente.',
    )

    return redirect("eventos:panel_organizador")


@login_required
def editar_tipo_entrada(request, pk):
    """
    Permite al ORGANIZADOR editar un tipo de entrada
    perteneciente exclusivamente a uno de sus eventos.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar entradas.",
        )
        return redirect("eventos:inicio")

    tipo_entrada = get_object_or_404(
        TipoEntrada.objects.select_related("evento"),
        pk=pk,
        evento__organizador=request.user,
    )

    evento = tipo_entrada.evento

    if request.method == "POST":
        form = TipoEntradaForm(
            request.POST,
            instance=tipo_entrada,
        )

        if form.is_valid():
            tipo_entrada = form.save(commit=False)

            # El evento nunca se obtiene desde el formulario.
            tipo_entrada.evento = evento

            tipo_entrada.full_clean()
            tipo_entrada.save()

            messages.success(
                request,
                "Tipo de entrada actualizado correctamente.",
            )

            return redirect(
                "eventos:editar_evento",
                pk=evento.pk,
            )
    else:
        form = TipoEntradaForm(
            instance=tipo_entrada
        )

    return render(
        request,
        "eventos/tipo_entrada_form.html",
        {
            "form": form,
            "evento": evento,
            "tipo_entrada": tipo_entrada,
            "titulo": "Editar tipo de entrada",
            "texto_boton": "GUARDAR CAMBIOS",
        },
    )

# ============================================================
# ELIMINAR TIPO DE ENTRADA - ORGANIZADOR
# ============================================================

@login_required
@require_POST
def eliminar_tipo_entrada(request, pk):
    """
    Permite al ORGANIZADOR eliminar un tipo de entrada
    únicamente si pertenece a uno de sus eventos y no
    posee compras asociadas.

    Si existe historial de compra, el registro se conserva
    para mantener la integridad de los datos.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para eliminar entradas.",
        )
        return redirect("eventos:inicio")

    tipo_entrada = get_object_or_404(
        TipoEntrada.objects.select_related("evento"),
        pk=pk,
        evento__organizador=request.user,
    )

    evento = tipo_entrada.evento

    if tipo_entrada.detalles_compra.exists():
        messages.error(
            request,
            (
                "No se puede eliminar este tipo de entrada "
                "porque posee compras asociadas. "
                "Puedes dejarlo inactivo para impedir nuevas ventas."
            ),
        )

        return redirect(
            "eventos:editar_evento",
            pk=evento.pk,
        )

    nombre_tipo = tipo_entrada.nombre

    tipo_entrada.delete()

    messages.success(
        request,
        f'Tipo de entrada "{nombre_tipo}" eliminado correctamente.',
    )

    return redirect(
        "eventos:editar_evento",
        pk=evento.pk,
    )


# ============================================================
# CREAR RECINTO - PANEL ORGANIZADOR
# ============================================================

@login_required
def nuevo_recinto(request):
    """
    Permite al ORGANIZADOR crear un recinto desde
    su panel privado.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para crear recintos.",
        )
        return redirect("eventos:inicio")

    if request.method == "POST":
        form = RecintoForm(request.POST)

        if form.is_valid():
            recinto = form.save()

            messages.success(
                request,
                f'Recinto "{recinto.nombre}" creado correctamente.',
            )

            return redirect(
                "eventos:panel_organizador"
            )

    else:
        form = RecintoForm()

    return render(
        request,
        "eventos/recinto_form.html",
        {
            "form": form,
            "titulo": "Nuevo recinto",
            "texto_boton": "CREAR RECINTO",
        },
    )
