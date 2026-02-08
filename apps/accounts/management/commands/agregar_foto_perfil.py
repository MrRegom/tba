"""
Comando de management para agregar la columna foto_perfil a la tabla tba_persona.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega la columna foto_perfil a la tabla tba_persona si no existe'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Verificar si la columna ya existe
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='tba_persona'
                AND column_name='foto_perfil'
            """)
            
            columna_existe = cursor.fetchone() is not None
            
            if columna_existe:
                # Verificar el tamaño actual
                cursor.execute("""
                    SELECT character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name='tba_persona'
                    AND column_name='foto_perfil'
                """)
                resultado = cursor.fetchone()
                tamaño_actual = resultado[0] if resultado else None
                
                if tamaño_actual and tamaño_actual < 255:
                    # Actualizar el tamaño a 255
                    try:
                        cursor.execute("""
                            ALTER TABLE tba_persona
                            ALTER COLUMN foto_perfil TYPE VARCHAR(255)
                        """)
                        self.stdout.write(
                            self.style.SUCCESS(f'Columna foto_perfil actualizada de {tamaño_actual} a 255 caracteres.')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error al actualizar el tamaño de la columna: {str(e)}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('La columna foto_perfil ya existe en tba_persona con tamaño adecuado.')
                    )
                return
            
            # Agregar la columna
            try:
                cursor.execute("""
                    ALTER TABLE tba_persona
                    ADD COLUMN foto_perfil VARCHAR(255) NULL
                """)
                self.stdout.write(
                    self.style.SUCCESS('Columna foto_perfil agregada exitosamente a tba_persona.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al agregar la columna: {str(e)}')
                )

