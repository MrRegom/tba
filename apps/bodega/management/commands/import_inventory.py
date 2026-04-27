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
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            
            # Mapeo de columnas (basado en el análisis previo)
            # 0: ID (ignorar)
            # 1: Nombre
            # 2: Descripción
            # 3: Categoría
            # 4: Marca
            # 5: Unidad Medida
            # 6: Stock Mínimo
            # 7: Stock Máximo
            # 8: Retirado
            # 9: Stock Actual
            
            rows = list(sheet.iter_rows(min_row=2, values_only=True))
            total = len(rows)
            created = 0
            updated = 0
            
            self.stdout.write(f"Iniciando importación de {total} registros...")

            with transaction.atomic():
                for row in rows:
                    if not row[1]: # Si no hay nombre, saltar
                        continue
                        
                    nombre = str(row[1]).strip()
                    descripcion = str(row[2]).strip() if row[2] else ""
                    cat_name = str(row[3]).strip() if row[3] else "Sin Categoría"
                    marca_name = str(row[4]).strip() if row[4] else "Genérico"
                    unidad_name = str(row[5]).strip() if row[5] else "UND"
                    stock_min = int(row[6]) if row[6] is not None else 0
                    stock_actual = int(row[9]) if row[9] is not None else 0
                    
                    # 1. Obtener o crear maestros
                    categoria, _ = Categoria.objects.get_or_create(nombre=cat_name)
                    marca, _ = Marca.objects.get_or_create(nombre=marca_name)
                    unidad, _ = UnidadMedida.objects.get_or_create(nombre=unidad_name)
                    
                    # 2. Crear o actualizar artículo
                    articulo, was_created = Articulo.objects.update_or_create(
                        nombre=nombre,
                        defaults={
                            'descripcion': descripcion,
                            'categoria': categoria,
                            'marca': marca,
                            'unidad_medida': unidad,
                            'stock_minimo': stock_min,
                            'stock_actual': stock_actual,
                            'activo': True
                        }
                    )
                    
                    if was_created:
                        created += 1
                    else:
                        updated += 1

            self.stdout.write(self.style.SUCCESS(
                f"Importación finalizada con éxito. "
                f"Creados: {created}, Actualizados: {updated}"
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error durante la importación: {str(e)}"))
