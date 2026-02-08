"""
Comando para crear 10 toldos de prueba en el inventario.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.activos.models import (
    CategoriaActivo, EstadoActivo, Marca, Ubicacion, Activo
)


class Command(BaseCommand):
    help = 'Crea 10 toldos de prueba en el inventario'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de toldos de prueba...'))
        
        # Obtener o crear usuario administrador para auditoría
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
        except Exception:
            admin_user = None
        
        # Crear o obtener categoría "Toldos"
        try:
            categoria = CategoriaActivo.objects.get(codigo='TOL')
            created = False
        except CategoriaActivo.DoesNotExist:
            categoria = CategoriaActivo(
                codigo='TOL',
                nombre='Toldos',
                sigla='TOL',
                descripcion='Toldos para eventos y actividades',
                activo=True,
                eliminado=False,
                usuario_creacion=admin_user,
                usuario_actualizacion=admin_user
            )
            categoria.save()
            created = True
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Categoria creada: {categoria.nombre}'))
        else:
            self.stdout.write(f'  Categoria ya existe: {categoria.nombre}')
        
        # Obtener marca existente (usar la primera disponible)
        marca = Marca.objects.filter(activo=True, eliminado=False).first()
        if not marca:
            self.stdout.write(self.style.ERROR('ERROR: No existe ninguna marca activa'))
            return
        
        self.stdout.write(f'  Usando marca: {marca.nombre}')
        
        # Obtener estado "Disponible"
        try:
            estado_disponible = EstadoActivo.objects.get(codigo='DISP')
        except EstadoActivo.DoesNotExist:
            self.stdout.write(self.style.ERROR('ERROR: No existe el estado DISPONIBLE'))
            return
        
        # Obtener ubicación existente (usar la primera disponible)
        ubicacion = Ubicacion.objects.filter(activo=True, eliminado=False).first()
        if not ubicacion:
            self.stdout.write(self.style.ERROR('ERROR: No existe ninguna ubicacion activa'))
            return
        
        self.stdout.write(f'  Usando ubicacion: {ubicacion.nombre}')
        
        # Crear 10 toldos
        toldos_creados = 0
        toldos_existentes = 0
        
        tamaños = ['3x3', '4x4', '5x5', '3x4', '4x5']
        colores = ['Azul', 'Blanco', 'Verde', 'Rojo', 'Amarillo']
        
        for i in range(1, 11):
            codigo = f'TOL-{i:03d}'
            
            # Verificar si ya existe
            if Activo.objects.filter(codigo=codigo).exists():
                toldos_existentes += 1
                self.stdout.write(f'  [EXISTE] {codigo}')
                continue
            
            # Datos del toldo
            tamaño = tamaños[i % len(tamaños)]
            color = colores[i % len(colores)]
            numero_serie = f'SN-TOL-2024-{i:04d}'
            
            # Crear el toldo
            toldo = Activo.objects.create(
                codigo=codigo,
                nombre=f'Toldo {tamaño} {color}',
                categoria=categoria,
                estado=estado_disponible,
                marca=marca,
                numero_serie=numero_serie,
                descripcion=f'Toldo plegable de {tamaño} metros, color {color}',
                precio_unitario=Decimal('150000.00'),
                activo=True,
                eliminado=False,
                usuario_creacion=admin_user,
                usuario_actualizacion=admin_user
            )
            
            toldos_creados += 1
            self.stdout.write(self.style.SUCCESS(
                f'[OK] [{toldos_creados}] {toldo.codigo} - {toldo.nombre} (S/N: {numero_serie})'
            ))
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Resumen:'))
        self.stdout.write(f'  - Toldos creados: {toldos_creados}')
        self.stdout.write(f'  - Toldos ya existentes: {toldos_existentes}')
        self.stdout.write(f'  - Total: {toldos_creados + toldos_existentes}')
        self.stdout.write('='*60)
        
        if toldos_creados > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\n{toldos_creados} toldos creados exitosamente!'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\nNo se crearon toldos nuevos (todos ya existian)'
            ))

