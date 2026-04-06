from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.solicitudes.models import Area, Departamento
from core.models import AutoCodeMixin, BaseModel
from core.utils import generar_codigo_unico, validar_rut, format_rut


class FotocopiadoraEquipo(AutoCodeMixin, BaseModel):
    AUTO_CODE_PREFIX = "FEQ"

    codigo = models.CharField(max_length=20, unique=True, verbose_name="Codigo")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    ubicacion = models.CharField(max_length=150, verbose_name="Ubicacion")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripcion")

    class Meta:
        db_table = "tba_fotocopiadora_equipo"
        verbose_name = "Equipo Fotocopiadora"
        verbose_name_plural = "Equipos Fotocopiadora"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class TrabajoFotocopia(BaseModel):
    class TipoUso(models.TextChoices):
        INTERNO = "INTERNO", "Uso Institucional (Colegio)"
        PERSONAL = "PERSONAL", "Uso Personal (Docente)"

    numero = models.CharField(max_length=20, unique=True, verbose_name="Numero")
    fecha_hora = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name="Fecha y Hora"
    )
    tipo_uso = models.CharField(
        max_length=20, choices=TipoUso.choices, verbose_name="Tipo de Uso"
    )

    equipo = models.ForeignKey(
        FotocopiadoraEquipo,
        on_delete=models.PROTECT,
        related_name="trabajos",
        verbose_name="Equipo",
    )

    solicitante_usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trabajos_fotocopia",
        verbose_name="Solicitante (Usuario)",
    )
    solicitante_nombre = models.CharField(max_length=200, verbose_name="Solicitante")
    rut_solicitante = models.CharField(
        max_length=12, blank=True, null=True, verbose_name="RUT Solicitante"
    )

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trabajos_fotocopia",
        verbose_name="Departamento",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trabajos_fotocopia",
        verbose_name="Area",
    )

    cantidad_copias = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Cantidad de Copias"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio Unitario",
    )
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Monto Total",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    class Meta:
        db_table = "tba_fotocopiadora_trabajo"
        verbose_name = "Trabajo Fotocopia"
        verbose_name_plural = "Trabajos Fotocopia"
        ordering = ["-fecha_hora", "-numero"]
        indexes = [
            models.Index(fields=["-fecha_hora"]),
            models.Index(fields=["tipo_uso", "-fecha_hora"]),
            models.Index(fields=["equipo", "-fecha_hora"]),
            models.Index(fields=["rut_solicitante"]),
        ]
        permissions = [
            (
                "registrar_trabajo_interno",
                "Puede registrar trabajo interno de fotocopiadora",
            ),
            (
                "registrar_trabajo_cobro",
                "Puede registrar trabajo con cobro informativo",
            ),
            ("anular_trabajo_fotocopia", "Puede anular trabajos de fotocopiadora"),
            ("ver_reportes_fotocopiadora", "Puede ver reportes de fotocopiadora"),
            (
                "gestionar_equipos_fotocopiadora",
                "Puede gestionar equipos de fotocopiadora",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.numero} - {self.solicitante_nombre} ({self.tipo_uso})"

    def clean(self) -> None:
        errors = {}

        if self.tipo_uso == self.TipoUso.INTERNO:
            if not self.departamento and not self.area:
                errors["departamento"] = (
                    "Para uso interno debe indicar departamento o area."
                )
            self.rut_solicitante = None
            self.precio_unitario = Decimal("0")
            self.monto_total = Decimal("0")

        if self.tipo_uso in {self.TipoUso.PERSONAL, self.TipoUso.EXTERNO}:
            if not self.rut_solicitante:
                errors["rut_solicitante"] = (
                    "El RUT es obligatorio para uso personal o externo."
                )
            elif not validar_rut(self.rut_solicitante):
                errors["rut_solicitante"] = "RUT invalido."
            else:
                self.rut_solicitante = format_rut(self.rut_solicitante)

            if self.precio_unitario is None:
                errors["precio_unitario"] = (
                    "El precio unitario es obligatorio para uso personal o externo."
                )

        if self.cantidad_copias <= 0:
            errors["cantidad_copias"] = "La cantidad de copias debe ser mayor a cero."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        if not self.numero:
            self.numero = generar_codigo_unico(
                "FOT", TrabajoFotocopia, "numero", longitud=8
            )

        if self.tipo_uso == self.TipoUso.INTERNO:
            self.precio_unitario = Decimal("0")
            self.monto_total = Decimal("0")
        elif self.precio_unitario is not None:
            self.monto_total = Decimal(self.cantidad_copias) * self.precio_unitario

        super().save(*args, **kwargs)


class PrintRequestType(models.TextChoices):
    PHOTOCOPY = "PHOTOCOPY", "Fotocopia"
    PRINT = "PRINT", "Impresion"
    MIXED = "MIXED", "Mixto"


class PrintRequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Borrador"
    PENDING_APPROVAL = "PENDING_APPROVAL", "POR APROBAR"
    APPROVED = "APPROVED", "Aprobada"
    REJECTED = "REJECTED", "Rechazada"
    IN_PROGRESS = "IN_PROGRESS", "En preparacion"
    READY_FOR_PICKUP = "READY_FOR_PICKUP", "Lista para retiro"
    DELIVERED = "DELIVERED", "Entregada"
    CLOSED = "CLOSED", "Cerrada"
    CANCELLED = "CANCELLED", "Cancelada"


class PrintPriority(models.TextChoices):
    LOW = "LOW", "Baja"
    NORMAL = "NORMAL", "Normal"
    HIGH = "HIGH", "Alta"
    URGENT = "URGENT", "Urgente"


class PrintSourceMode(models.TextChoices):
    TEACHER_PORTAL = "TEACHER_PORTAL", "Portal Docente"
    OPERATOR_MANUAL = "OPERATOR_MANUAL", "Carga Manual Operadora"
    MIGRATED_LEGACY = "MIGRATED_LEGACY", "Migrado Legacy"


class PrintPageSize(models.TextChoices):
    A4 = "A4", "A4"
    A3 = "A3", "A3"
    LETTER = "LETTER", "Carta"
    LEGAL = "LEGAL", "Legal"
    OFICIO = "OFICIO", "Oficio"


class PrintSide(models.TextChoices):
    SINGLE = "SINGLE", "Una Cara"
    DOUBLE = "DOUBLE", "Doble Faz"


class PrintColorMode(models.TextChoices):
    BW = "BW", "Blanco y Negro"
    COLOR = "COLOR", "Color"


class PrintCommentType(models.TextChoices):
    GENERAL = "GENERAL", "General"
    APPROVAL = "APPROVAL", "Aprobacion"
    OPERATION = "OPERATION", "Operacion"
    DELIVERY = "DELIVERY", "Entrega"
    INTERNAL = "INTERNAL", "Interno"


class PrintMembershipRole(models.TextChoices):
    REQUESTER = "REQUESTER", "Solicitante"
    APPROVER = "APPROVER", "Aprobador"
    OPERATOR = "OPERATOR", "Operador"
    ADMIN = "ADMIN", "Administrador"
    AUDITOR = "AUDITOR", "Auditor"
    SUPERADMIN = "SUPERADMIN", "Superadministrador"


class PrintCostCenter(AutoCodeMixin, BaseModel):
    AUTO_CODE_PREFIX = "PCC"

    codigo = models.CharField(max_length=30, unique=True, verbose_name="Codigo")
    nombre = models.CharField(max_length=120, verbose_name="Nombre")
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="centros_costo_impresion",
        null=True,
        blank=True,
        verbose_name="Departamento",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="centros_costo_impresion",
        null=True,
        blank=True,
        verbose_name="Area",
    )
    monthly_copy_quota = models.PositiveIntegerField(
        default=0, verbose_name="Cuota mensual de copias"
    )
    monthly_color_quota = models.PositiveIntegerField(
        default=0, verbose_name="Cuota mensual de color"
    )

    class Meta:
        db_table = "tba_print_cost_center"
        verbose_name = "Centro de costo de impresion"
        verbose_name_plural = "Centros de costo de impresion"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class PrintRoleMembership(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="print_role_memberships",
        verbose_name="Usuario",
    )
    role = models.CharField(
        max_length=30, choices=PrintMembershipRole.choices, verbose_name="Rol"
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="print_role_memberships",
        null=True,
        blank=True,
        verbose_name="Departamento",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="print_role_memberships",
        null=True,
        blank=True,
        verbose_name="Area",
    )
    equipo = models.ForeignKey(
        FotocopiadoraEquipo,
        on_delete=models.PROTECT,
        related_name="print_role_memberships",
        null=True,
        blank=True,
        verbose_name="Equipo",
    )
    cost_center = models.ForeignKey(
        PrintCostCenter,
        on_delete=models.PROTECT,
        related_name="print_role_memberships",
        null=True,
        blank=True,
        verbose_name="Centro de costo",
    )
    is_primary = models.BooleanField(default=False, verbose_name="Es principal")
    valid_from = models.DateField(null=True, blank=True, verbose_name="Vigente desde")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Vigente hasta")

    class Meta:
        db_table = "tba_print_role_membership"
        verbose_name = "Membresia de rol de impresion"
        verbose_name_plural = "Membresias de rol de impresion"
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["departamento", "role"]),
            models.Index(fields=["area", "role"]),
            models.Index(fields=["equipo", "role"]),
            models.Index(fields=["cost_center", "role"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "role",
                    "departamento",
                    "area",
                    "equipo",
                    "cost_center",
                ],
                name="uniq_print_role_membership_scope",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_primary=True, activo=True, eliminado=False),
                name="uniq_active_primary_print_membership_per_user",
            ),
        ]

    def __str__(self) -> str:
        scope = self.area or self.departamento or self.equipo or "Global"
        return f"{self.user} - {self.get_role_display()} - {scope}"

    def clean(self) -> None:
        errors = {}
        if self.role == PrintMembershipRole.APPROVER and not (
            self.departamento_id or self.area_id
        ):
            errors["departamento"] = (
                "Un aprobador debe quedar asociado a un departamento o area."
            )
        if (
            self.role == PrintMembershipRole.OPERATOR
            and self.departamento_id
            and self.area_id
        ):
            errors["area"] = (
                "La operadora debe quedar asociada a area o departamento, no a ambos simultaneamente."
            )
        if self.role in {
            PrintMembershipRole.ADMIN,
            PrintMembershipRole.AUDITOR,
            PrintMembershipRole.SUPERADMIN,
        } and (
            self.departamento_id
            or self.area_id
            or self.equipo_id
            or self.cost_center_id
        ):
            errors["role"] = (
                "Los perfiles globales del modulo no deben quedar restringidos a un alcance operativo."
            )
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            errors["valid_to"] = (
                "La vigencia de termino no puede ser anterior a la de inicio."
            )
        if errors:
            raise ValidationError(errors)


class PrintRequest(BaseModel):
    numero = models.CharField(
        max_length=30, unique=True, db_index=True, verbose_name="Numero"
    )
    title = models.CharField(max_length=180, verbose_name="Titulo")
    description = models.TextField(blank=True, verbose_name="Descripcion")
    use_type = models.CharField(
        max_length=20,
        choices=TrabajoFotocopia.TipoUso.choices,
        default=TrabajoFotocopia.TipoUso.INTERNO,
        verbose_name="Tipo de uso",
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Monto Total",
    )
    request_type = models.CharField(
        max_length=20,
        choices=PrintRequestType.choices,
        default=PrintRequestType.PHOTOCOPY,
        verbose_name="Tipo de solicitud",
    )
    status = models.CharField(
        max_length=30,
        choices=PrintRequestStatus.choices,
        default=PrintRequestStatus.DRAFT,
        db_index=True,
        verbose_name="Estado",
    )
    priority = models.CharField(
        max_length=20,
        choices=PrintPriority.choices,
        default=PrintPriority.NORMAL,
        db_index=True,
        verbose_name="Prioridad",
    )
    required_at = models.DateTimeField(db_index=True, verbose_name="Fecha requerida")
    submitted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de envio"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de aprobacion"
    )
    rejected_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de rechazo"
    )
    started_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha inicio operacion"
    )
    ready_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha listo para retiro"
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de entrega"
    )
    closed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de cierre"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de cancelacion"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_requests_created",
        verbose_name="Solicitante",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_requests_approved",
        null=True,
        blank=True,
        verbose_name="Aprobador",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_requests_operated",
        null=True,
        blank=True,
        verbose_name="Operador",
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_requests_closed",
        null=True,
        blank=True,
        verbose_name="Cerrado por",
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_requests_cancelled",
        null=True,
        blank=True,
        verbose_name="Cancelado por",
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="print_requests",
        null=True,
        blank=True,
        verbose_name="Departamento",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="print_requests",
        null=True,
        blank=True,
        verbose_name="Area",
    )
    equipo = models.ForeignKey(
        FotocopiadoraEquipo,
        on_delete=models.PROTECT,
        related_name="print_requests",
        null=True,
        blank=True,
        verbose_name="Equipo asignado",
    )
    cost_center = models.ForeignKey(
        PrintCostCenter,
        on_delete=models.PROTECT,
        related_name="print_requests",
        null=True,
        blank=True,
        verbose_name="Centro de costo",
    )
    approval_comment = models.TextField(
        blank=True, verbose_name="Observacion de aprobacion"
    )
    rejection_reason = models.TextField(blank=True, verbose_name="Motivo de rechazo")
    operator_comment = models.TextField(
        blank=True, verbose_name="Observacion operativa"
    )
    delivery_comment = models.TextField(
        blank=True, verbose_name="Observacion de entrega"
    )
    close_reason = models.TextField(blank=True, verbose_name="Motivo de cierre")
    is_partial_approval = models.BooleanField(
        default=False, verbose_name="Aprobacion parcial"
    )
    source_mode = models.CharField(
        max_length=20,
        choices=PrintSourceMode.choices,
        default=PrintSourceMode.TEACHER_PORTAL,
        db_index=True,
        verbose_name="Origen",
    )

    class Meta:
        db_table = "tba_print_request"
        verbose_name = "Solicitud de impresion"
        verbose_name_plural = "Solicitudes de impresion"
        ordering = ["-fecha_creacion", "-required_at"]
        indexes = [
            models.Index(fields=["status", "required_at"]),
            models.Index(fields=["requester", "status"]),
            models.Index(fields=["departamento", "status"]),
            models.Index(fields=["area", "status"]),
            models.Index(fields=["operator", "status"]),
            models.Index(fields=["approver", "status"]),
            models.Index(fields=["source_mode", "fecha_creacion"]),
        ]
        permissions = [
            ("submit_printrequest", "Puede enviar solicitudes de impresion"),
            ("approve_printrequest", "Puede aprobar solicitudes de impresion"),
            ("reject_printrequest", "Puede rechazar solicitudes de impresion"),
            (
                "partial_approve_printrequest",
                "Puede aprobar parcialmente solicitudes de impresion",
            ),
            ("operate_printrequest", "Puede operar solicitudes de impresion"),
            (
                "assign_operator_printrequest",
                "Puede asignar operador a solicitudes de impresion",
            ),
            ("mark_ready_printrequest", "Puede marcar solicitudes listas para retiro"),
            ("deliver_printrequest", "Puede marcar solicitudes entregadas"),
            ("close_printrequest", "Puede cerrar solicitudes de impresion"),
            (
                "cancel_own_printrequest",
                "Puede cancelar sus propias solicitudes de impresion",
            ),
            (
                "cancel_any_printrequest",
                "Puede cancelar cualquier solicitud de impresion",
            ),
            ("reopen_printrequest", "Puede reabrir solicitudes de impresion"),
            ("view_all_printrequest", "Puede ver todas las solicitudes de impresion"),
            (
                "view_department_printrequest",
                "Puede ver solicitudes de impresion de su ambito",
            ),
            (
                "view_operational_queue_printrequest",
                "Puede ver la bandeja operativa de impresion",
            ),
            (
                "manage_print_settings",
                "Puede gestionar configuracion del modulo de impresion",
            ),
            (
                "manage_print_cost_centers",
                "Puede gestionar centros de costo y cuotas de impresion",
            ),
            (
                "manage_print_memberships",
                "Puede gestionar memberships del modulo de impresion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.numero} - {self.title}"

    def save(self, *args, **kwargs) -> None:
        if not self.numero:
            self.numero = generar_codigo_unico(
                "PRN", PrintRequest, "numero", longitud=10
            )
        super().save(*args, **kwargs)

    def clean(self) -> None:
        errors = {}
        if (
            self.area_id
            and self.departamento_id
            and self.area
            and self.area.departamento_id != self.departamento_id
        ):
            errors["area"] = (
                "El area seleccionada no pertenece al departamento indicado."
            )
        if self.required_at and self.required_at <= timezone.now():
            errors["required_at"] = "La fecha requerida debe ser futura."
        if (
            self.status
            in {
                PrintRequestStatus.APPROVED,
                PrintRequestStatus.IN_PROGRESS,
                PrintRequestStatus.READY_FOR_PICKUP,
                PrintRequestStatus.DELIVERED,
                PrintRequestStatus.CLOSED,
            }
            and not self.approver_id
        ):
            errors["approver"] = (
                "Una solicitud aprobada u operativa debe registrar aprobador."
            )
        if (
            self.status
            in {
                PrintRequestStatus.IN_PROGRESS,
                PrintRequestStatus.READY_FOR_PICKUP,
                PrintRequestStatus.DELIVERED,
                PrintRequestStatus.CLOSED,
            }
            and not self.operator_id
        ):
            errors["operator"] = "Una solicitud en operacion debe registrar operador."
        if self.status == PrintRequestStatus.REJECTED and not self.rejection_reason:
            errors["rejection_reason"] = "Debe registrar motivo de rechazo."
        if self.status == PrintRequestStatus.CLOSED and not self.closed_at:
            errors["closed_at"] = (
                "Una solicitud cerrada debe registrar fecha de cierre."
            )
        if self.status == PrintRequestStatus.CLOSED and not self.closed_by_id:
            errors["closed_by"] = "Una solicitud cerrada debe registrar quien la cerro."
        if self.status == PrintRequestStatus.CANCELLED and not self.cancelled_at:
            errors["cancelled_at"] = (
                "Una solicitud cancelada debe registrar fecha de cancelacion."
            )
        if self.status == PrintRequestStatus.CANCELLED and not self.cancelled_by_id:
            errors["cancelled_by"] = (
                "Una solicitud cancelada debe registrar quien la cancelo."
            )
        if errors:
            raise ValidationError(errors)


class PrintRequestItem(BaseModel):
    request = models.ForeignKey(
        PrintRequest,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Solicitud",
    )
    line_number = models.PositiveIntegerField(verbose_name="Linea")
    document_title = models.CharField(max_length=180, verbose_name="Documento")
    page_size = models.CharField(
        max_length=10, choices=PrintPageSize.choices, default=PrintPageSize.A4
    )
    print_side = models.CharField(
        max_length=20, choices=PrintSide.choices, default=PrintSide.SINGLE
    )
    color_mode = models.CharField(
        max_length=20, choices=PrintColorMode.choices, default=PrintColorMode.BW
    )
    copy_count_requested = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Cantidad solicitada"
    )
    copy_count_approved = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad aprobada",
    )
    original_page_count = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)], verbose_name="Cantidad de paginas originales"
    )
    stapled = models.BooleanField(default=False, verbose_name="Corcheteado")
    collated = models.BooleanField(default=False, verbose_name="Ordenado")
    ring_bound = models.BooleanField(default=False, verbose_name="Anillado")
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        db_table = "tba_print_request_item"
        verbose_name = "Detalle de solicitud de impresion"
        verbose_name_plural = "Detalles de solicitud de impresion"
        ordering = ["line_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "line_number"], name="uniq_print_request_item_line"
            ),
        ]
        indexes = [
            models.Index(fields=["request", "line_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.request.numero} - {self.document_title}"

    def clean(self) -> None:
        errors = {}
        if (
            self.copy_count_approved
            and self.copy_count_approved > self.copy_count_requested
        ):
            errors["copy_count_approved"] = (
                "La cantidad aprobada no puede superar la solicitada."
            )
        if errors:
            raise ValidationError(errors)


class PrintRequestStatusHistory(BaseModel):
    request = models.ForeignKey(
        PrintRequest,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Solicitud",
    )
    from_status = models.CharField(
        max_length=30, blank=True, verbose_name="Estado origen"
    )
    to_status = models.CharField(
        max_length=30,
        choices=PrintRequestStatus.choices,
        db_index=True,
        verbose_name="Estado destino",
    )
    action = models.CharField(max_length=40, db_index=True, verbose_name="Accion")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Realizado por",
    )
    performed_at = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Fecha"
    )
    comment = models.TextField(blank=True, verbose_name="Comentario")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Payload")

    class Meta:
        db_table = "tba_print_request_status_history"
        verbose_name = "Historial de estado de impresion"
        verbose_name_plural = "Historial de estados de impresion"
        ordering = ["-performed_at", "-id"]
        indexes = [
            models.Index(fields=["request", "performed_at"]),
            models.Index(fields=["performed_by", "performed_at"]),
        ]


class PrintRequestComment(BaseModel):
    request = models.ForeignKey(
        PrintRequest,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Solicitud",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_request_comments",
        verbose_name="Autor",
    )
    comment_type = models.CharField(
        max_length=20,
        choices=PrintCommentType.choices,
        default=PrintCommentType.GENERAL,
    )
    body = models.TextField(verbose_name="Comentario")
    is_internal = models.BooleanField(default=False, verbose_name="Interno")

    class Meta:
        db_table = "tba_print_request_comment"
        verbose_name = "Comentario de solicitud de impresion"
        verbose_name_plural = "Comentarios de solicitudes de impresion"
        ordering = ["fecha_creacion", "id"]


class PrintRequestAttachment(BaseModel):
    request = models.ForeignKey(
        PrintRequest,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="Solicitud",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="print_request_attachments",
        verbose_name="Subido por",
    )
    file = models.FileField(
        upload_to="fotocopiadora/requests/%Y/%m/", verbose_name="Archivo"
    )
    original_name = models.CharField(max_length=255, verbose_name="Nombre original")
    mime_type = models.CharField(max_length=120, blank=True, verbose_name="Tipo MIME")
    size_bytes = models.PositiveBigIntegerField(
        default=0, verbose_name="Tamano en bytes"
    )

    class Meta:
        db_table = "tba_print_request_attachment"
        verbose_name = "Adjunto de solicitud de impresion"
        verbose_name_plural = "Adjuntos de solicitudes de impresion"
        ordering = ["fecha_creacion", "id"]
