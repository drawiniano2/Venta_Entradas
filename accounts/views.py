from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse
from rest_framework_simplejwt.views import TokenObtainPairView

from .forms import RegistroUsuarioForm
from .models import Usuario
from .serializers import CustomTokenObtainPairSerializer


# ============================================================
# AUTENTICACION API - JWT
# ============================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de autenticacion JWT de la API.

    Valida las credenciales del usuario y devuelve:
    - access token
    - refresh token
    - informacion basica del usuario

    El token incluye el rol ESPECTADOR u ORGANIZADOR
    como claim personalizado.
    """

    serializer_class = CustomTokenObtainPairSerializer


# ============================================================
# AUTENTICACION WEB - SESION DJANGO
# ============================================================

def registro_web(request):
    """
    Registra un nuevo usuario desde la interfaz web.

    Reglas:
    - Solo permite registrar usuarios ESPECTADOR.
    - El rol es asignado por el formulario desde el servidor.
    - Utiliza las validaciones de contraseña de Django.
    - Después del registro inicia sesión automáticamente.
    """

    if request.user.is_authenticated:
        return redirect("eventos:inicio")

    if request.method == "POST":
        formulario = RegistroUsuarioForm(
            request.POST,
        )

        if formulario.is_valid():
            usuario = formulario.save()

            login(
                request,
                usuario,
            )

            messages.success(
                request,
                (
                    "Cuenta creada correctamente. "
                    f"Bienvenido, {usuario.username}."
                ),
            )

            return redirect(
                "eventos:inicio"
            )

    else:
        formulario = RegistroUsuarioForm()

    contexto = {
        "formulario": formulario,
    }

    return render(
        request,
        "accounts/registro.html",
        contexto,
    )


def login_web(request):
    """
    Inicia una sesion web utilizando el mismo Usuario
    personalizado utilizado por la API JWT.

    JWT continua siendo el mecanismo de autenticacion
    de la API. Esta vista se utiliza solamente para
    la interfaz HTML del sitio.
    """

    if request.user.is_authenticated:
        return redirect("eventos:inicio")

    siguiente = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        formulario = AuthenticationForm(
            request=request,
            data=request.POST,
        )

        if formulario.is_valid():
            usuario = formulario.get_user()

            login(
                request,
                usuario,
            )

            messages.success(
                request,
                f"Bienvenido, {usuario.username}.",
            )

            if siguiente:
                return redirect(siguiente)

            return redirect("eventos:inicio")

    else:
        formulario = AuthenticationForm(
            request=request,
        )

    contexto = {
        "formulario": formulario,
        "next": siguiente,
    }

    return render(
        request,
        "accounts/login.html",
        contexto,
    )


def logout_web(request):
    """
    Cierra exclusivamente la sesion web Django.
    """

    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "Sesion cerrada correctamente.",
        )

    return redirect("eventos:inicio")




# ============================================================
# GESTION DE USUARIOS - ADMINISTRADOR
# ============================================================

@login_required
def gestion_usuarios(request):
    """
    Muestra los usuarios registrados para que exclusivamente
    un administrador pueda revisar y administrar sus roles.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes permisos para acceder a la gesti?n de usuarios.",
        )
        return redirect("eventos:inicio")

    usuarios = (
        Usuario.objects
        .all()
        .order_by("username")
    )

    return render(
        request,
        "accounts/gestion_usuarios.html",
        {
            "usuarios": usuarios,
        },
    )


# ============================================================
# CAMBIAR ROL DE USUARIO - ADMINISTRADOR
# ============================================================

@login_required
@require_POST
def cambiar_rol_usuario(request, pk):
    """
    Permite exclusivamente a un administrador cambiar el rol
    entre ESPECTADOR y ORGANIZADOR.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes permisos para modificar roles.",
        )
        return redirect("eventos:inicio")

    usuario = get_object_or_404(
        Usuario,
        pk=pk,
    )

    # No permitimos modificar desde esta pantalla
    # una cuenta administrativa.
    if usuario.is_staff or usuario.is_superuser:
        messages.error(
            request,
            "No se puede modificar el rol de un administrador desde esta pantalla.",
        )
        return redirect("accounts_web:gestion_usuarios")

    nuevo_rol = request.POST.get("rol")

    roles_validos = {
        Usuario.Rol.ESPECTADOR,
        Usuario.Rol.ORGANIZADOR,
    }

    if nuevo_rol not in roles_validos:
        messages.error(
            request,
            "El rol solicitado no es válido.",
        )
        return redirect("accounts_web:gestion_usuarios")

    rol_anterior = usuario.rol

    if rol_anterior == nuevo_rol:
        messages.info(
            request,
            f'{usuario.username} ya tiene el rol {usuario.get_rol_display()}.',
        )
        return redirect("accounts_web:gestion_usuarios")

    usuario.rol = nuevo_rol
    usuario.save(update_fields=["rol"])

    messages.success(
        request,
        (
            f'Rol de "{usuario.username}" actualizado: '
            f'{rol_anterior} → {nuevo_rol}.'
        ),
    )

    return redirect("accounts_web:gestion_usuarios")


# ============================================================
# ELIMINAR USUARIO - ADMINISTRADOR
# ============================================================

@login_required
@require_POST
def eliminar_usuario(request, pk):
    """
    Permite exclusivamente a un administrador eliminar una
    cuenta que no tenga informaci?n hist?rica protegida.

    Las cuentas administrativas no pueden eliminarse.
    Las relaciones PROTECT de compras y eventos impiden borrar
    usuarios que posean informaci?n que deba conservarse.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes permisos para eliminar usuarios.",
        )
        return redirect("eventos:inicio")

    usuario = get_object_or_404(
        Usuario,
        pk=pk,
    )

    # Nunca permitimos eliminar cuentas administrativas.
    if usuario.is_staff or usuario.is_superuser:
        messages.error(
            request,
            "No se puede eliminar una cuenta administrativa.",
        )
        return redirect("accounts_web:gestion_usuarios")

    username = usuario.username

    try:
        usuario.delete()

    except ProtectedError:
        messages.error(
            request,
            (
                f'No se puede eliminar "{username}" porque tiene '
                "compras o eventos asociados que deben conservarse."
            ),
        )

        return redirect("accounts_web:gestion_usuarios")

    messages.success(
        request,
        f'Usuario "{username}" eliminado correctamente.',
    )

    return redirect("accounts_web:gestion_usuarios")

