# Generated manually on 2025-12-08

from django.db import migrations


def add_foto_perfil_column(apps, schema_editor):
    """
    Agrega la columna foto_perfil a la tabla tba_persona si no existe.
    """
    with schema_editor.connection.cursor() as cursor:
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='tba_persona'
            AND column_name='foto_perfil'
        """)
        if cursor.fetchone() is None:
            # Agregar la columna como VARCHAR para almacenar la ruta del archivo
            cursor.execute("""
                ALTER TABLE tba_persona
                ADD COLUMN foto_perfil VARCHAR(100) NULL
            """)


def remove_foto_perfil_column(apps, schema_editor):
    """
    Elimina la columna foto_perfil de la tabla tba_persona.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='tba_persona'
            AND column_name='foto_perfil'
        """)
        if cursor.fetchone() is not None:
            cursor.execute("""
                ALTER TABLE tba_persona
                DROP COLUMN foto_perfil
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auditoriapin_usuario_actualizacion_and_more'),
    ]

    operations = [
        migrations.RunPython(add_foto_perfil_column, remove_foto_perfil_column),
    ]

