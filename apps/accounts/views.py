from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.models import User, Group, Permission
from django.db import transaction
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import (
    UserCreateForm, UserUpdateForm, UserPasswordChangeForm,
    GroupForm, GroupPermissionsForm, UserGroupsForm, UserPermissionsForm,
    UserFilterForm, PermissionForm, CargoForm, PersonaForm, PINForm, UserCargoForm
)
from .models import AuthLogs, AuthLogAccion

# Importar utilidades centralizadas
from core.utils import registrar_log_auditoria
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin
)


# ========== MENÚ PRINCIPAL ==========

class MenuAdministracionView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Vista del menú principal de Administración.
    
    Incluye dos secciones:
    1. Administración de Usuarios (Usuarios, Roles/Grupos, Permisos)
    2. Organización (Ubicación, Talleres, Área, Departamentos)
    """
    template_name = 'account/menu_administracion.html'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar modelos de Organización
        from apps.activos.models import Ubicacion, Taller
        from apps.solicitudes.models import Area, Departamento

        # Estadísticas - Administración de Usuarios
        context['stats_usuarios'] = {
            'total_usuarios': User.objects.count(),
            'usuarios_activos': User.objects.filter(is_active=True).count(),
            'usuarios_staff': User.objects.filter(is_staff=True).count(),
            'total_grupos': Group.objects.count(),
            'total_permisos': Permission.objects.count(),
        }

        # Estadísticas - Organización
        context['stats_organizacion'] = {
            'total_ubicaciones': Ubicacion.objects.filter(eliminado=False).count(),
            'total_talleres': Taller.objects.filter(eliminado=False).count(),
            'total_areas': Area.objects.filter(eliminado=False).count(),
            'total_departamentos': Departamento.objects.filter(eliminado=False).count(),
        }

        # Permisos del usuario actual - Administración de Usuarios
        context['permisos_usuarios'] = {
            'puede_crear_usuarios': self.request.user.has_perm('auth.add_user'),
            'puede_editar_usuarios': self.request.user.has_perm('auth.change_user'),
            'puede_eliminar_usuarios': self.request.user.has_perm('auth.delete_user'),
            'puede_gestionar_grupos': self.request.user.has_perm('auth.change_group'),
            'puede_gestionar_permisos': self.request.user.has_perm('auth.view_permission'),
        }

        # Permisos del usuario actual - Organización
        context['permisos_organizacion'] = {
            'puede_gestionar_ubicacion': self.request.user.has_perm('activos.view_ubicacion'),
            'puede_gestionar_taller': self.request.user.has_perm('activos.view_taller'),
            'puede_gestionar_area': self.request.user.has_perm('solicitudes.view_area'),
            'puede_gestionar_departamento': self.request.user.has_perm('solicitudes.view_departamento'),
        }

        context['titulo'] = 'Administración'

        return context


# ========== GESTIÓN DE USUARIOS ==========

@login_required
@permission_required('auth.view_user', raise_exception=True)
def lista_usuarios(request):
    """Listar todos los usuarios con filtros"""
    form = UserFilterForm(request.GET or None)
    usuarios = User.objects.prefetch_related('groups').all()

    # Aplicar filtros
    if form.is_valid():
        buscar = form.cleaned_data.get('buscar')
        is_active = form.cleaned_data.get('is_active')
        is_staff = form.cleaned_data.get('is_staff')
        group = form.cleaned_data.get('group')

        if buscar:
            usuarios = usuarios.filter(
                Q(username__icontains=buscar) |
                Q(email__icontains=buscar) |
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar)
            )

        if is_active != '':
            usuarios = usuarios.filter(is_active=is_active)

        if is_staff != '':
            usuarios = usuarios.filter(is_staff=is_staff)

        if group:
            usuarios = usuarios.filter(groups=group)

    # Permisos
    permisos = {
        'puede_crear': request.user.has_perm('auth.add_user'),
        'puede_editar': request.user.has_perm('auth.change_user'),
        'puede_eliminar': request.user.has_perm('auth.delete_user'),
        'puede_cambiar_password': request.user.has_perm('auth.change_user'),
    }

    context = {
        'titulo': 'Listado de Usuarios',
        'usuarios': usuarios,
        'form': form,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/lista_usuarios.html', context)


@login_required
@permission_required('auth.view_user', raise_exception=True)
def detalle_usuario(request, pk):
    """Ver detalle de un usuario"""
    usuario = get_object_or_404(User.objects.prefetch_related('groups', 'user_permissions'), pk=pk)

    # Obtener datos relacionados
    from .models import Persona, UserSecure, UserCargo, Cargo
    
    try:
        persona = Persona.objects.get(user=usuario, eliminado=False)
    except Persona.DoesNotExist:
        persona = None
    
    try:
        user_secure = UserSecure.objects.get(user=usuario, eliminado=False)
    except UserSecure.DoesNotExist:
        user_secure = None
    
    # Obtener cargos del usuario (historial)
    cargos_usuario = UserCargo.objects.filter(
        usuario=usuario,
        eliminado=False
    ).select_related('cargo').order_by('-fecha_inicio')

    # Permisos
    permisos = {
        'puede_editar': request.user.has_perm('auth.change_user'),
        'puede_eliminar': request.user.has_perm('auth.delete_user'),
        'puede_cambiar_password': request.user.has_perm('auth.change_user'),
    }

    context = {
        'titulo': f'Usuario: {usuario.username}',
        'usuario_detalle': usuario,
        'persona': persona,
        'user_secure': user_secure,
        'cargos_usuario': cargos_usuario,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/detalle_usuario.html', context)


@login_required
@permission_required('auth.add_user', raise_exception=True)
@transaction.atomic
def crear_usuario(request):
    """Crear un nuevo usuario con datos de Persona"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()

            # Crear registro de Persona
            from .models import Persona
            documento_identidad = f'TEMP-{usuario.username}'  # Temporal, puede actualizarse después
            persona = Persona.objects.create(
                user=usuario,
                documento_identidad=documento_identidad,
                nombres=form.cleaned_data['nombres'],
                apellido1=form.cleaned_data['apellido1'],
                apellido2=form.cleaned_data.get('apellido2', ''),
                sexo=form.cleaned_data['sexo'],
                fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                talla=form.cleaned_data.get('talla', ''),
                numero_zapato=form.cleaned_data.get('numero_zapato', ''),
                foto_perfil=form.cleaned_data.get('foto_perfil'),
                activo=form.cleaned_data.get('activo_persona', True),
                eliminado=False,
            )

            # Configurar PIN si se proporcionó
            pin_texto = form.cleaned_data.get('pin', '').strip()
            if pin_texto:
                from .models import UserSecure, AuditoriaPin
                user_secure, created = UserSecure.objects.get_or_create(
                    user=usuario,
                    defaults={'activo': True, 'eliminado': False}
                )
                user_secure.set_pin(pin_texto)
                user_secure.save()
                
                # Registrar en auditoría
                AuditoriaPin.objects.create(
                    usuario=usuario,
                    accion='CONFIRMACION_ENTREGA',
                    exitoso=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    detalles={'accion': 'PIN configurado al crear usuario'},
                )

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Usuario creado: {usuario.username}',
                request
            )

            mensaje = f'Usuario {usuario.username} creado exitosamente.'
            if pin_texto:
                mensaje += ' PIN configurado correctamente.'
            messages.success(request, mensaje)
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserCreateForm()

    context = {
        'titulo': 'Crear Usuario',
        'form': form,
        'action': 'Crear',
        'usuario_detalle': None,  # No hay usuario al crear
        'tiene_pin': False,  # No hay PIN al crear
    }

    return render(request, 'account/gestion_usuarios/form_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def editar_usuario(request, pk):
    """Editar un usuario existente"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()

            # Actualizar PIN si se proporcionó
            pin_texto = form.cleaned_data.get('pin', '').strip()
            if pin_texto:
                from .models import UserSecure, AuditoriaPin
                user_secure, created = UserSecure.objects.get_or_create(
                    user=usuario,
                    defaults={'activo': True, 'eliminado': False}
                )
                
                if not created and user_secure.eliminado:
                    user_secure.eliminado = False
                    user_secure.activo = True
                
                tiene_pin_anterior = bool(user_secure.pin)
                user_secure.set_pin(pin_texto)
                user_secure.intentos_fallidos = 0
                user_secure.bloqueado = False
                user_secure.save()
                
                # Registrar en auditoría
                AuditoriaPin.objects.create(
                    usuario=usuario,
                    accion='CONFIRMACION_ENTREGA',
                    exitoso=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    detalles={'accion': 'PIN configurado' if not tiene_pin_anterior else 'PIN cambiado desde edición'},
                )

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Usuario actualizado: {usuario.username}',
                request
            )

            mensaje = f'Usuario {usuario.username} actualizado exitosamente.'
            if pin_texto:
                mensaje += ' PIN actualizado correctamente.'
            messages.success(request, mensaje)
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserUpdateForm(instance=usuario)

    # Obtener información del PIN para mostrar en el template
    from .models import UserSecure
    try:
        user_secure = UserSecure.objects.get(user=usuario, eliminado=False)
        tiene_pin = bool(user_secure.pin)
    except UserSecure.DoesNotExist:
        user_secure = None
        tiene_pin = False

    context = {
        'titulo': f'Editar Usuario: {usuario.username}',
        'form': form,
        'action': 'Actualizar',
        'usuario_detalle': usuario,
        'user_secure': user_secure,
        'tiene_pin': tiene_pin,
    }

    return render(request, 'account/gestion_usuarios/form_usuario.html', context)


@login_required
@permission_required('auth.delete_user', raise_exception=True)
@transaction.atomic
def eliminar_usuario(request, pk):
    """Eliminar (desactivar) un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    # No permitir eliminar superusuarios o el propio usuario
    if usuario.is_superuser:
        messages.error(request, 'No se puede eliminar un superusuario.')
        return redirect('accounts:lista_usuarios')

    if usuario == request.user:
        messages.error(request, 'No puedes eliminarte a ti mismo.')
        return redirect('accounts:lista_usuarios')

    if request.method == 'POST':
        username = usuario.username
        usuario.is_active = False
        usuario.save()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Usuario desactivado: {username}',
            request
        )

        messages.success(request, f'Usuario {username} desactivado exitosamente.')
        return redirect('accounts:lista_usuarios')

    context = {
        'titulo': 'Eliminar Usuario',
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/eliminar_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def cambiar_password_usuario(request, pk):
    """Cambiar contraseña de un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPasswordChangeForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password1'])
            usuario.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Contraseña cambiada para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Contraseña de {usuario.username} actualizada exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserPasswordChangeForm()

    context = {
        'titulo': f'Cambiar Contraseña: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/cambiar_password.html', context)


# ========== GESTIÓN DE GRUPOS (ROLES) ==========

@login_required
@permission_required('auth.view_group', raise_exception=True)
def lista_grupos(request):
    """Listar todos los grupos/roles"""
    grupos = Group.objects.annotate(num_usuarios=Count('user')).all()

    # Permisos
    permisos = {
        'puede_crear': request.user.has_perm('auth.add_group'),
        'puede_editar': request.user.has_perm('auth.change_group'),
        'puede_eliminar': request.user.has_perm('auth.delete_group'),
    }

    context = {
        'titulo': 'Listado de Roles/Grupos',
        'grupos': grupos,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/lista_grupos.html', context)


@login_required
@permission_required('auth.view_group', raise_exception=True)
def detalle_grupo(request, pk):
    """Ver detalle de un grupo/rol"""
    grupo = get_object_or_404(
        Group.objects.prefetch_related('permissions', 'user_set'),
        pk=pk
    )

    # Permisos
    permisos = {
        'puede_editar': request.user.has_perm('auth.change_group'),
        'puede_eliminar': request.user.has_perm('auth.delete_group'),
    }

    context = {
        'titulo': f'Rol/Grupo: {grupo.name}',
        'grupo': grupo,
        'permisos': permisos,
    }

    return render(request, 'account/gestion_usuarios/detalle_grupo.html', context)


@login_required
@permission_required('auth.add_group', raise_exception=True)
@transaction.atomic
def crear_grupo(request):
    """Crear un nuevo grupo/rol"""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            grupo = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Grupo/Rol creado: {grupo.name}',
                request
            )

            messages.success(request, f'Rol {grupo.name} creado exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupForm()

    context = {
        'titulo': 'Crear Rol/Grupo',
        'form': form,
        'action': 'Crear',
    }

    return render(request, 'account/gestion_usuarios/form_grupo.html', context)


@login_required
@permission_required('auth.change_group', raise_exception=True)
@transaction.atomic
def editar_grupo(request, pk):
    """Editar un grupo/rol existente"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=grupo)
        if form.is_valid():
            grupo = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Grupo/Rol actualizado: {grupo.name}',
                request
            )

            messages.success(request, f'Rol {grupo.name} actualizado exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupForm(instance=grupo)

    context = {
        'titulo': f'Editar Rol: {grupo.name}',
        'form': form,
        'action': 'Actualizar',
        'grupo': grupo,
    }

    return render(request, 'account/gestion_usuarios/form_grupo.html', context)


@login_required
@permission_required('auth.delete_group', raise_exception=True)
@transaction.atomic
def eliminar_grupo(request, pk):
    """Eliminar un grupo/rol"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        nombre = grupo.name
        grupo.delete()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Grupo/Rol eliminado: {nombre}',
            request
        )

        messages.success(request, f'Rol {nombre} eliminado exitosamente.')
        return redirect('accounts:lista_grupos')

    context = {
        'titulo': 'Eliminar Rol/Grupo',
        'grupo': grupo,
    }

    return render(request, 'account/gestion_usuarios/eliminar_grupo.html', context)


# ========== ASIGNACIÓN DE PERMISOS Y GRUPOS ==========

@login_required
@permission_required('auth.change_group', raise_exception=True)
@transaction.atomic
def asignar_permisos_grupo(request, pk):
    """Asignar permisos a un grupo"""
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupPermissionsForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permisos actualizados para grupo: {grupo.name}',
                request
            )

            messages.success(request, f'Permisos del rol {grupo.name} actualizados exitosamente.')
            return redirect('accounts:detalle_grupo', pk=grupo.pk)
    else:
        form = GroupPermissionsForm(instance=grupo)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría
    permisos_organizados = {}
    for permission in form.fields['permissions'].queryset:
        app_label = permission.content_type.app_label

        # Determinar la categoría
        if permission.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permission.id]
            categoria_nombre = categoria.get_modulo_display()
            permission.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permission.content_type.model.title()
            permission.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permission)

    context = {
        'titulo': f'Asignar Permisos: {grupo.name}',
        'form': form,
        'grupo': grupo,
        'permisos_organizados': permisos_organizados,
    }

    return render(request, 'account/gestion_usuarios/asignar_permisos_grupo.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def asignar_grupos_usuario(request, pk):
    """Asignar grupos/roles a un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserGroupsForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Grupos actualizados para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Roles del usuario {usuario.username} actualizados exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserGroupsForm(instance=usuario)

    context = {
        'titulo': f'Asignar Roles: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
    }

    return render(request, 'account/gestion_usuarios/asignar_grupos_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def asignar_permisos_usuario(request, pk):
    """Asignar permisos específicos a un usuario"""
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPermissionsForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permisos actualizados para usuario: {usuario.username}',
                request
            )

            messages.success(request, f'Permisos del usuario {usuario.username} actualizados exitosamente.')
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserPermissionsForm(instance=usuario)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría
    permisos_organizados = {}
    for permission in form.fields['user_permissions'].queryset:
        app_label = permission.content_type.app_label

        # Determinar la categoría
        if permission.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permission.id]
            categoria_nombre = categoria.get_modulo_display()
            permission.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permission.content_type.model.title()
            permission.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permission)

    context = {
        'titulo': f'Asignar Permisos: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
        'permisos_organizados': permisos_organizados,
    }

    return render(request, 'account/gestion_usuarios/asignar_permisos_usuario.html', context)


# ========== GESTIÓN DE PERMISOS ==========

@login_required
@permission_required('auth.view_permission', raise_exception=True)
def lista_permisos(request):
    """Listar permisos personalizados organizados por app y categoría"""
    # Obtener búsqueda y filtros
    buscar = request.GET.get('buscar', '')
    app_filter = request.GET.get('app', '')

    # Obtener solo permisos personalizados (excluir add_, change_, delete_, view_)
    permisos = Permission.objects.select_related('content_type').exclude(
        codename__startswith='add_'
    ).exclude(
        codename__startswith='change_'
    ).exclude(
        codename__startswith='delete_'
    ).exclude(
        codename__startswith='view_'
    )

    # Aplicar filtro de búsqueda
    if buscar:
        permisos = permisos.filter(
            Q(name__icontains=buscar) |
            Q(codename__icontains=buscar) |
            Q(content_type__model__icontains=buscar) |
            Q(content_type__app_label__icontains=buscar)
        )

    # Aplicar filtro por app
    if app_filter:
        permisos = permisos.filter(content_type__app_label=app_filter)

    # Importar CategoriaPermiso para permisos del módulo de solicitudes
    try:
        from apps.solicitudes.models import CategoriaPermiso
        # Obtener mapeo de permisos a categorías
        categorias_map = {
            cat.permiso_id: cat
            for cat in CategoriaPermiso.objects.select_related('permiso')
        }
    except ImportError:
        categorias_map = {}

    # Organizar permisos por app y categoría/modelo
    permisos_organizados = {}
    for permiso in permisos:
        app_label = permiso.content_type.app_label

        # Determinar la categoría
        if permiso.id in categorias_map:
            # Si tiene categoría definida, usar la categoría
            categoria = categorias_map[permiso.id]
            categoria_nombre = categoria.get_modulo_display()
            permiso.categoria_obj = categoria  # Agregar para acceso en template
        else:
            # Si no tiene categoría, usar el nombre del modelo
            categoria_nombre = permiso.content_type.model.title()
            permiso.categoria_obj = None

        if app_label not in permisos_organizados:
            permisos_organizados[app_label] = {}

        if categoria_nombre not in permisos_organizados[app_label]:
            permisos_organizados[app_label][categoria_nombre] = []

        permisos_organizados[app_label][categoria_nombre].append(permiso)

    # Obtener lista de apps para el filtro (solo apps con permisos personalizados)
    apps = Permission.objects.select_related('content_type').exclude(
        codename__startswith='add_'
    ).exclude(
        codename__startswith='change_'
    ).exclude(
        codename__startswith='delete_'
    ).exclude(
        codename__startswith='view_'
    ).values_list(
        'content_type__app_label', flat=True
    ).distinct().order_by('content_type__app_label')

    # Permisos del usuario
    permisos_usuario = {
        'puede_crear': request.user.has_perm('auth.add_permission'),
        'puede_editar': request.user.has_perm('auth.change_permission'),
        'puede_eliminar': request.user.has_perm('auth.delete_permission'),
    }

    context = {
        'titulo': 'Listado de Permisos',
        'permisos_organizados': permisos_organizados,
        'apps': apps,
        'buscar': buscar,
        'app_filter': app_filter,
        'permisos': permisos_usuario,
    }

    return render(request, 'account/gestion_usuarios/lista_permisos.html', context)


@login_required
@permission_required('auth.view_permission', raise_exception=True)
def detalle_permiso(request, pk):
    """Ver detalle de un permiso específico"""
    permiso = get_object_or_404(
        Permission.objects.select_related('content_type'),
        pk=pk
    )

    # Obtener grupos que tienen este permiso
    grupos_con_permiso = Group.objects.filter(permissions=permiso).annotate(
        num_usuarios=Count('user')
    )

    # Obtener usuarios que tienen este permiso directamente
    usuarios_con_permiso = User.objects.filter(user_permissions=permiso).select_related()

    # Permisos del usuario
    permisos_usuario = {
        'puede_editar': request.user.has_perm('auth.change_permission'),
        'puede_eliminar': request.user.has_perm('auth.delete_permission'),
    }

    context = {
        'titulo': f'Permiso: {permiso.name}',
        'permiso': permiso,
        'grupos_con_permiso': grupos_con_permiso,
        'usuarios_con_permiso': usuarios_con_permiso,
        'permisos': permisos_usuario,
    }

    return render(request, 'account/gestion_usuarios/detalle_permiso.html', context)


@login_required
@permission_required('auth.add_permission', raise_exception=True)
@transaction.atomic
def crear_permiso(request):
    """Crear un nuevo permiso personalizado"""
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            permiso = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Permiso personalizado creado: {permiso.codename}',
                request
            )

            messages.success(request, f'Permiso "{permiso.name}" creado exitosamente.')
            return redirect('accounts:detalle_permiso', pk=permiso.pk)
    else:
        form = PermissionForm()

    context = {
        'titulo': 'Crear Permiso Personalizado',
        'form': form,
        'action': 'Crear',
    }

    return render(request, 'account/gestion_usuarios/form_permiso.html', context)


@login_required
@permission_required('auth.change_permission', raise_exception=True)
@transaction.atomic
def editar_permiso(request, pk):
    """Editar un permiso personalizado"""
    permiso = get_object_or_404(Permission, pk=pk)

    # Verificar si es un permiso del sistema (auto-generado)
    # Los permisos del sistema tienen codenames que empiezan con add_, change_, delete_, view_
    es_permiso_sistema = permiso.codename.startswith(('add_', 'change_', 'delete_', 'view_'))

    if es_permiso_sistema:
        messages.warning(request, 'No se pueden editar los permisos del sistema.')
        return redirect('accounts:detalle_permiso', pk=permiso.pk)

    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permiso)
        if form.is_valid():
            permiso = form.save()

            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR',
                f'Permiso personalizado actualizado: {permiso.codename}',
                request
            )

            messages.success(request, f'Permiso "{permiso.name}" actualizado exitosamente.')
            return redirect('accounts:detalle_permiso', pk=permiso.pk)
    else:
        form = PermissionForm(instance=permiso)

    context = {
        'titulo': f'Editar Permiso: {permiso.name}',
        'form': form,
        'action': 'Actualizar',
        'permiso': permiso,
    }

    return render(request, 'account/gestion_usuarios/form_permiso.html', context)


@login_required
@permission_required('auth.delete_permission', raise_exception=True)
@transaction.atomic
def eliminar_permiso(request, pk):
    """Eliminar un permiso personalizado"""
    permiso = get_object_or_404(Permission, pk=pk)

    # Verificar si es un permiso del sistema
    es_permiso_sistema = permiso.codename.startswith(('add_', 'change_', 'delete_', 'view_'))

    if es_permiso_sistema:
        messages.error(request, 'No se pueden eliminar los permisos del sistema.')
        return redirect('accounts:lista_permisos')

    if request.method == 'POST':
        nombre = permiso.name
        codename = permiso.codename
        permiso.delete()

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ELIMINAR',
            f'Permiso personalizado eliminado: {codename}',
            request
        )

        messages.success(request, f'Permiso "{nombre}" eliminado exitosamente.')
        return redirect('accounts:lista_permisos')

    context = {
        'titulo': 'Eliminar Permiso',
        'permiso': permiso,
    }

    return render(request, 'account/gestion_usuarios/eliminar_permiso.html', context)


# ========== GESTIÓN DE ORGANIZACIÓN ==========
# Vistas CRUD para Ubicación, Talleres, Área, Departamentos

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin
)
from .forms import UbicacionForm, TallerForm, AreaForm, DepartamentoForm


# ==================== VISTAS DE UBICACIÓN ====================

class UbicacionListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar ubicaciones con paginación y filtros."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    template_name = 'account/organizacion/ubicacion/lista.html'
    context_object_name = 'ubicaciones'
    permission_required = 'activos.view_ubicacion'
    paginate_by = 25

    def get_queryset(self):
        """Retorna ubicaciones no eliminadas con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False)

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Ubicaciones'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('activos.add_ubicacion')
        return context


class UbicacionCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear una nueva ubicación."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'account/organizacion/ubicacion/form.html'
    permission_required = 'activos.add_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Ubicación creada: {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación "{obj.nombre}" creada exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Ubicación'
        context['action'] = 'Crear'
        return context


class UbicacionUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar una ubicación existente."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'account/organizacion/ubicacion/form.html'
    permission_required = 'activos.change_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Ubicación actualizada: {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación "{obj.nombre}" actualizada exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Ubicación: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class UbicacionDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) una ubicación."""
    from apps.activos.models import Ubicacion
    model = Ubicacion
    template_name = 'account/organizacion/ubicacion/eliminar.html'
    permission_required = 'activos.delete_ubicacion'
    success_url = reverse_lazy('accounts:ubicacion_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Ubicación eliminada: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Ubicación: {self.object.nombre}'
        return context


# ==================== VISTAS DE TALLER ====================

class TallerListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar talleres con paginación y filtros."""
    from apps.activos.models import Taller
    model = Taller
    template_name = 'account/organizacion/taller/lista.html'
    context_object_name = 'talleres'
    permission_required = 'activos.view_taller'
    paginate_by = 25

    def get_queryset(self):
        """Retorna talleres no eliminados con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(ubicacion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Talleres'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('activos.add_taller')
        return context


class TallerCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear un nuevo taller."""
    from apps.activos.models import Taller
    model = Taller
    form_class = TallerForm
    template_name = 'account/organizacion/taller/form.html'
    permission_required = 'activos.add_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Taller creado: {obj.codigo} - {obj.nombre}'
    success_message = 'Taller "{obj.nombre}" creado exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Taller'
        context['action'] = 'Crear'
        return context


class TallerUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un taller existente."""
    from apps.activos.models import Taller
    model = Taller
    form_class = TallerForm
    template_name = 'account/organizacion/taller/form.html'
    permission_required = 'activos.change_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Taller actualizado: {obj.codigo} - {obj.nombre}'
    success_message = 'Taller "{obj.nombre}" actualizado exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Taller: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class TallerDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un taller."""
    from apps.activos.models import Taller
    model = Taller
    template_name = 'account/organizacion/taller/eliminar.html'
    permission_required = 'activos.delete_taller'
    success_url = reverse_lazy('accounts:taller_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Taller eliminado: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Taller: {self.object.nombre}'
        return context


# ==================== VISTAS DE ÁREA ====================

class AreaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar áreas con paginación y filtros."""
    from apps.solicitudes.models import Area
    model = Area
    template_name = 'account/organizacion/area/lista.html'
    context_object_name = 'areas'
    permission_required = 'solicitudes.view_area'
    paginate_by = 25

    def get_queryset(self):
        """Retorna áreas no eliminadas con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('departamento', 'responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        # Filtro por departamento
        departamento_id = self.request.GET.get('departamento', '')
        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        from apps.solicitudes.models import Departamento
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Áreas'
        context['query'] = self.request.GET.get('q', '')
        context['departamento_id'] = self.request.GET.get('departamento', '')
        context['departamentos'] = Departamento.objects.filter(eliminado=False).order_by('codigo')
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_area')
        return context


class AreaCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear una nueva área."""
    from apps.solicitudes.models import Area
    model = Area
    form_class = AreaForm
    template_name = 'account/organizacion/area/form.html'
    permission_required = 'solicitudes.add_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Área creada: {obj.codigo} - {obj.nombre}'
    success_message = 'Área "{obj.nombre}" creada exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Área'
        context['action'] = 'Crear'
        return context


class AreaUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un área existente."""
    from apps.solicitudes.models import Area
    model = Area
    form_class = AreaForm
    template_name = 'account/organizacion/area/form.html'
    permission_required = 'solicitudes.change_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Área actualizada: {obj.codigo} - {obj.nombre}'
    success_message = 'Área "{obj.nombre}" actualizada exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Área: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class AreaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un área."""
    from apps.solicitudes.models import Area
    model = Area
    template_name = 'account/organizacion/area/eliminar.html'
    permission_required = 'solicitudes.delete_area'
    success_url = reverse_lazy('accounts:area_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Área eliminada: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Área: {self.object.nombre}'
        # Verificar si tiene relaciones
        context['tiene_solicitudes'] = hasattr(self.object, 'solicitudes') and self.object.solicitudes.filter(eliminado=False).exists()
        return context


# ==================== VISTAS DE DEPARTAMENTO ====================

class DepartamentoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar departamentos con paginación y filtros."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    template_name = 'account/organizacion/departamento/lista.html'
    context_object_name = 'departamentos'
    permission_required = 'solicitudes.view_departamento'
    paginate_by = 25

    def get_queryset(self):
        """Retorna departamentos no eliminados con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False).select_related('responsable')

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Departamentos'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('solicitudes.add_departamento')
        return context


class DepartamentoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear un nuevo departamento."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'account/organizacion/departamento/form.html'
    permission_required = 'solicitudes.add_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Departamento creado: {obj.codigo} - {obj.nombre}'
    success_message = 'Departamento "{obj.nombre}" creado exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Departamento'
        context['action'] = 'Crear'
        return context


class DepartamentoUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un departamento existente."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'account/organizacion/departamento/form.html'
    permission_required = 'solicitudes.change_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Departamento actualizado: {obj.codigo} - {obj.nombre}'
    success_message = 'Departamento "{obj.nombre}" actualizado exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Departamento: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class DepartamentoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un departamento."""
    from apps.solicitudes.models import Departamento
    model = Departamento
    template_name = 'account/organizacion/departamento/eliminar.html'
    permission_required = 'solicitudes.delete_departamento'
    success_url = reverse_lazy('accounts:departamento_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Departamento eliminado: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Departamento: {self.object.nombre}'
        # Verificar si tiene áreas relacionadas
        context['tiene_areas'] = self.object.areas.filter(eliminado=False).exists()
        return context


# ========== GESTIÓN DE CARGOS ==========

class CargoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar cargos con paginación y filtros."""
    from .models import Cargo
    model = Cargo
    template_name = 'account/cargos/lista.html'
    context_object_name = 'cargos'
    permission_required = 'accounts.view_cargo'
    paginate_by = 25

    def get_queryset(self):
        """Retorna cargos no eliminados con búsqueda."""
        queryset = super().get_queryset().filter(eliminado=False)
        
        # Búsqueda
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q)
            )
        
        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Cargos'
        context['query'] = self.request.GET.get('q', '')
        context['puede_crear'] = self.request.user.has_perm('accounts.add_cargo')
        return context


class CargoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """Vista para crear un nuevo cargo."""
    from .models import Cargo
    model = Cargo
    form_class = CargoForm
    template_name = 'account/cargos/form.html'
    permission_required = 'accounts.add_cargo'
    success_url = reverse_lazy('accounts:cargo_lista')
    audit_action = 'CREAR'
    audit_description_template = 'Cargo creado: {obj.codigo} - {obj.nombre}'
    success_message = 'Cargo "{obj.nombre}" creado exitosamente.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Cargo'
        context['action'] = 'Crear'
        return context


class CargoUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """Vista para actualizar un cargo existente."""
    from .models import Cargo
    model = Cargo
    form_class = CargoForm
    template_name = 'account/cargos/form.html'
    permission_required = 'accounts.change_cargo'
    success_url = reverse_lazy('accounts:cargo_lista')
    audit_action = 'ACTUALIZAR'
    audit_description_template = 'Cargo actualizado: {obj.codigo} - {obj.nombre}'
    success_message = 'Cargo "{obj.nombre}" actualizado exitosamente.'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Cargo: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context


class CargoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un cargo."""
    from .models import Cargo
    model = Cargo
    template_name = 'account/cargos/eliminar.html'
    permission_required = 'accounts.delete_cargo'
    success_url = reverse_lazy('accounts:cargo_lista')
    audit_action = 'ELIMINAR'
    audit_description_template = 'Cargo eliminado: {obj.codigo} - {obj.nombre}'

    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Cargo: {self.object.nombre}'
        # Verificar si tiene usuarios asignados
        from .models import UserCargo
        context['tiene_usuarios'] = UserCargo.objects.filter(
            cargo=self.object,
            eliminado=False
        ).exists()
        context['count_usuarios'] = UserCargo.objects.filter(
            cargo=self.object,
            eliminado=False
        ).count()
        return context


# ========== GESTIÓN DE PIN, PERSONA Y CARGOS DE USUARIO ==========

@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def gestionar_pin_usuario(request, pk):
    """Gestionar PIN de un usuario (crear o cambiar)."""
    usuario = get_object_or_404(User, pk=pk)
    
    from .models import UserSecure, AuditoriaPin
    
    # Obtener o crear UserSecure
    user_secure, created = UserSecure.objects.get_or_create(
        user=usuario,
        defaults={'activo': True, 'eliminado': False}
    )
    
    if not created and user_secure.eliminado:
        user_secure.eliminado = False
        user_secure.activo = True
        user_secure.save()
    
    tiene_pin = bool(user_secure.pin)
    
    if request.method == 'POST':
        form = PINForm(request.POST)
        if form.is_valid():
            pin_texto = form.cleaned_data['pin']
            
            # Guardar PIN encriptado
            user_secure.set_pin(pin_texto)
            user_secure.intentos_fallidos = 0
            user_secure.bloqueado = False
            user_secure.save()

            # Registrar en auditoría (usamos CONFIRMACION_ENTREGA como acción genérica para cambios de PIN)
            AuditoriaPin.objects.create(
                usuario=usuario,
                accion='CONFIRMACION_ENTREGA',
                exitoso=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalles={'accion': 'PIN configurado' if not tiene_pin else 'PIN cambiado'},
            )
            
            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR' if tiene_pin else 'CREAR',
                f'PIN {"cambiado" if tiene_pin else "configurado"} para usuario: {usuario.username}',
                request
            )
            
            messages.success(
                request,
                f'PIN {"actualizado" if tiene_pin else "configurado"} exitosamente para {usuario.username}.'
            )
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = PINForm()
    
    context = {
        'titulo': f'{"Cambiar" if tiene_pin else "Configurar"} PIN: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
        'tiene_pin': tiene_pin,
        'user_secure': user_secure,
    }
    
    return render(request, 'account/gestion_usuarios/gestionar_pin.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def desbloquear_usuario(request, pk):
    """Desbloquear un usuario bloqueado por intentos fallidos de PIN."""
    usuario = get_object_or_404(User, pk=pk)
    
    from .models import UserSecure, AuditoriaPin
    
    try:
        user_secure = UserSecure.objects.get(user=usuario, eliminado=False)
    except UserSecure.DoesNotExist:
        messages.error(request, f'El usuario {usuario.username} no tiene PIN configurado.')
        return redirect('accounts:detalle_usuario', pk=usuario.pk)
    
    if not user_secure.bloqueado:
        messages.info(request, f'El usuario {usuario.username} no está bloqueado.')
        return redirect('accounts:detalle_usuario', pk=usuario.pk)
    
    if request.method == 'POST':
        user_secure.desbloquear()
        user_secure.save()

        # Registrar en auditoría
        AuditoriaPin.objects.create(
            usuario=usuario,
            accion='DESBLOQUEO',
            exitoso=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            detalles={'desbloqueado_por': request.user.username},
        )
        
        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ACTUALIZAR',
            f'Usuario desbloqueado: {usuario.username}',
            request
        )
        
        messages.success(request, f'Usuario {usuario.username} desbloqueado exitosamente.')
        return redirect('accounts:detalle_usuario', pk=usuario.pk)
    
    context = {
        'titulo': f'Desbloquear Usuario: {usuario.username}',
        'usuario_detalle': usuario,
        'user_secure': user_secure,
    }
    
    return render(request, 'account/gestion_usuarios/desbloquear_usuario.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def gestionar_persona_usuario(request, pk):
    """Gestionar datos de Persona de un usuario (crear o editar)."""
    usuario = get_object_or_404(User, pk=pk)
    
    from .models import Persona
    
    try:
        persona = Persona.objects.get(user=usuario, eliminado=False)
    except Persona.DoesNotExist:
        persona = None
    
    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        if form.is_valid():
            persona_obj = form.save(commit=False)
            persona_obj.user = usuario
            persona_obj.save()
            
            # Registrar log
            registrar_log_auditoria(
                request.user,
                'ACTUALIZAR' if persona else 'CREAR',
                f'Datos de persona {"actualizados" if persona else "creados"} para usuario: {usuario.username}',
                request
            )
            
            messages.success(
                request,
                f'Datos de persona {"actualizados" if persona else "creados"} exitosamente para {usuario.username}.'
            )
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = PersonaForm(instance=persona)
    
    context = {
        'titulo': f'{"Editar" if persona else "Crear"} Datos de Persona: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
        'persona': persona,
    }
    
    return render(request, 'account/gestion_usuarios/gestionar_persona.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
@transaction.atomic
def gestionar_cargos_usuario(request, pk):
    """Asignar un nuevo cargo a un usuario."""
    usuario = get_object_or_404(User, pk=pk)
    
    from .models import UserCargo
    
    if request.method == 'POST':
        form = UserCargoForm(request.POST)
        if form.is_valid():
            user_cargo = form.save(commit=False)
            user_cargo.usuario = usuario
            user_cargo.save()
            
            # Registrar log
            registrar_log_auditoria(
                request.user,
                'CREAR',
                f'Cargo {user_cargo.cargo.nombre} asignado a usuario: {usuario.username}',
                request
            )
            
            messages.success(
                request,
                f'Cargo {user_cargo.cargo.nombre} asignado exitosamente a {usuario.username}.'
            )
            return redirect('accounts:detalle_usuario', pk=usuario.pk)
    else:
        form = UserCargoForm()
    
    # Obtener historial de cargos
    cargos_usuario = UserCargo.objects.filter(
        usuario=usuario,
        eliminado=False
    ).select_related('cargo').order_by('-fecha_inicio')
    
    context = {
        'titulo': f'Gestionar Cargos: {usuario.username}',
        'form': form,
        'usuario_detalle': usuario,
        'cargos_usuario': cargos_usuario,
    }
    
    return render(request, 'account/gestion_usuarios/gestionar_cargos.html', context)


# ==================== VISTAS AJAX PARA MODALES ====================

@login_required
@require_http_methods(["POST"])
def cambiar_password_usuario_ajax(request, pk):
    """
    Vista AJAX para cambiar contraseña de un usuario mediante modal.
    
    Permite que administradores cambien la contraseña de otros usuarios.
    """
    usuario = get_object_or_404(User, pk=pk)
    
    # Verificar permisos
    if not request.user.has_perm('auth.change_user'):
        return JsonResponse({
            'success': False,
            'message': 'No tiene permisos para cambiar contraseñas.'
        }, status=403)
    
    form = UserPasswordChangeForm(request.POST)
    if form.is_valid():
        usuario.set_password(form.cleaned_data['password1'])
        usuario.save()
        
        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ACTUALIZAR',
            f'Contraseña cambiada para usuario: {usuario.username}',
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Contraseña de {usuario.username} actualizada exitosamente.'
        })
    else:
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors[0] if field_errors else ''
        
        return JsonResponse({
            'success': False,
            'message': 'Error al validar el formulario.',
            'errors': errors
        }, status=400)


@login_required
@require_http_methods(["POST"])
def gestionar_pin_usuario_ajax(request, pk):
    """
    Vista AJAX para gestionar PIN de un usuario mediante modal.
    
    Permite que administradores configuren/cambien el PIN de otros usuarios.
    """
    usuario = get_object_or_404(User, pk=pk)
    
    # Verificar permisos
    if not request.user.has_perm('auth.change_user'):
        return JsonResponse({
            'success': False,
            'message': 'No tiene permisos para gestionar PINs.'
        }, status=403)
    
    from .models import UserSecure, AuditoriaPin
    
    # Obtener o crear UserSecure
    user_secure, created = UserSecure.objects.get_or_create(
        user=usuario,
        defaults={'activo': True, 'eliminado': False}
    )
    
    if not created and user_secure.eliminado:
        user_secure.eliminado = False
        user_secure.activo = True
        user_secure.save()
    
    tiene_pin = bool(user_secure.pin)
    
    form = PINForm(request.POST)
    if form.is_valid():
        pin_texto = form.cleaned_data['pin']
        
        # Guardar PIN encriptado
        user_secure.set_pin(pin_texto)
        user_secure.intentos_fallidos = 0
        user_secure.bloqueado = False
        user_secure.save()

        # Registrar en auditoría
        AuditoriaPin.objects.create(
            usuario=usuario,
            accion='CONFIRMACION_ENTREGA',
            exitoso=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            detalles={'accion': 'PIN configurado' if not tiene_pin else 'PIN cambiado'},
        )

        # Registrar log
        registrar_log_auditoria(
            request.user,
            'ACTUALIZAR' if tiene_pin else 'CREAR',
            f'PIN {"cambiado" if tiene_pin else "configurado"} para usuario: {usuario.username}',
            request
        )

        return JsonResponse({
            'success': True,
            'message': f'PIN {"actualizado" if tiene_pin else "configurado"} exitosamente para {usuario.username}.'
        })
    else:
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors[0] if field_errors else ''

        return JsonResponse({
            'success': False,
            'message': 'Error al validar el formulario.',
            'errors': errors
        }, status=400)


@login_required
@require_http_methods(["POST"])
def gestionar_mi_pin(request):
    """
    Vista AJAX para que un usuario gestione su propio PIN mediante modal.
    
    Permite auto-gestión de PIN sin necesidad de permisos de administrador.
    """
    usuario = request.user
    
    from .models import UserSecure, AuditoriaPin
    
    # Obtener o crear UserSecure
    user_secure, created = UserSecure.objects.get_or_create(
        user=usuario,
        defaults={'activo': True, 'eliminado': False}
    )
    
    if not created and user_secure.eliminado:
        user_secure.eliminado = False
        user_secure.activo = True
        user_secure.save()
    
    tiene_pin = bool(user_secure.pin)
    
    form = PINForm(request.POST)
    if form.is_valid():
        pin_texto = form.cleaned_data['pin']
        
        # Guardar PIN encriptado
        user_secure.set_pin(pin_texto)
        user_secure.intentos_fallidos = 0
        user_secure.bloqueado = False
        user_secure.save()

        # Registrar en auditoría
        AuditoriaPin.objects.create(
            usuario=usuario,
            accion='CONFIRMACION_ENTREGA',
            exitoso=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            detalles={'accion': 'PIN auto-configurado' if not tiene_pin else 'PIN auto-cambiado'},
        )
        
        # Registrar log
        registrar_log_auditoria(
            usuario,
            'ACTUALIZAR' if tiene_pin else 'CREAR',
            f'PIN {"auto-cambiado" if tiene_pin else "auto-configurado"} por {usuario.username}',
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'PIN {"actualizado" if tiene_pin else "configurado"} exitosamente.'
        })
    else:
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors[0] if field_errors else ''
        
        return JsonResponse({
            'success': False,
            'message': 'Error al validar el formulario.',
            'errors': errors
        }, status=400)