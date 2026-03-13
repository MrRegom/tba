from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import BaseAuditedViewMixin, PaginatedListMixin, ScopedObjectPermissionMixin, SoftDeleteMixin

from .forms import (
    FiltroTrabajoFotocopiaForm,
    FotocopiadoraEquipoForm,
    PrintRequestApprovalForm,
    PrintRequestAttachmentForm,
    PrintRequestForm,
    PrintRequestItemFormSet,
    PrintRequestTransitionCommentForm,
    TrabajoFotocopiaForm,
)
from .models import FotocopiadoraEquipo, PrintRequest, PrintRequestAttachment, PrintRequestStatus, TrabajoFotocopia
from .services import PrintRequestQueryService, PrintRequestTransitionService


class MenuFotocopiadoraView(BaseAuditedViewMixin, TemplateView):
    template_name = 'fotocopiadora/menu_fotocopiadora.html'
    permission_required = 'fotocopiadora.view_printrequest'

    def has_permission(self):
        user = self.request.user
        return user.has_perm('fotocopiadora.view_printrequest') or user.has_perm('fotocopiadora.view_trabajofotocopia')

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
        workflow_qs = PrintRequestQueryService.for_user(
            PrintRequest.objects.filter(eliminado=False),
            self.request.user,
        )
        context['workflow_stats'] = {
            'mis_solicitudes': workflow_qs.filter(requester=self.request.user).count(),
            'pendientes_aprobacion': workflow_qs.filter(status=PrintRequestStatus.PENDING_APPROVAL).count(),
            'pendientes_operacion': workflow_qs.filter(
                status__in=[PrintRequestStatus.APPROVED, PrintRequestStatus.IN_PROGRESS]
            ).count(),
            'listas_retiro': workflow_qs.filter(status=PrintRequestStatus.READY_FOR_PICKUP).count(),
        }

        user = self.request.user
        context['permisos'] = {
            'puede_crear': user.has_perm('fotocopiadora.add_trabajofotocopia'),
            'puede_gestionar': user.has_perm('fotocopiadora.change_trabajofotocopia'),
            'puede_gestionar_equipos': user.has_perm('fotocopiadora.gestionar_equipos_fotocopiadora'),
            'puede_reportes': user.has_perm('fotocopiadora.ver_reportes_fotocopiadora'),
            'puede_crear_solicitud': user.has_perm('fotocopiadora.add_printrequest'),
            'puede_ver_solicitudes': user.has_perm('fotocopiadora.view_printrequest'),
            'puede_aprobar': user.has_perm('fotocopiadora.approve_printrequest'),
            'puede_operar_bandeja': user.has_perm('fotocopiadora.view_operational_queue_printrequest'),
            'puede_ver_todo_workflow': user.has_perm('fotocopiadora.view_all_printrequest'),
        }
        return context


class PrintRequestScopedMixin:
    def get_base_queryset(self):
        return PrintRequest.objects.filter(eliminado=False).select_related(
            'requester', 'approver', 'operator', 'departamento', 'area', 'equipo', 'cost_center'
        ).prefetch_related('items', 'status_history', 'attachments')

    def get_queryset(self):
        return PrintRequestQueryService.for_user(self.get_base_queryset(), self.request.user)


class MyPrintRequestListView(BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/my_list.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_printrequest'

    def get_queryset(self):
        return super().get_queryset().filter(requester=self.request.user).order_by('-fecha_creacion')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Mis Solicitudes de Impresion'
        context['queue_mode'] = 'mine'
        return context


class ApprovalQueueListView(BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/approval_queue.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_department_printrequest'

    def get_queryset(self):
        return super().get_queryset().filter(status=PrintRequestStatus.PENDING_APPROVAL).order_by('required_at', '-priority')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Bandeja de Aprobacion'
        return context


class OperatorQueueListView(BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/operator_queue.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_operational_queue_printrequest'

    def get_queryset(self):
        return super().get_queryset().filter(
            status__in=[
                PrintRequestStatus.APPROVED,
                PrintRequestStatus.IN_PROGRESS,
                PrintRequestStatus.READY_FOR_PICKUP,
                PrintRequestStatus.DELIVERED,
            ]
        ).order_by('required_at', '-priority')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Bandeja Operativa'
        return context


class WorkflowAdminListView(BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/admin_list.html'
    context_object_name = 'requests'
    paginate_by = 25
    permission_required = 'fotocopiadora.view_all_printrequest'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Todas las Solicitudes de Impresion'
        return context


class PrintRequestDetailView(ScopedObjectPermissionMixin, BaseAuditedViewMixin, DetailView):
    template_name = 'fotocopiadora/requests/detail.html'
    context_object_name = 'print_request'
    permission_required = 'fotocopiadora.view_printrequest'

    def get_queryset(self):
        return self.get_base_queryset()

    def get_base_queryset(self):
        return PrintRequest.objects.filter(eliminado=False).select_related(
            'requester', 'approver', 'operator', 'departamento', 'area', 'equipo', 'cost_center'
        ).prefetch_related('items', 'status_history', 'attachments', 'comments__author')

    def has_object_permission(self, obj) -> bool:
        return PrintRequestQueryService.can_view(self.request.user, obj)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        obj = self.object
        user = self.request.user
        context['titulo'] = f'Solicitud {obj.numero}'
        context['can_submit'] = obj.status == PrintRequestStatus.DRAFT and obj.requester_id == user.id and user.has_perm('fotocopiadora.submit_printrequest')
        context['can_cancel'] = obj.status in {PrintRequestStatus.DRAFT, PrintRequestStatus.PENDING_APPROVAL} and (
            obj.requester_id == user.id or user.has_perm('fotocopiadora.cancel_any_printrequest')
        )
        context['can_approve'] = obj.status == PrintRequestStatus.PENDING_APPROVAL and PrintRequestQueryService.can_approve(user, obj)
        context['can_operate'] = obj.status in {
            PrintRequestStatus.APPROVED,
            PrintRequestStatus.IN_PROGRESS,
            PrintRequestStatus.READY_FOR_PICKUP,
            PrintRequestStatus.DELIVERED,
        } and PrintRequestQueryService.can_operate(user, obj)
        context['approval_form'] = PrintRequestApprovalForm(request_obj=obj)
        context['transition_form'] = PrintRequestTransitionCommentForm()
        return context


class PrintRequestCreateView(BaseAuditedViewMixin, CreateView):
    model = PrintRequest
    form_class = PrintRequestForm
    template_name = 'fotocopiadora/requests/form.html'
    permission_required = 'fotocopiadora.add_printrequest'
    success_url = reverse_lazy('fotocopiadora:mis_solicitudes_impresion')
    audit_action = 'CREAR'
    audit_description_template = 'Creo solicitud de impresion {obj.numero}'
    success_message = 'Solicitud {obj.numero} creada exitosamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Solicitud de Impresion'
        context['action'] = 'Crear'
        context['formset'] = kwargs.get('formset') or PrintRequestItemFormSet()
        context['attachment_form'] = kwargs.get('attachment_form') or PrintRequestAttachmentForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = PrintRequestItemFormSet(request.POST)
        attachment_form = PrintRequestAttachmentForm(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid() and attachment_form.is_valid():
            return self.forms_valid(form, formset, attachment_form)
        return self.render_to_response(self.get_context_data(form=form, formset=formset, attachment_form=attachment_form))

    def forms_valid(self, form, formset, attachment_form):
        self.object = form.save(commit=False)
        self.object.requester = self.request.user
        self.object.source_mode = 'TEACHER_PORTAL'
        self.object.save()

        formset.instance = self.object
        items = formset.save(commit=False)
        line = 1
        for item in items:
            item.request = self.object
            item.line_number = line
            item.save()
            line += 1
        for deleted in formset.deleted_objects:
            deleted.delete()

        upload = attachment_form.cleaned_data.get('file')
        if upload:
            PrintRequestAttachment.objects.create(
                request=self.object,
                uploaded_by=self.request.user,
                file=upload,
                original_name=getattr(upload, 'name', 'archivo'),
                mime_type=getattr(upload, 'content_type', ''),
                size_bytes=getattr(upload, 'size', 0),
            )

        self.log_action(self.object, self.request)
        messages.success(self.request, self.get_success_message(self.object))
        return HttpResponseRedirect(self.get_success_url())


class PrintRequestUpdateView(ScopedObjectPermissionMixin, BaseAuditedViewMixin, UpdateView):
    model = PrintRequest
    form_class = PrintRequestForm
    template_name = 'fotocopiadora/requests/form.html'
    permission_required = 'fotocopiadora.change_printrequest'
    success_url = reverse_lazy('fotocopiadora:mis_solicitudes_impresion')
    audit_action = 'EDITAR'
    audit_description_template = 'Edito solicitud de impresion {obj.numero}'
    success_message = 'Solicitud {obj.numero} actualizada exitosamente.'

    def get_queryset(self):
        return PrintRequest.objects.filter(eliminado=False)

    def has_object_permission(self, obj) -> bool:
        return obj.requester_id == self.request.user.id and obj.status == PrintRequestStatus.DRAFT

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Solicitud {self.object.numero}'
        context['action'] = 'Editar'
        context['formset'] = kwargs.get('formset') or PrintRequestItemFormSet(instance=self.object)
        context['attachment_form'] = kwargs.get('attachment_form') or PrintRequestAttachmentForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = PrintRequestItemFormSet(request.POST, instance=self.object)
        attachment_form = PrintRequestAttachmentForm(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid() and attachment_form.is_valid():
            return self.forms_valid(form, formset, attachment_form)
        return self.render_to_response(self.get_context_data(form=form, formset=formset, attachment_form=attachment_form))

    def forms_valid(self, form, formset, attachment_form):
        self.object = form.save()
        items = formset.save(commit=False)
        line = 1
        for item in items:
            item.request = self.object
            item.line_number = line
            item.save()
            line += 1
        for deleted in formset.deleted_objects:
            deleted.delete()

        upload = attachment_form.cleaned_data.get('file')
        if upload:
            PrintRequestAttachment.objects.create(
                request=self.object,
                uploaded_by=self.request.user,
                file=upload,
                original_name=getattr(upload, 'name', 'archivo'),
                mime_type=getattr(upload, 'content_type', ''),
                size_bytes=getattr(upload, 'size', 0),
            )

        self.log_action(self.object, self.request)
        messages.success(self.request, self.get_success_message(self.object))
        return HttpResponseRedirect(self.get_success_url())


class PrintRequestTransitionView(ScopedObjectPermissionMixin, BaseAuditedViewMixin, DetailView):
    model = PrintRequest
    permission_required = 'fotocopiadora.view_printrequest'

    def get_queryset(self):
        return PrintRequest.objects.filter(eliminado=False).prefetch_related('items')

    def has_object_permission(self, obj) -> bool:
        return PrintRequestQueryService.can_view(self.request.user, obj)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action', '').upper()

        if action in {'APPROVE', 'REJECT'}:
            form = PrintRequestApprovalForm(request.POST, request_obj=self.object)
            if not form.is_valid():
                for _, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
                return redirect('fotocopiadora:detalle_solicitud_impresion', pk=self.object.pk)
            comment = form.cleaned_data.get('comment', '')
            if action == 'APPROVE':
                form.apply()
        else:
            form = PrintRequestTransitionCommentForm(request.POST)
            if not form.is_valid():
                messages.error(request, 'Debe corregir el comentario ingresado.')
                return redirect('fotocopiadora:detalle_solicitud_impresion', pk=self.object.pk)
            comment = form.cleaned_data.get('comment', '')

        try:
            PrintRequestTransitionService.transition(
                request_obj=self.object,
                action=action,
                actor=request.user,
                request=request,
                comment=comment,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Accion {action.lower()} ejecutada correctamente para la solicitud {self.object.numero}.')

        return redirect('fotocopiadora:detalle_solicitud_impresion', pk=self.object.pk)


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
