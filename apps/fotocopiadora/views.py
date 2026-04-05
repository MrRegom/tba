from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import BaseAuditedViewMixin, PaginatedListMixin, ScopedObjectPermissionMixin, SoftDeleteMixin
from apps.solicitudes.models import Area, Departamento

from .forms import (
    FotocopiadoraEquipoForm,
    PrintRequestApprovalForm,
    PrintRequestAttachmentForm,
    PrintRequestForm,
    PrintRequestItemFormSet,
    PrintRoleMembershipForm,
    PrintRequestTransitionCommentForm,
)
from .models import FotocopiadoraEquipo, PrintMembershipRole, PrintRequest, PrintRequestAttachment, PrintRequestStatus, PrintRoleMembership
from .services import PrintRequestQueryService, PrintRequestTransitionService


class MenuFotocopiadoraView(BaseAuditedViewMixin, TemplateView):
    template_name = 'fotocopiadora/menu_fotocopiadora.html'
    permission_required = 'fotocopiadora.view_printrequest'

    def has_permission(self):
        return self.request.user.has_perm('fotocopiadora.view_printrequest')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        workflow_qs = PrintRequestQueryService.for_user(
            PrintRequest.objects.filter(eliminado=False),
            user,
        )
        profile = PrintRequestQueryService.module_profile(user)
        primary_membership = PrintRequestQueryService.primary_membership(user)

        context['titulo'] = 'Fotocopiadora'
        context['stats'] = {
            'mis_solicitudes': workflow_qs.filter(requester=user).count(),
            'pendientes_aprobacion': workflow_qs.filter(status=PrintRequestStatus.PENDING_APPROVAL).count(),
            'pendientes_operacion': workflow_qs.filter(status__in=[PrintRequestStatus.APPROVED, PrintRequestStatus.IN_PROGRESS]).count(),
            'listas_retiro': workflow_qs.filter(status=PrintRequestStatus.READY_FOR_PICKUP).count(),
        }
        context['module_profile'] = profile
        context['primary_membership'] = primary_membership
        card_definitions = {
            'my_requests': {
                'tag': 'Solicitud docente',
                'title': 'Mis Solicitudes',
                'description': 'Consulte el estado, historial y observaciones de sus requerimientos.',
                'actions': [
                    {'label': 'Ver bandeja', 'url': reverse('fotocopiadora:mis_solicitudes_impresion'), 'style': 'primary'},
                    {'label': 'Nueva', 'url': reverse('fotocopiadora:crear_solicitud_impresion'), 'style': 'outline'},
                ],
            },
            'approval_queue': {
                'tag': 'Aprobación',
                'title': 'Bandeja de Aprobación',
                'description': 'Revise las solicitudes del área, apruebe, rechace o ajuste cantidades.',
                'actions': [
                    {'label': 'Gestionar', 'url': reverse('fotocopiadora:bandeja_aprobacion_impresion'), 'style': 'primary'},
                ],
            },
            'operator_queue': {
                'tag': 'Operación',
                'title': 'Bandeja Operativa',
                'description': 'Tome trabajos aprobados, marque preparación, retiro y entrega.',
                'actions': [
                    {'label': 'Abrir bandeja', 'url': reverse('fotocopiadora:bandeja_operativa_impresion'), 'style': 'primary'},
                ],
            },
            'admin_overview': {
                'tag': 'Supervisión',
                'title': 'Control Global',
                'description': 'Supervise todas las solicitudes del módulo con trazabilidad completa.',
                'actions': [
                    {'label': 'Ver todas', 'url': reverse('fotocopiadora:lista_solicitudes_impresion'), 'style': 'primary'},
                ],
            },
            'memberships_admin': {
                'tag': 'Administración',
                'title': 'Memberships',
                'description': 'Administre perfiles principales, ámbitos y vigencias del módulo.',
                'actions': [
                    {'label': 'Gestionar', 'url': reverse('fotocopiadora:lista_memberships'), 'style': 'primary'},
                ],
            },
            'equipment_admin': {
                'tag': 'Parámetros',
                'title': 'Equipos',
                'description': 'Administre equipos, ubicaciones y capacidad operativa del módulo.',
                'actions': [
                    {'label': 'Gestionar equipos', 'url': reverse('fotocopiadora:lista_equipos'), 'style': 'primary'},
                ],
            },
            'audit_overview': {
                'tag': 'Consulta',
                'title': 'Consulta Global',
                'description': 'Revise solicitudes, historial y trazabilidad sin acciones operativas.',
                'actions': [
                    {'label': 'Ver solicitudes', 'url': reverse('fotocopiadora:lista_solicitudes_impresion'), 'style': 'primary'},
                ],
            },
        }
        context['cards'] = [card_definitions[key] for key in PrintRequestQueryService.home_cards_for_user(user) if key in card_definitions]
        return context


class PrintRequestScopedMixin:
    def get_base_queryset(self):
        return PrintRequest.objects.filter(eliminado=False).select_related(
            'requester', 'approver', 'operator', 'departamento', 'area', 'equipo', 'cost_center'
        ).prefetch_related('items', 'status_history', 'attachments')

    def get_queryset(self):
        return PrintRequestQueryService.for_user(self.get_base_queryset(), self.request.user)


class ModuleProfileRequiredMixin:
    allowed_profiles: tuple[str, ...] = tuple()

    def dispatch(self, request, *args, **kwargs):
        profile = PrintRequestQueryService.module_profile(request.user)
        if self.allowed_profiles and profile not in self.allowed_profiles and not request.user.is_superuser:
            messages.error(request, 'Su perfil principal del modulo no permite acceder a esta pantalla.')
            return redirect('fotocopiadora:menu_fotocopiadora')
        return super().dispatch(request, *args, **kwargs)


class MyPrintRequestListView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/my_list.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_printrequest'
    allowed_profiles = (PrintMembershipRole.REQUESTER, PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)

    def get_queryset(self):
        return super().get_queryset().filter(requester=self.request.user).order_by('-fecha_creacion')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Mis Solicitudes de Impresion'
        context['queue_mode'] = 'mine'
        return context


class ApprovalQueueListView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/approval_queue.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_department_printrequest'
    allowed_profiles = (PrintMembershipRole.APPROVER, PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)

    def get_queryset(self):
        return super().get_queryset().filter(status=PrintRequestStatus.PENDING_APPROVAL).order_by('required_at', '-priority')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Bandeja de Aprobacion'
        return context


class OperatorQueueListView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/operator_queue.html'
    context_object_name = 'requests'
    paginate_by = 20
    permission_required = 'fotocopiadora.view_operational_queue_printrequest'
    allowed_profiles = (PrintMembershipRole.OPERATOR, PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)

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


class WorkflowAdminListView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, PrintRequestScopedMixin, PaginatedListMixin, ListView):
    template_name = 'fotocopiadora/requests/admin_list.html'
    context_object_name = 'requests'
    paginate_by = 25
    permission_required = 'fotocopiadora.view_all_printrequest'
    allowed_profiles = (PrintMembershipRole.ADMIN, PrintMembershipRole.AUDITOR, PrintMembershipRole.SUPERADMIN)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Todas las Solicitudes de Impresion'
        return context


class MembershipListView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, PaginatedListMixin, ListView):
    model = PrintRoleMembership
    template_name = 'fotocopiadora/memberships/list.html'
    context_object_name = 'memberships'
    paginate_by = 25
    permission_required = 'fotocopiadora.manage_print_memberships'
    allowed_profiles = (PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)

    def get_queryset(self):
        return PrintRoleMembership.objects.filter(eliminado=False).select_related(
            'user', 'departamento', 'area', 'equipo', 'cost_center'
        ).order_by('user__username', 'role')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Memberships de Fotocopiadora'
        return context


class MembershipCreateView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, CreateView):
    model = PrintRoleMembership
    form_class = PrintRoleMembershipForm
    template_name = 'fotocopiadora/memberships/form.html'
    permission_required = 'fotocopiadora.manage_print_memberships'
    success_url = reverse_lazy('fotocopiadora:lista_memberships')
    allowed_profiles = (PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)
    audit_action = 'CREAR'
    audit_description_template = 'Creo membership de fotocopiadora {obj}'
    success_message = 'Membership creado correctamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Membership'
        context['action'] = 'Crear'
        return context


class MembershipUpdateView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, UpdateView):
    model = PrintRoleMembership
    form_class = PrintRoleMembershipForm
    template_name = 'fotocopiadora/memberships/form.html'
    permission_required = 'fotocopiadora.manage_print_memberships'
    success_url = reverse_lazy('fotocopiadora:lista_memberships')
    allowed_profiles = (PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)
    audit_action = 'EDITAR'
    audit_description_template = 'Edito membership de fotocopiadora {obj}'
    success_message = 'Membership actualizado correctamente.'

    def get_queryset(self):
        return PrintRoleMembership.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Membership'
        context['action'] = 'Guardar cambios'
        return context


class MembershipDeleteView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    model = PrintRoleMembership
    template_name = 'fotocopiadora/memberships/delete.html'
    permission_required = 'fotocopiadora.manage_print_memberships'
    success_url = reverse_lazy('fotocopiadora:lista_memberships')
    allowed_profiles = (PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)
    audit_action = 'ELIMINAR'
    audit_description_template = 'Desactivo membership de fotocopiadora {obj}'
    success_message = 'Membership desactivado correctamente.'

    def get_queryset(self):
        return PrintRoleMembership.objects.filter(eliminado=False)


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


class PrintRequestCreateView(ModuleProfileRequiredMixin, BaseAuditedViewMixin, CreateView):
    model = PrintRequest
    form_class = PrintRequestForm
    template_name = 'fotocopiadora/requests/form.html'
    permission_required = 'fotocopiadora.add_printrequest'
    success_url = reverse_lazy('fotocopiadora:mis_solicitudes_impresion')
    allowed_profiles = (PrintMembershipRole.REQUESTER, PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)
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
        context['areas_all'] = Area.objects.filter(activo=True, eliminado=False).values('id', 'nombre', 'codigo', 'departamento_id')
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
        from .services import PrintRequestTransitionService
        with transaction.atomic():
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
                from .models import PrintRequestAttachment
                PrintRequestAttachment.objects.create(
                    request=self.object,
                    uploaded_by=self.request.user,
                    file=upload,
                    original_name=getattr(upload, 'name', 'archivo'),
                    mime_type=getattr(upload, 'content_type', ''),
                    size_bytes=getattr(upload, 'size', 0),
                )

        # Tratar de enviar a aprobacion automaticamente
        try:
            PrintRequestTransitionService.transition(
                request_obj=self.object,
                action='SUBMIT',
                actor=self.request.user,
                request=self.request,
                comment='Envio automatico al crear solicitud.'
            )
        except Exception:
            pass

        self.log_action(self.object, self.request)
        messages.success(self.request, self.get_success_message(self.object))
        return HttpResponseRedirect(self.get_success_url())


class PrintRequestUpdateView(ModuleProfileRequiredMixin, ScopedObjectPermissionMixin, BaseAuditedViewMixin, UpdateView):
    model = PrintRequest
    form_class = PrintRequestForm
    template_name = 'fotocopiadora/requests/form.html'
    permission_required = 'fotocopiadora.change_printrequest'
    success_url = reverse_lazy('fotocopiadora:mis_solicitudes_impresion')
    allowed_profiles = (PrintMembershipRole.REQUESTER, PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN)
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
        context['areas_all'] = Area.objects.filter(activo=True, eliminado=False).values('id', 'nombre', 'codigo', 'departamento_id')
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
        with transaction.atomic():
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
            from decimal import Decimal
            price_str = request.POST.get('total_price')
            total_price = Decimal(price_str) if price_str else None
            pin_to_verify = request.POST.get('pin')
            
            PrintRequestTransitionService.transition(
                request_obj=self.object,
                action=action,
                actor=request.user,
                request=request,
                comment=comment,
                total_price=total_price,
                pin_to_verify=pin_to_verify,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Accion {action.lower()} ejecutada correctamente para la solicitud {self.object.numero}.')

        return redirect('fotocopiadora:detalle_solicitud_impresion', pk=self.object.pk)


class LegacyWorkflowRetiredView(BaseAuditedViewMixin, TemplateView):
    permission_required = 'fotocopiadora.view_printrequest'

    def dispatch(self, request, *args, **kwargs):
        messages.warning(
            request,
            'El flujo manual de fotocopiadora fue retirado. Use exclusivamente el workflow oficial del modulo.'
        )
        return redirect('fotocopiadora:menu_fotocopiadora')


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
