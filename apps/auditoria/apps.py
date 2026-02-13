from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auditoria'
    verbose_name = 'Auditoría'
    
    def ready(self):
        """Se ejecuta cuando la app está lista."""
        # Solo activar auditoría si no estamos en modo migración
        import sys
        if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
            from apps.auditoria.middleware import activar_auditoria_automatica
            activar_auditoria_automatica()
