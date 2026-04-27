import os
import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.bodega.models import Articulo, Categoria, Marca, UnidadMedida

class Command(BaseCommand):
    help = 'Importa inventario total desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta al archivo .xlsx')

    def handle(self, *args, **options):
        file_path = options['excel_file']
        
        if not os.path.exists(file_path):
            self.stderr.write(f"Error: El archivo {file_path} no existe.")
            return

        try:
            from django.contrib.auth.models import User
            from apps.bodega.models import Bodega
            
            wb = openpyxl.load_workbook(file_path, data_only=True)
            
            # 1. Asegurar una Bodega física para la restricción not-null
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
                
            bodega_principal, _ = Bodega.objects.get_or_create(
                codigo="BOD-001",
                defaults={
                    "nombre": "Bodega Principal",
                    "responsable": admin_user
                }
            )
            
            total_created = 0
            total_updated = 0
            
            with transaction.atomic():
                for sheet in wb.worksheets:
                    cat_name = sheet.title.strip()
                    self.stdout.write(f"Procesando categoría (pestaña): {cat_name}...")
                    
                    # Obtener o crear la categoría basada en el nombre de la pestaña
                    categoria, _ = Categoria.objects.get_or_create(nombre=cat_name)
                    
                    # Leer filas de esta pestaña (saltando encabezado)
                    rows = list(sheet.iter_rows(min_row=2, values_only=True))
                    
                    for row in rows:
                        if not row or not row[1]: # Si no hay nombre, saltar
                            continue
                            
                        nombre = str(row[1]).strip()
                        descripcion = str(row[2]).strip() if row[2] else ""
                        marca_name = str(row[4]).strip() if row[4] else "Genérico"
                        unidad_name = str(row[5]).strip() if row[5] else "UND"
                        stock_min = int(row[6]) if row[6] is not None else 0
                        stock_actual = int(row[9]) if row[9] is not None else 0
                        
                        # Obtener o crear maestros
                        marca, _ = Marca.objects.get_or_create(nombre=marca_name)
                        unidad, _ = UnidadMedida.objects.get_or_create(nombre=unidad_name)
                        
                        # Crear o actualizar artículo
                        articulo, was_created = Articulo.objects.update_or_create(
                            nombre=nombre,
                            categoria=categoria, # Incluimos categoría en el lookup para evitar colisiones entre hojas
                            defaults={
                                'descripcion': descripcion,
                                'marca': marca,
                                'unidad_medida': unidad,
                                'stock_minimo': stock_min,
                                'stock_actual': stock_actual,
                                'ubicacion_fisica': bodega_principal,
                                'activo': True
                            }
                        )
                        
                        if was_created:
                            total_created += 1
                        else:
                            total_updated += 1

            self.stdout.write(self.style.SUCCESS(
                f"Importación finalizada con éxito. "
                f"Total Creados: {total_created}, Total Actualizados: {total_updated}"
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error durante la importación: {str(e)}"))
