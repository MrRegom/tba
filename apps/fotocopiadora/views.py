from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import BaseAuditedViewMixin, PaginatedListMixin, SoftDeleteMixin

from .forms import FiltroTrabajoFotocopiaForm, FotocopiadoraEquipoForm, TrabajoFotocopiaForm
from .models import FotocopiadoraEquipo, TrabajoFotocopia


class MenuFotocopiadoraView(BaseAuditedViewMixin, TemplateView):
    template_name = 'fotocopiadora/menu_fotocopiadora.html'
    permission_required = 'fotocopiadora.view_trabajofotocopia'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        inicio_mes = hoy.replace(day=1)

        trabajos_mes = TrabajoFotocopia.objects.filter(
            eliminado=False,
            fecha_hora__date__gte=inicio_mes,
            fecha_hora__date__lte=hoy,
        )

        context['titulo'] = 'Fotocopiadora'
        context['stats'] = {
            'total_copias_mes': trabajos_mes.aggregate(total=Sum('cantidad_copias'))['total'] or 0,
            'copias_internas_mes': trabajos_mes.filter(tipo_uso=TrabajoFotocopia.TipoUso.INTERNO).aggregate(total=Sum('cantidad_copias'))['total'] or 0,
            'copias_cobro_mes': trabajos_mes.filter(tipo_uso__in=[TrabajoFotocopia.TipoUso.PERSONAL, TrabajoFotocopia.TipoUso.EXTERNO]).aggregate(total=Sum('cantidad_copias'))['total'] or 0,
            'monto_informativo_mes': trabajos_mes.aggregate(total=Sum('monto_total'))['total'] or Decimal('0'),
            'equipos_activos': FotocopiadoraEquipo.objects.filter(eliminado=False, activo=True).count(),
        }

        user = self.request.user
        context['permisos'] = {
            'puede_crear': user.has_perm('fotocopiadora.add_trabajofotocopia'),
            'puede_gestionar': user.has_perm('fotocopiadora.change_trabajofotocopia'),
            'puede_gestionar_equipos': user.has_perm('fotocopiadora.gestionar_equipos_fotocopiadora'),
            'puede_reportes': user.has_perm('fotocopiadora.ver_reportes_fotocopiadora'),
        }
        return context


class TrabajoFotocopiaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    model = TrabajoFotocopia
    template_name = 'fotocopiadora/lista_trabajos.html'
    context_object_name = 'trabajos'
    permission_required = 'fotocopiadora.view_trabajofotocopia'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[TrabajoFotocopia]:
        queryset = TrabajoFotocopia.objects.filter(eliminado=False).select_related(
            'equipo', 'solicitante_usuario', 'departamento', 'area'
        )

        form = FiltroTrabajoFotocopiaForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            if data.get('fecha_desde'):
                queryset = queryset.filter(fecha_hora__date__gte=data['fecha_desde'])
            if data.get('fecha_hasta'):
                queryset = queryset.filter(fecha_hora__date__lte=data['fecha_hasta'])
            if data.get('equipo'):
                queryset = queryset.filter(equipo=data['equipo'])
            if data.get('tipo_uso'):
                queryset = queryset.filter(tipo_uso=data['tipo_uso'])
            if data.get('solicitante'):
                q = data['solicitante']
                queryset = queryset.filter(
                    Q(solicitante_nombre__icontains=q) |
                    Q(solicitante_usuario__username__icontains=q)
                )
            if data.get('rut'):
                queryset = queryset.filter(rut_solicitante__icontains=data['rut'])

        return queryset.order_by('-fecha_hora', '-numero')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Trabajos de Fotocopiadora'
        context['form'] = FiltroTrabajoFotocopiaForm(self.request.GET)
        user = self.request.user
        context['permisos'] = {
            'puede_crear': user.has_perm('fotocopiadora.add_trabajofotocopia'),
            'puede_editar': user.has_perm('fotocopiadora.change_trabajofotocopia'),
            'puede_anular': user.has_perm('fotocopiadora.anular_trabajo_fotocopia'),
        }
        return context


class TrabajoFotocopiaDetailView(BaseAuditedViewMixin, DetailView):
    model = TrabajoFotocopia
    template_name = 'fotocopiadora/detalle_trabajo.html'
    context_object_name = 'trabajo'
    permission_required = 'fotocopiadora.view_trabajofotocopia'

    def get_queryset(self) -> QuerySet[TrabajoFotocopia]:
        return TrabajoFotocopia.objects.filter(eliminado=False).select_related(
            'equipo', 'solicitante_usuario', 'departamento', 'area'
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Trabajo {self.object.numero}'
        return context


class TrabajoFotocopiaCreateView(BaseAuditedViewMixin, CreateView):
    model = TrabajoFotocopia
    form_class = TrabajoFotocopiaForm
    template_name = 'fotocopiadora/form_trabajo.html'
    permission_required = 'fotocopiadora.add_trabajofotocopia'
    success_url = reverse_lazy('fotocopiadora:lista_trabajos')
    audit_action = 'CREAR'
    audit_description_template = 'Creo trabajo de fotocopiadora {obj.numero}'
    success_message = 'Trabajo {obj.numero} registrado exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Trabajo de Fotocopiadora'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not self.object.solicitante_usuario:
            self.object.solicitante_usuario = self.request.user
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class TrabajoFotocopiaUpdateView(BaseAuditedViewMixin, UpdateView):
    model = TrabajoFotocopia
    form_class = TrabajoFotocopiaForm
    template_name = 'fotocopiadora/form_trabajo.html'
    permission_required = 'fotocopiadora.change_trabajofotocopia'
    success_url = reverse_lazy('fotocopiadora:lista_trabajos')
    audit_action = 'EDITAR'
    audit_description_template = 'Edito trabajo de fotocopiadora {obj.numero}'
    success_message = 'Trabajo {obj.numero} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet[TrabajoFotocopia]:
        return TrabajoFotocopia.objects.filter(eliminado=False)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.has_perm('fotocopiadora.gestionar_equipos_fotocopiadora'):
            return super().dispatch(request, *args, **kwargs)

        limite = timezone.now() - timedelta(hours=24)
        if obj.solicitante_usuario_id != request.user.id or obj.fecha_hora < limite:
            return HttpResponseForbidden('No tiene permisos para editar este trabajo.')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Trabajo {self.object.numero}'
        context['action'] = 'Editar'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class TrabajoFotocopiaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    model = TrabajoFotocopia
    template_name = 'fotocopiadora/eliminar_trabajo.html'
    permission_required = 'fotocopiadora.anular_trabajo_fotocopia'
    success_url = reverse_lazy('fotocopiadora:lista_trabajos')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Anulo trabajo de fotocopiadora {obj.numero}'
    success_message = 'Trabajo {obj.numero} anulado correctamente.'

    def get_queryset(self) -> QuerySet[TrabajoFotocopia]:
        return TrabajoFotocopia.objects.filter(eliminado=False)


class EquipoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    model = FotocopiadoraEquipo
    template_name = 'fotocopiadora/equipos/lista.html'
    context_object_name = 'equipos'
    permission_required = 'fotocopiadora.gestionar_equipos_fotocopiadora'

    def get_queryset(self) -> QuerySet[FotocopiadoraEquipo]:
        return FotocopiadoraEquipo.objects.filter(eliminado=False).order_by('codigo')


class EquipoCreateView(BaseAuditedViewMixin, CreateView):
    model = FotocopiadoraEquipo
    form_class = FotocopiadoraEquipoForm
    template_name = 'fotocopiadora/equipos/form.html'
    permission_required = 'fotocopiadora.gestionar_equipos_fotocopiadora'
    success_url = reverse_lazy('fotocopiadora:lista_equipos')
    audit_action = 'CREAR'
    audit_description_template = 'Creo equipo de fotocopiadora {obj.codigo}'
    success_message = 'Equipo {obj.codigo} creado correctamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Equipo de Fotocopiadora'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class EquipoUpdateView(BaseAuditedViewMixin, UpdateView):
    model = FotocopiadoraEquipo
    form_class = FotocopiadoraEquipoForm
    template_name = 'fotocopiadora/equipos/form.html'
    permission_required = 'fotocopiadora.gestionar_equipos_fotocopiadora'
    success_url = reverse_lazy('fotocopiadora:lista_equipos')
    audit_action = 'EDITAR'
    audit_description_template = 'Edito equipo de fotocopiadora {obj.codigo}'
    success_message = 'Equipo {obj.codigo} actualizado correctamente.'

    def get_queryset(self) -> QuerySet[FotocopiadoraEquipo]:
        return FotocopiadoraEquipo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Equipo {self.object.codigo}'
        context['action'] = 'Editar'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class EquipoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    model = FotocopiadoraEquipo
    template_name = 'fotocopiadora/equipos/eliminar.html'
    permission_required = 'fotocopiadora.gestionar_equipos_fotocopiadora'
    success_url = reverse_lazy('fotocopiadora:lista_equipos')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Elimino equipo de fotocopiadora {obj.codigo}'
    success_message = 'Equipo {obj.codigo} eliminado correctamente.'

    def get_queryset(self) -> QuerySet[FotocopiadoraEquipo]:
        return FotocopiadoraEquipo.objects.filter(eliminado=False)
