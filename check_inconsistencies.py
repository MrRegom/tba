
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.solicitudes.models import DetalleSolicitud
from apps.bodega.models import DetalleEntregaBien, DetalleEntregaArticulo

dets = DetalleSolicitud.objects.filter(cantidad_despachada__gt=0, eliminado=False)
print(f"Buscando inconsistencias en {dets.count()} detalles...")

for d in dets:
    # Para bienes/activos
    if d.activo:
        ent_exists = DetalleEntregaBien.objects.filter(activo=d.activo, entrega__solicitud=d.solicitud).exists()
    # Para artículos
    else:
        ent_exists = DetalleEntregaArticulo.objects.filter(articulo=d.articulo, entrega__solicitud=d.solicitud).exists()
        
    if not ent_exists:
        print(f"INCONSISTENCIA: Solicitud {d.solicitud.numero} ({d.solicitud.estado.nombre})")
        print(f"  Item: {d.activo or d.articulo}")
        print(f"  Cantidad Despachada en Solicitud: {d.cantidad_despachada}")
        print(f"  No hay registros de Entrega correspondientes en Bodega.")
        print("-" * 20)
