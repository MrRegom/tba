from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Gestión de Notificaciones'

    def ready(self):
        import apps.notificaciones.signals  # noqa: F401
