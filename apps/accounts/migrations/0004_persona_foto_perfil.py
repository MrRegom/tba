# Reescrita con AddField estándar para correcta gestión de estado en Django
# La columna foto_perfil se agrega via AddField + IF NOT EXISTS para compatibilidad

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auditoriapin_usuario_actualizacion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='persona',
            name='foto_perfil',
            field=models.ImageField(
                blank=True,
                help_text='Foto de perfil del usuario',
                null=True,
                upload_to='perfiles/',
                verbose_name='Foto de Perfil',
            ),
        ),
    ]
