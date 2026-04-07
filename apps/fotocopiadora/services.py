from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from apps.notificaciones.models import Notificacion
from core.utils import registrar_log_auditoria

from .models import (
    PrintMembershipRole,
    PrintRequest,
    PrintRequestStatus,
    PrintRequestStatusHistory,
    PrintRoleMembership,
)


class PrintRequestQueryService:
    ROLE_PRECEDENCE = (
        PrintMembershipRole.SUPERADMIN,
        PrintMembershipRole.ADMIN,
        PrintMembershipRole.OPERATOR,
        PrintMembershipRole.APPROVER,
        PrintMembershipRole.REQUESTER,
        PrintMembershipRole.AUDITOR,
    )

    @staticmethod
    def role_memberships(user, role: str | None = None):
        qs = PrintRoleMembership.objects.filter(user=user, activo=True, eliminado=False)
        if role:
            qs = qs.filter(role=role)
        return qs

    @staticmethod
    def active_memberships(user):
        return PrintRoleMembership.objects.filter(user=user, activo=True, eliminado=False).select_related(
            'departamento', 'area', 'equipo', 'cost_center'
        )

    @classmethod
    def primary_membership(cls, user):
        if not getattr(user, 'is_authenticated', False):
            return None
        if user.is_superuser:
            return {'role': PrintMembershipRole.SUPERADMIN, 'is_primary': True}

        memberships = list(cls.active_memberships(user))
        primary = [membership for membership in memberships if membership.is_primary]
        if len(primary) == 1:
            return primary[0]
        if len(primary) > 1:
            return None
        if len(memberships) == 1:
            return memberships[0]
        for role in cls.ROLE_PRECEDENCE:
            for membership in memberships:
                if membership.role == role:
                    return membership
        return None

    @classmethod
    def module_profile(cls, user) -> str | None:
        if not user.is_authenticated:
            return None
        if getattr(user, 'is_superuser', False):
            return PrintMembershipRole.SUPERADMIN

        # PRIORIDAD 1: Membresía en Base de Datos (Configurada manualmente por Admin)
        membership = cls.primary_membership(user)
        if membership:
            return membership['role'] if isinstance(membership, dict) else membership.role

        # PRIORIDAD 2: Solo si no hay membresía, miramos permisos específicos de Django (Fallback seguro)
        if (
            user.has_perm('fotocopiadora.manage_print_memberships')
            or user.has_perm('fotocopiadora.manage_print_settings')
            or user.has_perm('fotocopiadora.manage_print_cost_centers')
            or user.has_perm('fotocopiadora.view_all_printrequest')
        ):
            # Si tiene permisos globales de gestión o auditoría, es ADMIN o AUDITOR
            if user.has_perm('fotocopiadora.manage_print_memberships'):
                return PrintMembershipRole.ADMIN
            return PrintMembershipRole.AUDITOR

        # PRIORIDAD 3: Permisos de acción
        if user.has_perm('fotocopiadora.approve_printrequest'):
            return PrintMembershipRole.APPROVER
        if user.has_perm('fotocopiadora.operate_printrequest'):
            return PrintMembershipRole.OPERATOR
        if user.has_perm('fotocopiadora.add_printrequest') or user.has_perm('fotocopiadora.view_printrequest'):
            return PrintMembershipRole.REQUESTER
            
        return None

    @staticmethod
    def for_user(queryset, user):
        if not user.is_authenticated:
            return queryset.none()

        if user.is_superuser:
            return queryset

        profile = PrintRequestQueryService.module_profile(user)
        if profile in {PrintMembershipRole.ADMIN, PrintMembershipRole.AUDITOR, PrintMembershipRole.SUPERADMIN}:
            return queryset

        if user.has_perm('fotocopiadora.manage_print_memberships') or user.has_perm('fotocopiadora.manage_print_settings'):
            return queryset

        if profile == PrintMembershipRole.APPROVER:
            memberships = PrintRequestQueryService.role_memberships(user, PrintMembershipRole.APPROVER)
            if not memberships.exists():
                return queryset.none()
            department_ids = list(memberships.exclude(departamento=None).values_list('departamento_id', flat=True))
            area_ids = list(memberships.exclude(area=None).values_list('area_id', flat=True))
            return queryset.filter(
                models.Q(departamento_id__in=department_ids) |
                models.Q(area_id__in=area_ids) |
                models.Q(requester=user) |
                models.Q(approver=user)
            ).distinct()

        if profile == PrintMembershipRole.OPERATOR:
            memberships = PrintRequestQueryService.role_memberships(user, PrintMembershipRole.OPERATOR)
            if not memberships.exists():
                return queryset.none()
            equipment_ids = list(memberships.exclude(equipo=None).values_list('equipo_id', flat=True))
            base = queryset.filter(
                status__in=[
                    PrintRequestStatus.PENDING_APPROVAL,
                    PrintRequestStatus.APPROVED,
                    PrintRequestStatus.IN_PROGRESS,
                    PrintRequestStatus.READY_FOR_PICKUP,
                    PrintRequestStatus.DELIVERED,
                ]
            )
            if equipment_ids:
                base = base.filter(models.Q(equipo_id__in=equipment_ids) | models.Q(equipo=None))
            return base.distinct()

        return queryset.filter(requester=user)

    @classmethod
    def home_cards_for_user(cls, user):
        if user.is_superuser:
            return ['my_requests', 'approval_queue', 'operator_queue', 'admin_overview', 'memberships_admin', 'equipment_admin']
            
        active_roles = set(cls.active_memberships(user).values_list('role', flat=True))
        
        # Si no tiene memberships pero tiene permisos específicos via Django Auth
        if not active_roles:
            profile = cls.module_profile(user)
            if profile:
                active_roles.add(profile)

        cards = []
        if active_roles:
            # Todos los usuarios del módulo pueden ver sus propias solicitudes
            cards.append('my_requests')

        if PrintMembershipRole.APPROVER in active_roles:
            cards.append('approval_queue')
        if PrintMembershipRole.OPERATOR in active_roles:
            cards.append('operator_queue')
        if PrintMembershipRole.ADMIN in active_roles or user.has_perm('fotocopiadora.manage_print_memberships'):
            cards.extend(['admin_overview', 'memberships_admin', 'equipment_admin'])
        if PrintMembershipRole.AUDITOR in active_roles:
            cards.append('audit_overview')
            
        # Limpiar duplicados manteniendo el orden
        seen = set()
        return [x for x in cards if not (x in seen or seen.add(x))]

    @staticmethod
    def can_view(user, request_obj: PrintRequest) -> bool:
        return PrintRequestQueryService.for_user(
            PrintRequest.objects.filter(pk=request_obj.pk, eliminado=False),
            user,
        ).exists()

    @staticmethod
    def can_approve(user, request_obj: PrintRequest) -> bool:
        if not user.is_authenticated or not user.has_perm('fotocopiadora.approve_printrequest'):
            return False
            
        # BLOQUEO DE HIERRO: Un operador NO aprueba NUNCA (aunque tenga otros permisos)
        has_operator_membership = PrintRequestQueryService.active_memberships(user).filter(role=PrintMembershipRole.OPERATOR).exists()
        if has_operator_membership and not user.is_superuser:
            return False

        # Segregación: Solicitante no aprueba lo suyo
        if request_obj.requester_id == user.id and not user.is_superuser:
            return False
            
        profile = PrintRequestQueryService.module_profile(user)

        if user.is_superuser or profile == PrintMembershipRole.SUPERADMIN:
            return True

        # El rol de administrador (módulo) también puede aprobar por jerarquía
        if profile == PrintMembershipRole.ADMIN:
            return True

        # Validar membresía específica de JEFATURA para el área/depto
        memberships = PrintRequestQueryService.active_memberships(user).filter(role=PrintMembershipRole.APPROVER)
        if request_obj.area_id and memberships.filter(area_id=request_obj.area_id).exists():
            return True
        if request_obj.departamento_id and memberships.filter(departamento_id=request_obj.departamento_id).exists():
            return True
        return False

    @staticmethod
    def can_operate(user, request_obj: PrintRequest) -> bool:
        if not user.is_authenticated or not user.has_perm('fotocopiadora.operate_printrequest'):
            return False

        # El solicitante no debería operar su propio pedido
        if request_obj.requester_id == user.id and not user.is_superuser:
            return False

        profile = PrintRequestQueryService.module_profile(user)
        if user.is_superuser or profile in {PrintMembershipRole.ADMIN, PrintMembershipRole.SUPERADMIN}:
            return True

        # Solo si su perfil es explícitamente OPERADOR (o SuperUser/Admin arriba)
        if profile != PrintMembershipRole.OPERATOR:
            return False

        # Validar membresía específica de OPERADOR para el equipo/bodega
        memberships = PrintRequestQueryService.active_memberships(user).filter(role=PrintMembershipRole.OPERATOR)
        if not memberships.exists():
            return False
            
        if request_obj.equipo_id and memberships.filter(equipo_id=request_obj.equipo_id).exists():
            return True
        return memberships.filter(equipo=None).exists()

    @staticmethod
    def approvers_for_request(request_obj: PrintRequest):
        qs = PrintRoleMembership.objects.filter(
            activo=True,
            eliminado=False,
            role=PrintMembershipRole.APPROVER,
        )
        if request_obj.area_id:
            users = list(qs.filter(area_id=request_obj.area_id).values_list('user_id', flat=True))
            if users:
                return users
        if request_obj.departamento_id:
            return list(qs.filter(departamento_id=request_obj.departamento_id).values_list('user_id', flat=True))
        return []


class PrintRequestNotificationService:
    @staticmethod
    def _notify_users(user_ids: list[int], title: str, message: str, url: str) -> None:
        if not user_ids:
            return
        user_model = get_user_model()
        for user_id in set(user_ids):
            user = user_model.objects.filter(pk=user_id, is_active=True).first()
            if user is None:
                continue
            Notificacion.crear(destinatario=user, tipo='SISTEMA', titulo=title, mensaje=message, url=url)

    @classmethod
    def handle_transition(cls, request_obj: PrintRequest, action: str) -> None:
        detail_url = reverse('fotocopiadora:detalle_solicitud_impresion', args=[request_obj.pk])
        if action == 'SUBMIT' and request_obj.status == 'PENDING_APPROVAL':
            cls._notify_users(
                PrintRequestQueryService.approvers_for_request(request_obj),
                'Fotocopiadora',
                f'Nueva solicitud {request_obj.numero} pendiente de aprobacion.',
                detail_url,
            )
        elif action == 'APPROVE':
            cls._notify_users(
                [request_obj.requester_id],
                'Fotocopiadora',
                f'Su solicitud {request_obj.numero} fue aprobada.',
                detail_url,
            )
            operator_ids = list(
                PrintRoleMembership.objects.filter(
                    activo=True,
                    eliminado=False,
                    role=PrintMembershipRole.OPERATOR,
                ).values_list('user_id', flat=True)
            )
            cls._notify_users(
                operator_ids,
                'Fotocopiadora',
                f'La solicitud {request_obj.numero} quedo disponible en bandeja operativa.',
                detail_url,
            )
        elif action == 'REJECT':
            cls._notify_users(
                [request_obj.requester_id],
                'Fotocopiadora',
                f'Su solicitud {request_obj.numero} fue rechazada.',
                detail_url,
            )
        elif action == 'READY':
            cls._notify_users(
                [request_obj.requester_id],
                'Fotocopiadora',
                f'Su solicitud {request_obj.numero} esta lista para retiro.',
                detail_url,
            )


@dataclass(frozen=True)
class TransitionRule:
    from_statuses: tuple[str, ...]
    to_status: str
    permission: str


class PrintRequestTransitionService:
    RULES = {
        'SUBMIT': TransitionRule((PrintRequestStatus.DRAFT,), PrintRequestStatus.PENDING_APPROVAL, 'fotocopiadora.submit_printrequest'),
        'APPROVE': TransitionRule((PrintRequestStatus.PENDING_APPROVAL,), PrintRequestStatus.APPROVED, 'fotocopiadora.approve_printrequest'),
        'REJECT': TransitionRule((PrintRequestStatus.PENDING_APPROVAL,), PrintRequestStatus.REJECTED, 'fotocopiadora.reject_printrequest'),
        'START': TransitionRule((PrintRequestStatus.APPROVED,), PrintRequestStatus.IN_PROGRESS, 'fotocopiadora.operate_printrequest'),
        'READY': TransitionRule((PrintRequestStatus.IN_PROGRESS,), PrintRequestStatus.READY_FOR_PICKUP, 'fotocopiadora.mark_ready_printrequest'),
        'DELIVER': TransitionRule((PrintRequestStatus.READY_FOR_PICKUP,), PrintRequestStatus.DELIVERED, 'fotocopiadora.deliver_printrequest'),
        'CLOSE': TransitionRule((PrintRequestStatus.DELIVERED,), PrintRequestStatus.CLOSED, 'fotocopiadora.close_printrequest'),
        'CANCEL': TransitionRule(
            (PrintRequestStatus.DRAFT, PrintRequestStatus.PENDING_APPROVAL),
            PrintRequestStatus.CANCELLED,
            'fotocopiadora.cancel_own_printrequest',
        ),
    }

    @classmethod
    @transaction.atomic
    def transition(cls, *, request_obj: PrintRequest, action: str, actor, request, comment: str = '', total_price: Decimal = None, pin_to_verify: str = None) -> PrintRequest:
        action = action.upper()
        request_obj = PrintRequest.objects.select_for_update().prefetch_related('items').get(
            pk=request_obj.pk,
            eliminado=False,
        )
        if action not in cls.RULES:
            raise ValidationError('Accion de flujo no soportada.')

        rule = cls.RULES[action]
        if request_obj.status not in rule.from_statuses:
            raise ValidationError(f'La transicion {action} no es valida para el estado {request_obj.status}.')

        if not actor.has_perm(rule.permission) and not actor.is_superuser:
            raise PermissionDenied('No tiene permisos para ejecutar esta accion.')

        cls._validate_scope(request_obj=request_obj, actor=actor, action=action)

        old_status = request_obj.status
        request_obj.status = rule.to_status
        now = timezone.now()

        if action == 'SUBMIT':
            request_obj.submitted_at = now
            # RECO: Las solicitudes de USO PERSONAL no requieren aprobación de jefatura
            if request_obj.use_type == 'PERSONAL':
                request_obj.status = PrintRequestStatus.APPROVED
                request_obj.approved_at = now
                request_obj.approver = actor
                request_obj.approval_comment = "Aprobación automática por Uso Personal."
                # Inicializar cantidades aprobadas
                for item in request_obj.items.all():
                    item.copy_count_approved = item.copy_count_requested
                    item.save(update_fields=['copy_count_approved', 'fecha_actualizacion'])
        elif action == 'APPROVE':
            request_obj.approver = actor
            request_obj.approved_at = now
            request_obj.approval_comment = comment
            partial = False
            for item in request_obj.items.all():
                if not item.copy_count_approved:
                    item.copy_count_approved = item.copy_count_requested
                    item.save(update_fields=['copy_count_approved', 'fecha_actualizacion'])
                if item.copy_count_approved < item.copy_count_requested:
                    partial = True
            request_obj.is_partial_approval = partial
        elif action == 'REJECT':
            if not comment.strip():
                raise ValidationError('Debe registrar una observacion de rechazo.')
            request_obj.approver = actor
            request_obj.rejected_at = now
            request_obj.rejection_reason = comment
        elif action == 'START':
            request_obj.operator = actor
            request_obj.started_at = now
            request_obj.operator_comment = comment
        elif action == 'READY':
            request_obj.ready_at = now
            request_obj.operator_comment = comment or request_obj.operator_comment
            if request_obj.use_type == 'PERSONAL' and total_price is not None:
                request_obj.total_price = total_price
        elif action == 'DELIVER':
            # Verificar PIN del solicitante si se requiere firma
            if not pin_to_verify:
                raise ValidationError('El PIN del solicitante es obligatorio para confirmar la entrega.')
            
            from apps.accounts.models import UserSecure
            try:
                security = request_obj.requester.seguridad
                if not security.verificar_pin(pin_to_verify):
                    raise ValidationError('El PIN ingresado no es correcto.')
            except AttributeError:
                raise ValidationError('El solicitante no tiene un perfil de seguridad (PIN) configurado.')

            request_obj.delivered_at = now
            request_obj.delivery_comment = comment
        elif action == 'CLOSE':
            request_obj.closed_by = actor
            request_obj.closed_at = now
            request_obj.close_reason = comment
        elif action == 'CANCEL':
            if not comment.strip():
                raise ValidationError('Debe registrar una observacion de cancelacion.')
            request_obj.cancelled_by = actor
            request_obj.cancelled_at = now

        request_obj.full_clean()
        request_obj.save()

        PrintRequestStatusHistory.objects.create(
            request=request_obj,
            from_status=old_status,
            to_status=request_obj.status,
            action=action,
            performed_by=actor,
            comment=comment,
            payload={},
        )

        registrar_log_auditoria(
            usuario=actor,
            accion_glosa=f'FOTOCOPIADORA_{action}',
            descripcion=f'Solicitud {request_obj.numero}: {old_status} -> {request_obj.status}',
            request=request,
            meta={'print_request_id': request_obj.pk, 'action': action},
        )

        PrintRequestNotificationService.handle_transition(request_obj, action)
        return request_obj

    @staticmethod
    def _validate_scope(*, request_obj: PrintRequest, actor, action: str) -> None:
        if action in {'APPROVE', 'REJECT'} and not PrintRequestQueryService.can_approve(actor, request_obj):
            raise PermissionDenied('No puede aprobar solicitudes fuera de su ambito.')
        if action in {'START', 'READY', 'DELIVER', 'CLOSE'} and not PrintRequestQueryService.can_operate(actor, request_obj):
            raise PermissionDenied('No puede operar esta solicitud.')
        if action == 'CANCEL' and request_obj.requester_id != actor.id and not actor.has_perm('fotocopiadora.cancel_any_printrequest') and not actor.is_superuser:
            raise PermissionDenied('Solo puede cancelar sus propias solicitudes.')
