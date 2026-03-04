from django.contrib import admin

from .models import FotocopiadoraEquipo, TrabajoFotocopia


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
