from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import (
    AuthEstado, AuthUserEstado, AuthLogAccion,
    Cargo, Persona, UserCargo, UserSecure, AuditoriaPin
)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    """Admin para gestión de cargos."""
    list_display = ['codigo', 'nombre', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'eliminado', 'fecha_creacion']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    """Admin para gestión de personas."""
    list_display = ['documento_identidad', 'get_nombre_completo', 'user', 'activo']
    list_filter = ['activo', 'eliminado', 'sexo']
    search_fields = ['documento_identidad', 'nombres', 'apellido1', 'apellido2', 'user__username']
    ordering = ['apellido1', 'apellido2', 'nombres']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['user']


@admin.register(UserCargo)
class UserCargoAdmin(admin.ModelAdmin):
    """Admin para gestión de cargos de usuarios."""
    list_display = ['usuario', 'cargo', 'fecha_inicio', 'fecha_fin', 'es_actual', 'activo']
    list_filter = ['activo', 'eliminado', 'cargo', 'fecha_inicio']
    search_fields = ['usuario__username', 'cargo__nombre']
    ordering = ['-fecha_inicio']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['usuario', 'cargo']


@admin.register(UserSecure)
class UserSecureAdmin(admin.ModelAdmin):
    """Admin para gestión de seguridad de usuarios."""
    list_display = ['user', 'bloqueado', 'intentos_fallidos', 'activo']
    list_filter = ['bloqueado', 'activo', 'eliminado']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['pin', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['user']
    
    def has_add_permission(self, request):
        """No permitir crear UserSecure desde admin (se crea automáticamente)."""
        return False


@admin.register(AuditoriaPin)
class AuditoriaPinAdmin(admin.ModelAdmin):
    """Admin para auditoría de uso de PIN."""
    list_display = ['usuario', 'accion', 'exitoso', 'fecha_creacion', 'ip_address']
    list_filter = ['accion', 'exitoso', 'fecha_creacion']
    search_fields = ['usuario__username', 'ip_address']
    ordering = ['-fecha_creacion']
    readonly_fields = ['fecha_creacion']
    raw_id_fields = ['usuario']
    
    def has_add_permission(self, request):
        """No permitir crear registros de auditoría manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar registros de auditoría."""
        return False