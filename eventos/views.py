from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from carrito.models import Carrito, ItemCarrito
from compras.models import Compra

from .forms import EventoForm, LocacionForm, RecintoForm, TipoEntradaForm
from .models import Asiento, Evento, Locacion, TipoEntrada


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

    # ========================================================
    # MAPA PUBLICO UNIVERSAL DE LOCACIONES Y ASIENTOS
    #
    # Esta estructura sirve para TODOS los modelos de escenario:
    #
    # - FRONTAL_SIMPLE
    # - FRONTAL_TRIBUNAS
    # - CENTRAL
    # - SIN_ESCENARIO
    #
    # Cada locacion conserva su posicion fisica y sus asientos
    # se agrupan por fila para reproducir visualmente el mapa
    # utilizado por el organizador.
    # ========================================================

    locaciones_mapa = []

    for locacion in locaciones:

        filas_mapa = {}

        for asiento in locacion.asientos.all():

            asiento.vendido = (
                asiento.pk in asientos_vendidos
            )

            fila = asiento.fila or "SIN FILA"

            if fila not in filas_mapa:
                filas_mapa[fila] = {
                    "nombre": fila,
                    "asientos": [],
                }

            filas_mapa[fila]["asientos"].append(
                asiento
            )

        filas = list(
            filas_mapa.values()
        )


        locaciones_mapa.append(
            {
                "locacion": locacion,
                "filas": filas,
            }
        )

    # --------------------------------------------------------
    # Separacion fisica de las locaciones.
    #
    # detalle.html utilizara estas colecciones para construir
    # la geometria correspondiente al tipo de escenario.
    # --------------------------------------------------------

    locaciones_frontales = [
        item
        for item in locaciones_mapa
        if item["locacion"].posicion == "FRONTAL"
    ]

    locaciones_posteriores = [
        item
        for item in locaciones_mapa
        if item["locacion"].posicion == "POSTERIOR"
    ]

    locaciones_izquierdas = [
        item
        for item in locaciones_mapa
        if item["locacion"].posicion == "IZQUIERDA"
    ]

    locaciones_derechas = [
        item
        for item in locaciones_mapa
        if item["locacion"].posicion == "DERECHA"
    ]

    locaciones_libres = [
        item
        for item in locaciones_mapa
        if item["locacion"].posicion == "LIBRE"
    ]

    contexto = {
        "evento": evento,
        "tipos_entrada": tipos_entrada,

        # Se conserva por compatibilidad con la plantilla actual.
        "locaciones": locaciones,

        # Estructura universal del nuevo mapa publico.
        "locaciones_mapa": locaciones_mapa,
        "locaciones_frontales": locaciones_frontales,
        "locaciones_posteriores": locaciones_posteriores,
        "locaciones_izquierdas": locaciones_izquierdas,
        "locaciones_derechas": locaciones_derechas,
        "locaciones_libres": locaciones_libres,

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

    # ========================================================
    # CAPACIDAD DE ASIENTOS PARA EDITAR EVENTO
    # ========================================================

    tipos_entrada = list(
        evento.tipos_entrada.all()
    )

    capacidad_total_evento = 0
    asientos_asignados_evento = 0

    for tipo in tipos_entrada:

        asientos_asignados_mapa = (
            Asiento.objects
            .filter(
                locacion__evento=evento,
                locacion__tipo_entrada=tipo,
                activo=True,
            )
            .count()
        )

        tipo.asientos_asignados_mapa = (
            asientos_asignados_mapa
        )

        tipo.capacidad_restante_mapa = max(
            tipo.stock_total
            - asientos_asignados_mapa,
            0,
        )

        capacidad_total_evento += tipo.stock_total
        asientos_asignados_evento += (
            asientos_asignados_mapa
        )

    capacidad_restante_evento = max(
        capacidad_total_evento
        - asientos_asignados_evento,
        0,
    )

    capacidad_completa_evento = (
        capacidad_total_evento > 0
        and capacidad_restante_evento == 0
    )

    return render(
        request,
        "eventos/evento_form.html",
        {
            "form": form,
            "evento": evento,
            "tipos_entrada": tipos_entrada,

            "capacidad_total_evento":
                capacidad_total_evento,

            "asientos_asignados_evento":
                asientos_asignados_evento,

            "capacidad_restante_evento":
                capacidad_restante_evento,

            "capacidad_completa_evento":
                capacidad_completa_evento,

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

        url_editar = reverse(
            "eventos:editar_evento",
            kwargs={
                "pk": evento.pk,
            },
        )

        return redirect(
            f"{url_editar}#generador-locaciones"
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
# GENERAR LOCACION Y ASIENTOS - ORGANIZADOR
# ============================================================

@login_required
@require_POST
def generar_locacion_asientos(request, evento_pk):
    """
    Crea una locacion para un evento con modalidad UBICACION
    y genera automaticamente sus asientos por filas.

    Ejemplo:
    fila inicial A + 3 filas + 4 asientos por fila genera:
    A1, A2, A3, A4
    B1, B2, B3, B4
    C1, C2, C3, C4
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar ubicaciones.",
        )
        return redirect("eventos:inicio")

    evento = get_object_or_404(
        Evento,
        pk=evento_pk,
        organizador=request.user,
    )

    # ========================================================
    # DESTINO DE RETORNO
    #
    # Si la locacion se crea desde el mapa, regresamos al mapa.
    # Si se crea desde Editar evento, conservamos el flujo
    # original y regresamos a Editar evento.
    # ========================================================

    volver_al_mapa = (
        request.POST.get(
            "volver_al_mapa",
            "",
        ).strip()
        == "1"
    )

    def volver_generador():
        """
        Regresa al lugar desde donde se solicito crear
        la locacion.
        """

        if volver_al_mapa:
            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

        url_editar = reverse(
            "eventos:editar_evento",
            kwargs={
                "pk": evento.pk,
            },
        )

        return redirect(
            f"{url_editar}#generador-locaciones"
        )

    if evento.modalidad_entrada != Evento.ModalidadEntrada.UBICACION:
        messages.error(
            request,
            (
                "Este evento no utiliza entradas con ubicacion. "
                "Debes configurar la modalidad correspondiente."
            ),
        )
        return volver_generador()

    nombre = request.POST.get(
        "nombre_locacion",
        "",
    ).strip()

    tipo_entrada_id = request.POST.get(
        "tipo_entrada",
        "",
    ).strip()

    posicion = request.POST.get(
        "posicion",
        "",
    ).strip().upper()

    fila_inicial = request.POST.get(
        "fila_inicial",
        "A",
    ).strip().upper()

    cantidad_filas_texto = request.POST.get(
        "cantidad_filas",
        "",
    ).strip()

    asientos_por_fila_texto = request.POST.get(
        "asientos_por_fila",
        "",
    ).strip()

    if not nombre:
        messages.error(
            request,
            "Debes indicar el nombre de la locacion.",
        )
        return volver_generador()

    if not tipo_entrada_id:
        messages.error(
            request,
            "Debes seleccionar un tipo de entrada.",
        )
        return volver_generador()

    posiciones_validas = {
        valor
        for valor, etiqueta in Locacion.Posicion.choices
    }

    if posicion not in posiciones_validas:
        messages.error(
            request,
            "Debes seleccionar una posicion valida para la locacion.",
        )
        return volver_generador()

    tipo_entrada = get_object_or_404(
        TipoEntrada,
        pk=tipo_entrada_id,
        evento=evento,
    )

    if Locacion.objects.filter(
        evento=evento,
        nombre__iexact=nombre,
    ).exists():
        messages.error(
            request,
            f'Ya existe una locacion llamada "{nombre}" en este evento.',
        )
        return volver_generador()

    if (
        len(fila_inicial) != 1
        or not fila_inicial.isalpha()
        or not fila_inicial.isascii()
    ):
        messages.error(
            request,
            "La fila inicial debe ser una letra entre A y Z.",
        )
        return volver_generador()

    try:
        cantidad_filas = int(cantidad_filas_texto)
        asientos_por_fila = int(asientos_por_fila_texto)

    except ValueError:
        messages.error(
            request,
            "La cantidad de filas y asientos debe ser numerica.",
        )
        return volver_generador()

    if cantidad_filas < 1 or cantidad_filas > 26:
        messages.error(
            request,
            "La cantidad de filas debe estar entre 1 y 26.",
        )
        return volver_generador()

    if asientos_por_fila < 1 or asientos_por_fila > 200:
        messages.error(
            request,
            "Los asientos por fila deben estar entre 1 y 200.",
        )
        return volver_generador()

    codigo_fila_inicial = ord(fila_inicial)

    if codigo_fila_inicial + cantidad_filas - 1 > ord("Z"):
        messages.error(
            request,
            "La cantidad de filas supera la letra Z.",
        )
        return volver_generador()

    total_asientos = cantidad_filas * asientos_por_fila

    # El stock configurado para este tipo de entrada debe poder
    # representar todos los asientos fisicos que se generaran.
    asientos_existentes_tipo = Asiento.objects.filter(
        locacion__evento=evento,
        locacion__tipo_entrada=tipo_entrada,
        activo=True,
    ).count()

    total_asientos_tipo = (
        asientos_existentes_tipo
        + total_asientos
    )

    if total_asientos_tipo > tipo_entrada.stock_total:
        messages.error(
            request,
            (
                f'No se pueden generar {total_asientos} asientos. '
                f'El tipo de entrada "{tipo_entrada.nombre}" tiene '
                f'stock total {tipo_entrada.stock_total} y quedaria '
                f'asociado a {total_asientos_tipo} asientos.'
            ),
        )
        return volver_generador()

    with transaction.atomic():

        orden = (
            Locacion.objects
            .filter(evento=evento)
            .count()
            + 1
        )

        locacion = Locacion(
            evento=evento,
            tipo_entrada=tipo_entrada,
            nombre=nombre,
            posicion=posicion,
            descripcion=(
                f"{cantidad_filas} filas, "
                f"{asientos_por_fila} asientos por fila."
            ),
            orden=orden,
            activo=True,
        )

        locacion.full_clean()
        locacion.save()

        asientos = []

        for indice_fila in range(cantidad_filas):

            fila = chr(
                codigo_fila_inicial
                + indice_fila
            )

            for numero in range(
                1,
                asientos_por_fila + 1,
            ):
                asientos.append(
                    Asiento(
                        locacion=locacion,
                        codigo=f"{fila}{numero}",
                        fila=fila,
                        numero=numero,
                        activo=True,
                    )
                )

        Asiento.objects.bulk_create(
            asientos
        )

    messages.success(
        request,
        (
            f'Locacion "{nombre}" creada correctamente con '
            f'{total_asientos} asientos.'
        ),
    )

    return volver_generador()



# ============================================================
# PANEL DE LOCACIONES Y ASIENTOS - ORGANIZADOR
# ============================================================

@login_required
def panel_asientos(request, evento_pk):
    """
    Muestra al organizador el mapa de locaciones y asientos
    de uno de sus propios eventos.

    Un asiento se considera vendido cuando existe un
    DetalleCompra asociado a una Compra PAGADA.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar asientos.",
        )
        return redirect("eventos:inicio")

    evento = get_object_or_404(
        Evento.objects.select_related(
            "recinto",
            "organizador",
        ),
        pk=evento_pk,
        organizador=request.user,
    )

    if (
        evento.modalidad_entrada
        != Evento.ModalidadEntrada.UBICACION
    ):
        messages.error(
            request,
            "Este evento no utiliza entradas con ubicacion.",
        )
        return redirect(
            "eventos:editar_evento",
            pk=evento.pk,
        )

    locaciones = (
        Locacion.objects
        .filter(
            evento=evento,
            activo=True,
        )
        .select_related(
            "tipo_entrada",
        )
        .prefetch_related(
            "asientos",
        )
        .order_by(
            "orden",
            "nombre",
        )
    )

    locaciones_panel = []

    for locacion in locaciones:

        asientos_panel = []
        filas_panel = {}

        vendidos = 0
        disponibles = 0
        inactivos = 0

        for asiento in locacion.asientos.all():

            vendido = asiento.detalles_compra.filter(
                compra__estado=Compra.Estado.PAGADO,
            ).exists()

            if vendido:
                estado = "VENDIDO"
                vendidos += 1

            elif not asiento.activo:
                estado = "INACTIVO"
                inactivos += 1

            else:
                estado = "DISPONIBLE"
                disponibles += 1

            dato_asiento = {
                "asiento": asiento,
                "estado": estado,
            }

            asientos_panel.append(
                dato_asiento
            )

            # Agrupar los asientos por su fila fisica.
            fila = asiento.fila or "SIN FILA"

            if fila not in filas_panel:
                filas_panel[fila] = {
                    "nombre": fila,
                    "asientos": [],
                    "total": 0,
                    "vendidos": 0,
                    "disponibles": 0,
                    "inactivos": 0,
                }

            filas_panel[fila]["asientos"].append(
                dato_asiento
            )

            filas_panel[fila]["total"] += 1

            if estado == "VENDIDO":
                filas_panel[fila]["vendidos"] += 1

            elif estado == "INACTIVO":
                filas_panel[fila]["inactivos"] += 1

            else:
                filas_panel[fila]["disponibles"] += 1

        filas = list(
            filas_panel.values()
        )

        locaciones_panel.append(
            {
                "locacion": locacion,
                "asientos": asientos_panel,
                "filas": filas,
                "total": len(asientos_panel),
                "vendidos": vendidos,
                "disponibles": disponibles,
                "inactivos": inactivos,
            }
        )

    # ========================================================
    # DISTRIBUCION FISICA DE LOCACIONES EN EL MAPA
    # ========================================================

    locaciones_frontales = []
    locaciones_posteriores = []
    locaciones_izquierdas = []
    locaciones_derechas = []
    locaciones_libres = []

    for item in locaciones_panel:

        posicion = item["locacion"].posicion

        if posicion == Locacion.Posicion.POSTERIOR:
            locaciones_posteriores.append(item)

        elif posicion == Locacion.Posicion.IZQUIERDA:
            locaciones_izquierdas.append(item)

        elif posicion == Locacion.Posicion.DERECHA:
            locaciones_derechas.append(item)

        elif posicion == Locacion.Posicion.LIBRE:
            locaciones_libres.append(item)

        else:
            locaciones_frontales.append(item)

    # ========================================================
    # TIPOS DE ENTRADA ACTIVOS
    # PARA CREAR LOCACIONES DIRECTAMENTE DESDE EL MAPA
    # ========================================================

    tipos_entrada = list(
        TipoEntrada.objects
        .filter(
            evento=evento,
            activo=True,
        )
        .order_by("nombre")
    )

    # ========================================================
    # CAPACIDAD FISICA RESTANTE POR TIPO DE ENTRADA
    #
    # stock_total = capacidad total configurada.
    # asientos asignados = asientos fisicos activos que ya
    # pertenecen a locaciones de este evento y tipo.
    #
    # Esta capacidad se utiliza solamente para construir
    # nuevas locaciones en el mapa.
    # ========================================================

    for tipo in tipos_entrada:

        asientos_asignados_mapa = (
            Asiento.objects
            .filter(
                locacion__evento=evento,
                locacion__tipo_entrada=tipo,
                activo=True,
            )
            .count()
        )

        tipo.asientos_asignados_mapa = (
            asientos_asignados_mapa
        )

        tipo.capacidad_restante_mapa = max(
            tipo.stock_total
            - asientos_asignados_mapa,
            0,
        )

    return render(
        request,
        "eventos/panel_asientos.html",
        {
            "evento": evento,
            "locaciones_panel": locaciones_panel,
            "locaciones_frontales": locaciones_frontales,
            "locaciones_posteriores": locaciones_posteriores,
            "locaciones_izquierdas": locaciones_izquierdas,
            "locaciones_derechas": locaciones_derechas,
            "locaciones_libres": locaciones_libres,
            "tipos_entrada": tipos_entrada,
        },
    )




# ============================================================
# MODIFICAR CANTIDAD DE ASIENTOS DE UNA FILA - ORGANIZADOR
# ============================================================

@login_required
@require_POST
def modificar_fila_asientos(request, locacion_pk, fila):
    """
    Permite agregar o quitar un asiento al final de una fila.

    Reglas:
    - Solo el organizador propietario puede modificarla.
    - Nunca se elimina un asiento vendido.
    - Al agregar un asiento aumenta el stock total y disponible.
    - Al quitar un asiento libre disminuye el stock total y
      disponible.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar asientos.",
        )
        return redirect("eventos:inicio")

    locacion = get_object_or_404(
        Locacion.objects.select_related(
            "evento",
            "evento__organizador",
            "tipo_entrada",
        ),
        pk=locacion_pk,
        evento__organizador=request.user,
    )

    evento = locacion.evento
    tipo_entrada = locacion.tipo_entrada
    fila = fila.upper().strip()

    if not tipo_entrada:
        messages.error(
            request,
            "La locacion no tiene un tipo de entrada asociado.",
        )
        return redirect(
            "eventos:panel_asientos",
            evento_pk=evento.pk,
        )

    accion = request.POST.get("accion")

    # ========================================================
    # AGREGAR UN ASIENTO AL FINAL DE LA FILA
    # ========================================================

    if accion == "agregar":

        asientos_fila = (
            Asiento.objects
            .filter(
                locacion=locacion,
                fila=fila,
            )
            .order_by("numero")
        )

        ultimo_numero = 0

        for asiento in asientos_fila:
            if (
                asiento.numero is not None
                and asiento.numero > ultimo_numero
            ):
                ultimo_numero = asiento.numero

        nuevo_numero = ultimo_numero + 1
        nuevo_codigo = f"{fila}{nuevo_numero}"

        with transaction.atomic():

            Asiento.objects.create(
                locacion=locacion,
                codigo=nuevo_codigo,
                fila=fila,
                numero=nuevo_numero,
                activo=True,
            )

            tipo_entrada.stock_total += 1
            tipo_entrada.stock_disponible += 1

            tipo_entrada.full_clean()

            tipo_entrada.save(
                update_fields=[
                    "stock_total",
                    "stock_disponible",
                ]
            )

        messages.success(
            request,
            (
                f"Asiento {nuevo_codigo} agregado "
                f"correctamente a la fila {fila}."
            ),
        )

    # ========================================================
    # QUITAR EL ULTIMO ASIENTO LIBRE DE LA FILA
    # ========================================================

    elif accion == "quitar":

        # ----------------------------------------------------
        # Buscar desde el final de la fila el ultimo asiento
        # que NO tenga una compra PAGADA asociada.
        #
        # Los asientos vendidos nunca se eliminan.
        # ----------------------------------------------------

        asientos_fila = (
            Asiento.objects
            .filter(
                locacion=locacion,
                fila=fila,
            )
            .order_by("-numero")
        )

        if not asientos_fila.exists():
            messages.error(
                request,
                f"La fila {fila} no tiene asientos para quitar.",
            )

            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

        ultimo_asiento = None

        for asiento in asientos_fila:

            vendido = asiento.detalles_compra.filter(
                compra__estado=Compra.Estado.PAGADO,
            ).exists()

            if not vendido:
                ultimo_asiento = asiento
                break

        if ultimo_asiento is None:
            messages.error(
                request,
                (
                    f"No se puede reducir la fila {fila}. "
                    f"Todos sus asientos estan vendidos."
                ),
            )

            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

        if tipo_entrada.stock_total <= 0:
            messages.error(
                request,
                "El stock total no permite quitar mas asientos.",
            )

            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

        if tipo_entrada.stock_disponible <= 0:
            messages.error(
                request,
                "No existe stock disponible para descontar.",
            )

            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

        codigo_eliminado = ultimo_asiento.codigo

        with transaction.atomic():

            ultimo_asiento.delete()

            tipo_entrada.stock_total -= 1
            tipo_entrada.stock_disponible -= 1

            tipo_entrada.full_clean()

            tipo_entrada.save(
                update_fields=[
                    "stock_total",
                    "stock_disponible",
                ]
            )

        messages.success(
            request,
            (
                f"Asiento {codigo_eliminado} eliminado "
                f"correctamente de la fila {fila}."
            ),
        )

    else:

        messages.error(
            request,
            "Operacion de fila no reconocida.",
        )

    return redirect(
        "eventos:panel_asientos",
        evento_pk=evento.pk,
    )


# ============================================================
# EDITAR LOCACION - ORGANIZADOR
# ============================================================

@login_required
def editar_locacion(request, pk):
    """
    Permite al organizador:

    1. Editar los datos generales de una locacion.
    2. Ampliar su capacidad agregando nuevas filas.

    Los asientos existentes nunca se eliminan ni se renumeran.
    """

    if request.user.rol != "ORGANIZADOR":
        messages.error(
            request,
            "No tienes permisos para gestionar locaciones.",
        )
        return redirect("eventos:inicio")

    locacion = get_object_or_404(
        Locacion.objects.select_related(
            "evento",
            "evento__organizador",
            "tipo_entrada",
        ),
        pk=pk,
        evento__organizador=request.user,
    )

    evento = locacion.evento

    # ========================================================
    # ACCION SOLICITADA
    #
    # Permite distinguir entre:
    # - guardar datos generales
    # - ampliar filas
    # - reducir filas
    # ========================================================

    accion = request.POST.get(
        "accion",
        "",
    ).strip()

    # ========================================================
    # AMPLIAR CAPACIDAD
    # ========================================================

    if (
        request.method == "POST"
        and request.POST.get("accion") == "ampliar"
    ):

        filas_nuevas_texto = request.POST.get(
            "filas_nuevas",
            "",
        ).strip()

        asientos_por_fila_texto = request.POST.get(
            "asientos_por_fila",
            "",
        ).strip()

        try:
            filas_nuevas = int(filas_nuevas_texto)
            asientos_por_fila = int(
                asientos_por_fila_texto
            )

        except ValueError:
            messages.error(
                request,
                (
                    "La cantidad de filas y los asientos "
                    "por fila deben ser numeros enteros."
                ),
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        if filas_nuevas < 1 or filas_nuevas > 26:
            messages.error(
                request,
                "Las filas nuevas deben estar entre 1 y 26.",
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        if (
            asientos_por_fila < 1
            or asientos_por_fila > 200
        ):
            messages.error(
                request,
                (
                    "Los asientos por fila deben estar "
                    "entre 1 y 200."
                ),
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        # ----------------------------------------------------
        # Determinar la ultima fila alfabetica existente.
        # ----------------------------------------------------

        filas_existentes = list(
            locacion.asientos
            .exclude(fila="")
            .values_list(
                "fila",
                flat=True,
            )
            .distinct()
        )

        filas_validas = [
            fila.upper()
            for fila in filas_existentes
            if (
                len(fila) == 1
                and fila.isascii()
                and fila.isalpha()
            )
        ]

        if filas_validas:
            ultima_fila = max(filas_validas)
            codigo_inicio = ord(ultima_fila) + 1

        else:
            ultima_fila = None
            codigo_inicio = ord("A")

        codigo_final = (
            codigo_inicio
            + filas_nuevas
            - 1
        )

        if codigo_final > ord("Z"):
            messages.error(
                request,
                (
                    "No se pueden agregar esas filas porque "
                    "la numeracion superaria la fila Z."
                ),
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        nuevos_asientos_total = (
            filas_nuevas
            * asientos_por_fila
        )

        # ----------------------------------------------------
        # El tipo de entrada debe existir.
        # ----------------------------------------------------

        tipo_entrada = locacion.tipo_entrada

        if tipo_entrada is None:
            messages.error(
                request,
                (
                    "La locacion debe tener un tipo de "
                    "entrada asociado antes de ampliar "
                    "su capacidad."
                ),
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        # ----------------------------------------------------
        # Comprobar capacidad contra stock_total.
        #
        # Se consideran TODOS los asientos activos asociados
        # al mismo tipo de entrada dentro del evento.
        # ----------------------------------------------------

        asientos_tipo = Asiento.objects.filter(
            locacion__evento=evento,
            locacion__tipo_entrada=tipo_entrada,
            activo=True,
        ).count()

        capacidad_resultante = (
            asientos_tipo
            + nuevos_asientos_total
        )

        # ----------------------------------------------------
        # Sincronizar capacidad fisica y stock.
        #
        # Al agregar nuevos asientos fisicos se aumenta en la
        # misma cantidad el stock total y el stock disponible.
        #
        # De esta manera las entradas ya vendidas permanecen
        # intactas.
        #
        # Ejemplo:
        # stock_total = 10
        # stock_disponible = 9
        # vendidos = 1
        #
        # +5 asientos:
        # stock_total = 15
        # stock_disponible = 14
        # vendidos = 1
        # ----------------------------------------------------

        aumento_stock = 0

        if capacidad_resultante > tipo_entrada.stock_total:
            aumento_stock = (
                capacidad_resultante
                - tipo_entrada.stock_total
            )

        # ----------------------------------------------------
        # Crear solamente las nuevas filas.
        # Los asientos anteriores permanecen intactos.
        # ----------------------------------------------------

        nuevos_asientos = []

        for indice_fila in range(filas_nuevas):

            fila = chr(
                codigo_inicio
                + indice_fila
            )

            for numero in range(
                1,
                asientos_por_fila + 1,
            ):

                nuevos_asientos.append(
                    Asiento(
                        locacion=locacion,
                        codigo=f"{fila}{numero}",
                        fila=fila,
                        numero=numero,
                        activo=True,
                    )
                )

        with transaction.atomic():

            Asiento.objects.bulk_create(
                nuevos_asientos
            )

            if aumento_stock > 0:

                tipo_entrada.stock_total += aumento_stock
                tipo_entrada.stock_disponible += aumento_stock

                tipo_entrada.full_clean()

                tipo_entrada.save(
                    update_fields=[
                        "stock_total",
                        "stock_disponible",
                    ]
                )

        primera_fila_nueva = chr(
            codigo_inicio
        )

        ultima_fila_nueva = chr(
            codigo_final
        )

        messages.success(
            request,
            (
                f'Locacion "{locacion.nombre}" ampliada '
                f"correctamente. Se agregaron "
                f"{nuevos_asientos_total} asientos "
                f"desde la fila {primera_fila_nueva} "
                f"hasta la fila {ultima_fila_nueva}."
            ),
        )

        return redirect(
            "eventos:panel_asientos",
            evento_pk=evento.pk,
        )

    # ========================================================
    # REDUCIR FILAS COMPLETAS DE LA LOCACION
    # FUNCION GENERAL PARA TODOS LOS TIPOS DE ESCENARIO
    # ========================================================

    if (
        request.method == "POST"
        and accion == "reducir_filas"
    ):

        try:
            filas_eliminar = int(
                request.POST.get(
                    "filas_eliminar",
                    "0",
                )
            )
        except (TypeError, ValueError):
            filas_eliminar = 0

        if filas_eliminar <= 0:
            messages.error(
                request,
                "Debes indicar una cantidad valida de filas a eliminar.",
            )
            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        # Obtener las filas existentes de la locacion.
        filas_existentes = list(
            locacion.asientos
            .exclude(fila="")
            .values_list(
                "fila",
                flat=True,
            )
            .distinct()
        )

        filas_validas = sorted(
            {
                fila.upper()
                for fila in filas_existentes
                if (
                    len(fila) == 1
                    and fila.isascii()
                    and fila.isalpha()
                )
            }
        )

        if not filas_validas:
            messages.error(
                request,
                "Esta locacion no posee filas que puedan eliminarse.",
            )
            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        # Dejamos siempre al menos una fila.
        if filas_eliminar >= len(filas_validas):
            messages.error(
                request,
                (
                    "No puedes eliminar todas las filas. "
                    "Debe permanecer al menos una fila."
                ),
            )
            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        # Se eliminan siempre las ultimas filas.
        #
        # A B C D E
        # eliminar 2 -> D E
        filas_objetivo = filas_validas[
            -filas_eliminar:
        ]

        asientos_objetivo = (
            locacion.asientos
            .filter(
                fila__in=filas_objetivo,
            )
        )

        # No permitir eliminar filas con entradas vendidas.
        vendidos_objetivo = (
            asientos_objetivo
            .filter(
                detalles_compra__compra__estado=Compra.Estado.PAGADO,
            )
            .distinct()
        )

        if vendidos_objetivo.exists():

            filas_con_ventas = sorted(
                set(
                    vendidos_objetivo.values_list(
                        "fila",
                        flat=True,
                    )
                )
            )

            messages.error(
                request,
                (
                    "No se pueden eliminar las filas "
                    f"{', '.join(filas_con_ventas)} porque "
                    "contienen asientos vendidos."
                ),
            )

            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        cantidad_eliminar = (
            asientos_objetivo.count()
        )

        if cantidad_eliminar <= 0:
            messages.error(
                request,
                "No se encontraron asientos para eliminar.",
            )
            return redirect(
                "eventos:editar_locacion",
                pk=locacion.pk,
            )

        tipo_entrada = locacion.tipo_entrada

        # Eliminar asientos y ajustar el stock.
        with transaction.atomic():

            asientos_objetivo.delete()

            tipo_entrada.stock_total = max(
                0,
                tipo_entrada.stock_total
                - cantidad_eliminar,
            )

            tipo_entrada.stock_disponible = max(
                0,
                tipo_entrada.stock_disponible
                - cantidad_eliminar,
            )

            tipo_entrada.full_clean()

            tipo_entrada.save(
                update_fields=[
                    "stock_total",
                    "stock_disponible",
                ]
            )

        messages.success(
            request,
            (
                f'Locacion "{locacion.nombre}" reducida correctamente. '
                f"Se eliminaron {filas_eliminar} fila(s): "
                f"{', '.join(filas_objetivo)}. "
                f"Total retirado: {cantidad_eliminar} asientos."
            ),
        )

        return redirect(
            "eventos:panel_asientos",
            evento_pk=evento.pk,
        )

    # ========================================================
    # EDITAR DATOS GENERALES
    # ========================================================

    if request.method == "POST":

        form = LocacionForm(
            request.POST,
            instance=locacion,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                (
                    f'Locacion "{locacion.nombre}" '
                    f"actualizada correctamente."
                ),
            )

            return redirect(
                "eventos:panel_asientos",
                evento_pk=evento.pk,
            )

    else:
        form = LocacionForm(
            instance=locacion,
        )

    # ========================================================
    # INFORMACION DE CAPACIDAD PARA EL TEMPLATE
    # ========================================================

    asientos_locacion = locacion.asientos.all()

    total_asientos = asientos_locacion.count()

    filas_actuales = list(
        asientos_locacion
        .exclude(fila="")
        .values_list(
            "fila",
            flat=True,
        )
        .distinct()
    )

    filas_actuales_validas = sorted(
        {
            fila.upper()
            for fila in filas_actuales
            if (
                len(fila) == 1
                and fila.isascii()
                and fila.isalpha()
            )
        }
    )

    cantidad_filas_actuales = len(
        filas_actuales_validas
    )

    ultima_fila = (
        filas_actuales_validas[-1]
        if filas_actuales_validas
        else "-"
    )

    vendidos = asientos_locacion.filter(
        detalles_compra__compra__estado=Compra.Estado.PAGADO,
    ).distinct().count()

    disponibles = asientos_locacion.filter(
        activo=True,
    ).exclude(
        detalles_compra__compra__estado=Compra.Estado.PAGADO,
    ).distinct().count()

    return render(
        request,
        "eventos/locacion_form.html",
        {
            "form": form,
            "locacion": locacion,
            "evento": evento,
            "total_asientos": total_asientos,
            "cantidad_filas_actuales": (
                cantidad_filas_actuales
            ),
            "ultima_fila": ultima_fila,
            "vendidos": vendidos,
            "disponibles": disponibles,
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

            volver = request.POST.get(
                "volver",
                "",
            ).strip()

            if volver == "evento":
                return redirect(
                    "eventos:nuevo_evento"
                )

            return redirect(
                "eventos:panel_organizador"
            )

    else:
        form = RecintoForm()

    volver = request.GET.get(
        "volver",
        "",
    ).strip()

    return render(
        request,
        "eventos/recinto_form.html",
        {
            "form": form,
            "titulo": "Nuevo recinto",
            "texto_boton": "CREAR RECINTO",
            "volver": volver,
        },
    )
