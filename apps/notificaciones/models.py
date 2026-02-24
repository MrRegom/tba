from django.db import models
from django.contrib.auth.models import User


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('SOLICITUD', 'Solicitud'),
        ('BAJA',      'Baja de Inventario'),
        ('COMPRA',    'Orden de Compra'),
        ('SISTEMA',   'Sistema'),
    ]

    ICONO_POR_TIPO = {
        'SOLICITUD': 'ri-file-list-3-line text-primary',
        'BAJA':      'ri-delete-bin-line text-danger',
        'COMPRA':    'ri-shopping-cart-2-line text-success',
        'SISTEMA':   'ri-information-line text-warning',
    }

    destinatario  = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notificaciones', verbose_name='Destinatario'
    )
    tipo          = models.CharField(max_length=20, choices=TIPO_CHOICES, default='SISTEMA')
    titulo        = models.CharField(max_length=200, verbose_name='Título')
    mensaje       = models.TextField(verbose_name='Mensaje')
    url           = models.CharField(max_length=500, blank=True, default='', verbose_name='URL')
    leida         = models.BooleanField(default=False, verbose_name='Leída')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tba_notificacion'
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.destinatario.username} — {self.titulo}'

    @property
    def icono_css(self):
        return self.ICONO_POR_TIPO.get(self.tipo, 'ri-notification-line text-secondary')

    @classmethod
    def crear(cls, destinatario, tipo, titulo, mensaje, url=''):
        """Atajo para crear una notificación."""
        return cls.objects.create(
            destinatario=destinatario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            url=url,
        )

    @classmethod
    def notificar_a_usuarios_con_permiso(cls, codename, tipo, titulo, mensaje, url=''):
        """Crea una notificación para cada usuario activo que tenga el permiso dado."""
        from django.contrib.auth.models import Permission
        from django.db.models import Q

        try:
            perm = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            return

        usuarios = User.objects.filter(
            Q(groups__permissions=perm) | Q(user_permissions=perm),
            is_active=True,
        ).distinct()

        notificaciones = [
            cls(destinatario=u, tipo=tipo, titulo=titulo, mensaje=mensaje, url=url)
            for u in usuarios
        ]
        cls.objects.bulk_create(notificaciones, ignore_conflicts=True)
