from django.contrib import admin
from apps.auditoria.models import RegistroAuditoria, AuditoriaSesion


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'accion', 'content_type', 'object_id', 'usuario', 'ip_address']
    list_filter = ['accion', 'timestamp', 'content_type']
    search_fields = ['descripcion', 'usuario__username', 'ip_address']
    readonly_fields = ['timestamp', 'content_type', 'object_id', 'accion', 'usuario', 
                       'datos_anteriores', 'datos_nuevos', 'ip_address', 'user_agent', 'descripcion']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """No permitir crear registros de auditoría manualmente."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar registros de auditoría."""
        return False


@admin.register(AuditoriaSesion)
class AuditoriaSesionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'evento', 'username', 'usuario', 'exitoso', 'ip_address']
    list_filter = ['evento', 'exitoso', 'timestamp']
    search_fields = ['username', 'usuario__username', 'ip_address']
    readonly_fields = ['timestamp', 'usuario', 'username', 'evento', 'ip_address', 
                       'user_agent', 'exitoso', 'razon_fallo']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """No permitir crear registros de sesión manualmente."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar registros de sesión."""
        return False
