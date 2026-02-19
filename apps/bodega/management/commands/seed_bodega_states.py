from django.core.management.base import BaseCommand
from apps.bodega.models import EstadoEntrega, TipoEntrega, Operacion, TipoMovimiento

class Command(BaseCommand):
    help = 'Seeds mandatory states and types for the Bodega module'

    def handle(self, *args, **options):
        self.stdout.write('Syncing database sequences...')
        from django.core.management import call_command
        from django.db import connection
        
        # Sincronizar secuencias para evitar errores de llave duplicada
        with connection.cursor() as cursor:
            # Esto es específico para PostgreSQL y ayuda a resetear los contadores de ID
            commands = [
                "SELECT setval(pg_get_serial_sequence('tba_bodega_estado_entrega', 'id'), coalesce(max(id), 1)) FROM tba_bodega_estado_entrega;",
                "SELECT setval(pg_get_serial_sequence('tba_bodega_conf_tipoentrega', 'id'), coalesce(max(id), 1)) FROM tba_bodega_conf_tipoentrega;",
                "SELECT setval(pg_get_serial_sequence('tba_bodega_operacion', 'id'), coalesce(max(id), 1)) FROM tba_bodega_operacion;",
                "SELECT setval(pg_get_serial_sequence('tba_bodega_conf_tipomovimiento', 'id'), coalesce(max(id), 1)) FROM tba_bodega_conf_tipomovimiento;"
            ]
            for cmd in commands:
                try:
                    cursor.execute(cmd)
                except Exception:
                    pass

        self.stdout.write('Seeding Bodega states...')

        # 1. Estados de Entrega
        estados = [
            {
                'codigo': 'PENDIENTE',
                'nombre': 'Pendiente',
                'color': '#ffc107',
                'es_inicial': True,
                'es_final': False,
                'descripcion': 'La entrega ha sido registrada pero no procesada.'
            },
            {
                'codigo': 'DESPACHADO',
                'nombre': 'Despachado',
                'color': '#198754',
                'es_inicial': False,
                'es_final': True,
                'descripcion': 'La entrega se ha completado exitosamente.'
            },
            {
                'codigo': 'DESPACHO_PARCIAL',
                'nombre': 'Despacho Parcial',
                'color': '#0dcaf0',
                'es_inicial': False,
                'es_final': False,
                'descripcion': 'Se ha entregado una parte de la solicitud.'
            },
            {
                'codigo': 'ANULADO',
                'nombre': 'Anulado',
                'color': '#dc3545',
                'es_inicial': False,
                'es_final': True,
                'descripcion': 'La entrega ha sido cancelada.'
            },
        ]

        for est in estados:
            try:
                obj, created = EstadoEntrega.objects.update_or_create(
                    codigo=est['codigo'],
                    defaults=est
                )
                status = 'created' if created else 'updated'
                self.stdout.write(f'  State "{est["codigo"]}": {status}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error in State "{est["codigo"]}": {str(e)}'))

        # 2. Tipos de Entrega
        tipos = [
            {'codigo': 'DESPACHO_INTERNO', 'nombre': 'Despacho Interno', 'requiere_autorizacion': False},
            {'codigo': 'ENTREGA_PERSONAL', 'nombre': 'Entrega a Personal', 'requiere_autorizacion': False},
        ]

        for t in tipos:
            try:
                obj, created = TipoEntrega.objects.update_or_create(
                    codigo=t['codigo'],
                    defaults=t
                )
                status = 'created' if created else 'updated'
                self.stdout.write(f'  Type "{t["codigo"]}": {status}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error in Type "{t["codigo"]}": {str(e)}'))

        # 3. Operaciones
        operaciones = [
            {'codigo': 'ENTRADA', 'nombre': 'Entrada de Inventario', 'tipo': 'ENTRADA'},
            {'codigo': 'SALIDA', 'nombre': 'Salida de Inventario', 'tipo': 'SALIDA'},
        ]

        for op in operaciones:
            try:
                obj, created = Operacion.objects.update_or_create(
                    codigo=op['codigo'],
                    defaults=op
                )
                status = 'created' if created else 'updated'
                self.stdout.write(f'  Operation "{op["codigo"]}": {status}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error in Operation "{op["codigo"]}": {str(e)}'))

        # 4. Tipos de Movimiento
        movs = [
            {'codigo': 'ENTREGA', 'nombre': 'Entrega de Artículo'},
            {'codigo': 'AJUSTE', 'nombre': 'Ajuste de Stock'},
            {'codigo': 'COMPRA', 'nombre': 'Ingreso por Compra'},
        ]

        for m in movs:
            try:
                obj, created = TipoMovimiento.objects.update_or_create(
                    codigo=m['codigo'],
                    defaults=m
                )
                status = 'created' if created else 'updated'
                self.stdout.write(f'  Movement Type "{m["codigo"]}": {status}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error in Movement Type "{m["codigo"]}": {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Bodega module data.'))
