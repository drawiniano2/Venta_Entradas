from rest_framework.permissions import BasePermission

from .models import Usuario


class EsOrganizador(BasePermission):
    """
    Permite el acceso únicamente a usuarios autenticados
    cuyo rol sea ORGANIZADOR.
    """

    message = "Esta operación requiere un usuario con rol ORGANIZADOR."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.ORGANIZADOR
        )


class EsEspectador(BasePermission):
    """
    Permite el acceso únicamente a usuarios autenticados
    cuyo rol sea ESPECTADOR.
    """

    message = "Esta operación requiere un usuario con rol ESPECTADOR."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.ESPECTADOR
        )


class EsOrganizadorOEspectador(BasePermission):
    """
    Permite el acceso a cualquiera de los dos roles
    válidos del sistema.
    """

    message = "El usuario no posee un rol válido para esta operación."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol
            in (
                Usuario.Rol.ORGANIZADOR,
                Usuario.Rol.ESPECTADOR,
            )
        )
