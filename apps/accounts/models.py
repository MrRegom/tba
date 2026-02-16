from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from core.models import BaseModel

class AuthEstado(models.Model):
    glosa = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "auth_estado"
        verbose_name = "Estado de usuario"
        verbose_name_plural = "Estados de usuario"
        indexes = [
            models.Index(fields=["activo"]),
        ]


class AuthUserEstado(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="estados")
    estado = models.ForeignKey(AuthEstado, on_delete=models.PROTECT, related_name="usuarios")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_user_estado"
        verbose_name = "Estado asignado a usuario"
        verbose_name_plural = "Estados de usuarios"
        # Si quieres que un usuario tenga sólo un estado actual, usa UniqueConstraint
        constraints = [
            models.UniqueConstraint(fields=["usuario"], name="uq_auth_user_estado_user_single", condition=models.Q()),
        ]
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"{self.usuario} -> {self.estado}"


class AuthLogAccion(models.Model):
    glosa = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "auth_log_accion"
        verbose_name = "Acción de log"
        verbose_name_plural = "Acciones de log"

    def __str__(self):
        return self.glosa


class AuthLogs(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="auth_logs")
    accion = models.ForeignKey(AuthLogAccion, on_delete=models.PROTECT, related_name="logs")
    descripcion = models.TextField(blank=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)
    agente = models.TextField(blank=True)  # user agent
    meta = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_logs"
        verbose_name = "Log de autenticación"
        verbose_name_plural = "Logs de autenticación"
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["accion"]),
            models.Index(fields=["-fecha_creacion"]),
        ]

    def __str__(self):
        u = self.usuario if self.usuario else "anon"
        return f"[{self.fecha_creacion}] {u} - {self.accion}"


class HistorialLogin(models.Model):
    """
    Tabla para guardar historial de logins: sesión (clave), IP, user-agent y fecha/hora.
    db_table mantiene el nombre legacy que indicaste: auth_user_login_history
    """
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_history",
        db_index=True,
    )
    session_key = models.CharField(
        "clave_sesión",
        max_length=128,
        null=True,
        blank=True,
        help_text="Clave de sesión (session_key). Si existe, puede relacionarse con sesiones_usuarios.id"
    )
    direccion_ip = models.GenericIPAddressField("ip", null=True, blank=True)
    agente = models.TextField("user agent", blank=True, default="")
    fecha_login = models.DateTimeField("fecha_login", default=timezone.now, db_index=True)

    class Meta:
        db_table = "auth_user_login_history"
        verbose_name = "Historial de login"
        verbose_name_plural = "Historiales de login"
        indexes = [
            models.Index(fields=["usuario", "fecha_login"], name="ix_login_usuario_fecha"),
            models.Index(fields=["session_key"], name="ix_login_session_key"),
            models.Index(fields=["direccion_ip", "fecha_login"], name="ix_login_ip_fecha"),
        ]
        ordering = ["-fecha_login"]

    def __str__(self):
        return f"{self.usuario or 'anon'} @ {self.fecha_login.isoformat()} ({self.direccion_ip})"


# ==================== GESTIÓN DE PERSONAS Y SEGURIDAD ====================

class Cargo(BaseModel):
    """
    Catálogo de cargos/puestos de trabajo del colegio.
    
    Tabla: tba_cargos
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único del cargo (ej: PROF-MAT, BOD-001)'
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Cargo',
        help_text='Nombre descriptivo del cargo'
    )

    class Meta:
        db_table = 'tba_cargos'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo', 'eliminado']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Persona(BaseModel):
    """
    Información personal extendida del funcionario.
    
    Tabla: tba_persona
    Relación 1:1 con User
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='persona',
        verbose_name='Usuario',
        help_text='Usuario asociado a esta persona'
    )
    documento_identidad = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='RUT/Documento de Identidad',
        help_text='RUT chileno o documento de identidad'
    )
    nombres = models.CharField(
        max_length=100,
        verbose_name='Nombres'
    )
    apellido1 = models.CharField(
        max_length=100,
        verbose_name='Primer Apellido'
    )
    apellido2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Segundo Apellido'
    )
    sexo = models.CharField(
        max_length=1,
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('O', 'Otro')
        ],
        verbose_name='Sexo'
    )
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de Nacimiento'
    )
    talla = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Talla',
        help_text='Talla de ropa (XS, S, M, L, XL, XXL)'
    )
    numero_zapato = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name='Número de Zapato',
        help_text='Número de zapato para EPP'
    )
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil',
        help_text='Foto de perfil del usuario'
    )

    class Meta:
        db_table = 'tba_persona'
        verbose_name = 'Persona/Funcionario'
        verbose_name_plural = 'Personas/Funcionarios'
        ordering = ['apellido1', 'apellido2', 'nombres']
        indexes = [
            models.Index(fields=['documento_identidad']),
            models.Index(fields=['user']),
            models.Index(fields=['activo', 'eliminado']),
        ]

    def __str__(self):
        return f"{self.documento_identidad} - {self.get_nombre_completo()}"

    def get_nombre_completo(self):
        """Retorna el nombre completo de la persona."""
        nombre = f"{self.nombres} {self.apellido1}"
        if self.apellido2:
            nombre += f" {self.apellido2}"
        return nombre


class UserCargo(BaseModel):
    """
    Relación entre usuarios y cargos (historial de cargos).
    
    Tabla: tba_user_cargos
    Permite que un usuario tenga múltiples cargos en el tiempo.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cargos_historico',
        verbose_name='Usuario'
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.PROTECT,
        related_name='usuarios',
        verbose_name='Cargo'
    )
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    fecha_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Fin',
        help_text='Dejar vacío si es el cargo actual'
    )

    class Meta:
        db_table = 'tba_user_cargos'
        verbose_name = 'Cargo de Usuario'
        verbose_name_plural = 'Cargos de Usuarios'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', 'fecha_inicio']),
            models.Index(fields=['cargo']),
            models.Index(fields=['activo', 'eliminado']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.cargo.nombre} ({self.fecha_inicio})"

    @property
    def es_actual(self):
        """Retorna True si es el cargo actual (fecha_fin es None)."""
        return self.fecha_fin is None


class UserSecure(BaseModel):
    """
    Gestión de seguridad del usuario: PIN y control de intentos fallidos.
    
    Tabla: tba_user_secure
    Relación 1:1 con User
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seguridad',
        verbose_name='Usuario'
    )
    pin = models.CharField(
        max_length=255,
        verbose_name='PIN Encriptado',
        help_text='PIN de 4 dígitos (almacenado encriptado)'
    )
    intentos_fallidos = models.IntegerField(
        default=0,
        verbose_name='Intentos Fallidos'
    )
    bloqueado = models.BooleanField(
        default=False,
        verbose_name='Usuario Bloqueado'
    )

    class Meta:
        db_table = 'tba_user_secure'
        verbose_name = 'Seguridad de Usuario'
        verbose_name_plural = 'Seguridad de Usuarios'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['bloqueado']),
            models.Index(fields=['activo', 'eliminado']),
        ]

    def __str__(self):
        estado = "BLOQUEADO" if self.bloqueado else "ACTIVO"
        return f"{self.user.username} - {estado}"

    def set_pin(self, pin_texto: str):
        """Encripta y guarda el PIN."""
        self.pin = make_password(pin_texto)

    def verificar_pin(self, pin_texto: str) -> bool:
        """Verifica si el PIN es correcto."""
        return check_password(pin_texto, self.pin)

    def registrar_intento_fallido(self):
        """Registra un intento fallido y bloquea si excede el límite."""
        self.intentos_fallidos += 1
        
        # Bloquear después de 3 intentos fallidos
        if self.intentos_fallidos >= 3:
            self.bloqueado = True
        
        self.save()

    def resetear_intentos(self):
        """Resetea los intentos fallidos después de un PIN correcto."""
        self.intentos_fallidos = 0
        self.save()

    def desbloquear(self):
        """Desbloquea el usuario (solo admin puede hacerlo)."""
        self.bloqueado = False
        self.intentos_fallidos = 0
        self.save()


class AuditoriaPin(BaseModel):
    """
    Auditoría de uso del PIN en movimientos de inventario.
    
    Tabla: tba_auditoria_pin
    Registra cada vez que se usa el PIN para confirmar una entrega.
    """
    ACCION_CHOICES = [
        ('CONFIRMACION_ENTREGA', 'Confirmación de Entrega'),
        ('INTENTO_FALLIDO', 'Intento Fallido'),
        ('BLOQUEO', 'Bloqueo de Usuario'),
        ('DESBLOQUEO', 'Desbloqueo de Usuario'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='auditoria_pin',
        verbose_name='Usuario'
    )
    accion = models.CharField(
        max_length=50,
        choices=ACCION_CHOICES,
        verbose_name='Acción'
    )
    exitoso = models.BooleanField(
        verbose_name='Exitoso'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='User Agent'
    )
    detalles = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Detalles Adicionales',
        help_text='Información adicional en formato JSON'
    )

    class Meta:
        db_table = 'tba_auditoria_pin'
        verbose_name = 'Auditoría de PIN'
        verbose_name_plural = 'Auditorías de PIN'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', '-fecha_creacion']),
            models.Index(fields=['accion']),
            models.Index(fields=['exitoso']),
            models.Index(fields=['activo', 'eliminado']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} - {self.fecha_creacion}"