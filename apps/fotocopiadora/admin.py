from django.contrib import admin

from .models import FotocopiadoraEquipo, PrintRequest, PrintRoleMembership, TrabajoFotocopia


@admin.register(FotocopiadoraEquipo)
class FotocopiadoraEquipoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'ubicacion', 'activo')
    search_fields = ('codigo', 'nombre', 'ubicacion')
    list_filter = ('activo', 'eliminado')


@admin.register(TrabajoFotocopia)
class TrabajoFotocopiaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha_hora', 'tipo_uso', 'equipo', 'solicitante_nombre', 'cantidad_copias', 'monto_total')
    search_fields = ('numero', 'solicitante_nombre', 'rut_solicitante')
    list_filter = ('tipo_uso', 'equipo', 'activo', 'eliminado')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PrintRequest)
class PrintRequestAdmin(admin.ModelAdmin):
    list_display = ('numero', 'title', 'status', 'requester', 'approver', 'operator', 'required_at')
    search_fields = ('numero', 'title', 'requester__username')
    list_filter = ('status', 'priority', 'request_type', 'departamento', 'area')
    raw_id_fields = ('requester', 'approver', 'operator', 'departamento', 'area', 'equipo', 'cost_center')


@admin.register(PrintRoleMembership)
class PrintRoleMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'departamento', 'area', 'equipo', 'cost_center', 'is_primary', 'activo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('role', 'is_primary', 'activo', 'departamento', 'area')
