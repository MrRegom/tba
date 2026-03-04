from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.solicitudes.models import Area, Departamento
from core.models import BaseModel
from core.utils import generar_codigo_unico, validar_rut, format_rut


class FotocopiadoraEquipo(BaseModel):
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Codigo')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    ubicacion = models.CharField(max_length=150, verbose_name='Ubicacion')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripcion')

    class Meta:
        db_table = 'tba_fotocopiadora_equipo'
        verbose_name = 'Equipo Fotocopiadora'
        verbose_name_plural = 'Equipos Fotocopiadora'
        ordering = ['codigo']

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class TrabajoFotocopia(BaseModel):
    class TipoUso(models.TextChoices):
        INTERNO = 'INTERNO', 'Uso Interno'
        PERSONAL = 'PERSONAL', 'Uso Personal'
        EXTERNO = 'EXTERNO', 'Uso Externo'

    numero = models.CharField(max_length=20, unique=True, verbose_name='Numero')
    fecha_hora = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Fecha y Hora')
    tipo_uso = models.CharField(max_length=20, choices=TipoUso.choices, verbose_name='Tipo de Uso')

    equipo = models.ForeignKey(
        FotocopiadoraEquipo,
        on_delete=models.PROTECT,
        related_name='trabajos',
        verbose_name='Equipo',
    )

    solicitante_usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trabajos_fotocopia',
        verbose_name='Solicitante (Usuario)',
    )
    solicitante_nombre = models.CharField(max_length=200, verbose_name='Solicitante')
    rut_solicitante = models.CharField(max_length=12, blank=True, null=True, verbose_name='RUT Solicitante')

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='trabajos_fotocopia',
        verbose_name='Departamento',
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='trabajos_fotocopia',
        verbose_name='Area',
    )

    cantidad_copias = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Cantidad de Copias')
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Precio Unitario',
    )
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Monto Total',
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'tba_fotocopiadora_trabajo'
        verbose_name = 'Trabajo Fotocopia'
        verbose_name_plural = 'Trabajos Fotocopia'
        ordering = ['-fecha_hora', '-numero']
        indexes = [
            models.Index(fields=['-fecha_hora']),
            models.Index(fields=['tipo_uso', '-fecha_hora']),
            models.Index(fields=['equipo', '-fecha_hora']),
            models.Index(fields=['rut_solicitante']),
        ]
        permissions = [
            ('registrar_trabajo_interno', 'Puede registrar trabajo interno de fotocopiadora'),
            ('registrar_trabajo_cobro', 'Puede registrar trabajo con cobro informativo'),
            ('anular_trabajo_fotocopia', 'Puede anular trabajos de fotocopiadora'),
            ('ver_reportes_fotocopiadora', 'Puede ver reportes de fotocopiadora'),
            ('gestionar_equipos_fotocopiadora', 'Puede gestionar equipos de fotocopiadora'),
        ]

    def __str__(self) -> str:
        return f"{self.numero} - {self.solicitante_nombre} ({self.tipo_uso})"

    def clean(self) -> None:
        errors = {}

        if self.tipo_uso == self.TipoUso.INTERNO:
            if not self.departamento and not self.area:
                errors['departamento'] = 'Para uso interno debe indicar departamento o area.'
            self.rut_solicitante = None
            self.precio_unitario = Decimal('0')
            self.monto_total = Decimal('0')

        if self.tipo_uso in {self.TipoUso.PERSONAL, self.TipoUso.EXTERNO}:
            if not self.rut_solicitante:
                errors['rut_solicitante'] = 'El RUT es obligatorio para uso personal o externo.'
            elif not validar_rut(self.rut_solicitante):
                errors['rut_solicitante'] = 'RUT invalido.'
            else:
                self.rut_solicitante = format_rut(self.rut_solicitante)

            if self.precio_unitario is None:
                errors['precio_unitario'] = 'El precio unitario es obligatorio para uso personal o externo.'

        if self.cantidad_copias <= 0:
            errors['cantidad_copias'] = 'La cantidad de copias debe ser mayor a cero.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        if not self.numero:
            self.numero = generar_codigo_unico('FOT', TrabajoFotocopia, 'numero', longitud=8)

        if self.tipo_uso == self.TipoUso.INTERNO:
            self.precio_unitario = Decimal('0')
            self.monto_total = Decimal('0')
        elif self.precio_unitario is not None:
            self.monto_total = Decimal(self.cantidad_copias) * self.precio_unitario

        super().save(*args, **kwargs)
