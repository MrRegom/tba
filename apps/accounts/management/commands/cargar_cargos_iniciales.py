"""
Management command para cargar cargos iniciales en la base de datos.

Uso:
    python manage.py cargar_cargos_iniciales
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import Cargo


class Command(BaseCommand):
    help = 'Carga los cargos iniciales del colegio en la base de datos'

    def handle(self, *args, **options):
        """Ejecuta el comando para cargar cargos iniciales."""
        
        cargos_data = [
            {'codigo': 'DIR-001', 'nombre': 'Directivos'},
            {'codigo': 'EDP-001', 'nombre': 'Educadores de Parvulo'},
            {'codigo': 'TEP-001', 'nombre': 'Tecnico de Parvulo'},
            {'codigo': 'PEB-001', 'nombre': 'Profesor Educacion Basica'},
            {'codigo': 'PEM-001', 'nombre': 'Profesor Educacion Media'},
            {'codigo': 'EDP-002', 'nombre': 'Educadora de Parvulo'},
            {'codigo': 'PSI-001', 'nombre': 'Psicologa'},
            {'codigo': 'TEN-001', 'nombre': 'Tecnico en Enfermeria'},
            {'codigo': 'ADM-001', 'nombre': 'Administrativo'},
            {'codigo': 'AUX-001', 'nombre': 'Auxiliar'},
            {'codigo': 'GUA-001', 'nombre': 'Guardia'},
        ]
        
        creados = 0
        actualizados = 0
        errores = []
        
        for cargo_data in cargos_data:
            try:
                cargo, created = Cargo.objects.update_or_create(
                    codigo=cargo_data['codigo'],
                    defaults={
                        'nombre': cargo_data['nombre'],
                        'activo': True,
                        'eliminado': False
                    }
                )
                
                if created:
                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] Cargo creado: {cargo.codigo} - {cargo.nombre}'
                        )
                    )
                else:
                    actualizados += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'[ACTUALIZADO] Cargo actualizado: {cargo.codigo} - {cargo.nombre}'
                        )
                    )
                    
            except Exception as e:
                errores.append({
                    'cargo': cargo_data['codigo'],
                    'error': str(e)
                })
                self.stdout.write(
                    self.style.ERROR(
                        f'[ERROR] Error al procesar {cargo_data["codigo"]}: {str(e)}'
                    )
                )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\nResumen:'))
        self.stdout.write(f'  • Cargos creados: {creados}')
        self.stdout.write(f'  • Cargos actualizados: {actualizados}')
        self.stdout.write(f'  • Errores: {len(errores)}')
        
        if errores:
            self.stdout.write(self.style.ERROR('\nErrores:'))
            for error in errores:
                self.stdout.write(f'  - {error["cargo"]}: {error["error"]}')
        
        self.stdout.write('\n' + '='*60)

