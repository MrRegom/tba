# Generated manually on 2025-12-08

from django.db import migrations


def add_foto_perfil_column(apps, schema_editor):
    """
    Agrega la columna foto_perfil a la tabla tba_persona si no existe.
    """
    table_name = 'tba_persona'
    column_name = 'foto_perfil'
    
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(100) NULL")
        else:
            # PostgreSQL y otros
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name=%s
                AND column_name=%s
            """, [table_name, column_name])
            
            if cursor.fetchone() is None:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(100) NULL")


def remove_foto_perfil_column(apps, schema_editor):
    """
    Elimina la columna foto_perfil de la tabla tba_persona.
    """
    table_name = 'tba_persona'
    column_name = 'foto_perfil'

    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name in columns:
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        else:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name=%s
                AND column_name=%s
            """, [table_name, column_name])
            
            if cursor.fetchone() is not None:
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auditoriapin_usuario_actualizacion_and_more'),
    ]

    operations = [
        migrations.RunPython(add_foto_perfil_column, remove_foto_perfil_column),
    ]

