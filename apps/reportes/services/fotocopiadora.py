from __future__ import annotations

from datetime import date
from typing import List, Optional

from django.db.models import Sum

from apps.reportes.dtos import ReportResult
from apps.fotocopiadora.models import TrabajoFotocopia


class ConsumoInternoFotocopiaService:
    """Reporte de consumo interno de fotocopias por area/departamento."""

    def run(
        self,
        desde: date,
        hasta: date,
        equipo_id: Optional[int] = None,
        departamento_id: Optional[int] = None,
    ) -> ReportResult:
        qs = TrabajoFotocopia.objects.filter(
            eliminado=False,
            tipo_uso=TrabajoFotocopia.TipoUso.INTERNO,
            fecha_hora__date__gte=desde,
            fecha_hora__date__lte=hasta,
        ).select_related('equipo', 'departamento', 'area')

        if equipo_id:
            qs = qs.filter(equipo_id=equipo_id)
        if departamento_id:
            qs = qs.filter(departamento_id=departamento_id)

        rows: List[List] = []
        for item in qs.order_by('-fecha_hora'):
            rows.append([
                item.numero,
                item.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                item.equipo.nombre,
                item.solicitante_nombre,
                item.departamento.nombre if item.departamento else '',
                item.area.nombre if item.area else '',
                item.cantidad_copias,
            ])

        return ReportResult(
            title='Consumo Interno de Fotocopiadora',
            columns=['Numero', 'Fecha', 'Equipo', 'Solicitante', 'Departamento', 'Area', 'Copias'],
            rows=rows,
            totals={'copias_total': qs.aggregate(total=Sum('cantidad_copias'))['total'] or 0},
            filters_summary={
                'desde': desde.strftime('%d/%m/%Y'),
                'hasta': hasta.strftime('%d/%m/%Y'),
                'equipo_id': equipo_id,
                'departamento_id': departamento_id,
            },
        )


class CobrosFotocopiaService:
    """Reporte de copias con cobro informativo."""

    def run(
        self,
        desde: date,
        hasta: date,
        equipo_id: Optional[int] = None,
        tipo_uso: Optional[str] = None,
    ) -> ReportResult:
        qs = TrabajoFotocopia.objects.filter(
            eliminado=False,
            tipo_uso__in=[TrabajoFotocopia.TipoUso.PERSONAL, TrabajoFotocopia.TipoUso.EXTERNO],
            fecha_hora__date__gte=desde,
            fecha_hora__date__lte=hasta,
        ).select_related('equipo')

        if equipo_id:
            qs = qs.filter(equipo_id=equipo_id)
        if tipo_uso:
            qs = qs.filter(tipo_uso=tipo_uso)

        rows: List[List] = []
        for item in qs.order_by('-fecha_hora'):
            rows.append([
                item.numero,
                item.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                item.get_tipo_uso_display(),
                item.equipo.nombre,
                item.solicitante_nombre,
                item.rut_solicitante or '',
                item.cantidad_copias,
                item.precio_unitario,
                item.monto_total,
            ])

        aggregates = qs.aggregate(
            copias_total=Sum('cantidad_copias'),
            monto_total=Sum('monto_total'),
        )

        return ReportResult(
            title='Copias con Cobro Informativo',
            columns=['Numero', 'Fecha', 'Tipo', 'Equipo', 'Solicitante', 'RUT', 'Copias', 'Precio Unitario', 'Monto Total'],
            rows=rows,
            totals={
                'copias_total': aggregates['copias_total'] or 0,
                'monto_total': aggregates['monto_total'] or 0,
            },
            filters_summary={
                'desde': desde.strftime('%d/%m/%Y'),
                'hasta': hasta.strftime('%d/%m/%Y'),
                'equipo_id': equipo_id,
                'tipo_uso': tipo_uso,
            },
        )
