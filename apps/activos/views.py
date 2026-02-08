"""
Vistas del módulo de activos.

Este módulo implementa las vistas para la gestión de activos,
incluyendo CRUD de catálogos y gestión de movimientos.

Todas las vistas usan CBVs (Class-Based Views) y siguen las
mejores prácticas de Django con type hints completos.
"""
from __future__ import annotations

from typing import Any

from django.db.models import QuerySet, Q
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin, FilteredListMixin
)
from .models import (
    Activo, CategoriaActivo, EstadoActivo, Ubicacion,
    Proveniencia, Marca, Taller, TipoMovimientoActivo, MovimientoActivo
)
from .forms import (
    ActivoForm, CategoriaActivoForm, EstadoActivoForm, UbicacionForm,
    ProvenienciaForm, MarcaForm, TallerForm, TipoMovimientoActivoForm,
    MovimientoActivoForm, FiltroActivosForm
)


# ==================== VISTA MENÚ PRINCIPAL ====================

class MenuInventarioView(BaseAuditedViewMixin, TemplateView):
    """
    Vista del menú principal del módulo de inventario (activos).

    Muestra estadísticas y accesos rápidos basados en permisos del usuario.
    Permisos: activos.view_activo
    """
    template_name = 'activos/menu_inventario.html'
    permission_required = 'activos.view_activo'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega estadísticas al contexto."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Estadísticas del módulo
        context['stats'] = {
            'total_activos': Activo.objects.filter(eliminado=False).count(),
            'total_categorias': CategoriaActivo.objects.filter(eliminado=False).count(),
            'total_movimientos': MovimientoActivo.objects.filter(eliminado=False).count(),
            'total_ubicaciones': Ubicacion.objects.filter(eliminado=False).count(),
        }

        # Permisos del usuario
        context['permisos'] = {
            'puede_crear': user.has_perm('activos.add_activo'),
            'puede_movimientos': user.has_perm('activos.add_movimientoactivo'),
            'puede_categorias': user.has_perm('activos.add_categoriaactivo'),
            'puede_gestionar': user.has_perm('activos.change_activo'),
        }

        context['titulo'] = 'Módulo de Inventario'
        return context


# ==================== VISTAS DE ACTIVOS ====================

class ActivoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar activos con filtros y paginación.

    Permisos: activos.view_activo
    Filtros: Categoría, estado, búsqueda por texto
    """
    model = Activo
    template_name = 'activos/lista_activos.html'
    context_object_name = 'activos'
    permission_required = 'activos.view_activo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Activo]:
        """Retorna activos con optimización N+1."""
        queryset = Activo.objects.filter(eliminado=False).select_related(
            'categoria', 'estado', 'marca'
        )

        # Aplicar filtros del formulario
        form = FiltroActivosForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data

            # Filtro por categoría
            if data.get('categoria'):
                queryset = queryset.filter(categoria=data['categoria'])

            # Filtro por estado
            if data.get('estado'):
                queryset = queryset.filter(estado=data['estado'])

            # Filtro de búsqueda por texto
            if data.get('buscar'):
                q = data['buscar']
                queryset = queryset.filter(
                    Q(codigo__icontains=q) |
                    Q(nombre__icontains=q) |
                    Q(numero_serie__icontains=q) |
                    Q(codigo_barras__icontains=q)
                )

        return queryset.order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Activos'
        context['form'] = FiltroActivosForm(self.request.GET)
        return context


class ActivoDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de un activo con su historial.

    Permisos: activos.view_activo
    """
    model = Activo
    template_name = 'activos/detalle_activo.html'
    context_object_name = 'activo'
    permission_required = 'activos.view_activo'

    def get_queryset(self) -> QuerySet[Activo]:
        """Optimiza consultas con select_related."""
        return Activo.objects.filter(eliminado=False).select_related(
            'categoria', 'estado', 'marca'
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega movimientos recientes al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Activo {self.object.codigo}'

        # Últimos 10 movimientos del activo con estado_nuevo
        context['movimientos'] = MovimientoActivo.objects.filter(
            activo=self.object, eliminado=False
        ).select_related(
            'tipo_movimiento', 'ubicacion_destino', 'taller',
            'responsable', 'proveniencia', 'usuario_registro',
            'estado_nuevo'  # Incluir estado_nuevo para mostrar el estado del movimiento
        ).order_by('-fecha_creacion')[:10]

        return context


class ActivoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear un nuevo activo.

    Permisos: activos.add_activo
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza integridad de datos
    """
    model = Activo
    form_class = ActivoForm
    template_name = 'activos/form_activo.html'
    permission_required = 'activos.add_activo'

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó activo {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Activo {obj.codigo} creado exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle del activo creado."""
        return reverse_lazy('activos:detalle_activo', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Activo'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: ActivoForm) -> HttpResponse:
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class ActivoUpdateView(BaseAuditedViewMixin, AtomicTransactionMixin, UpdateView):
    """
    Vista para editar un activo existente.

    Permisos: activos.change_activo
    Auditoría: Registra acción EDITAR automáticamente
    Transacción atómica: Garantiza integridad de datos
    """
    model = Activo
    form_class = ActivoForm
    template_name = 'activos/form_activo.html'
    permission_required = 'activos.change_activo'

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó activo {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Activo {obj.codigo} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet[Activo]:
        """Solo permite editar activos no eliminados."""
        return Activo.objects.filter(eliminado=False)

    def get_success_url(self) -> str:
        """Redirige al detalle del activo editado."""
        return reverse_lazy('activos:detalle_activo', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Activo {self.object.codigo}'
        context['action'] = 'Editar'
        context['activo'] = self.object
        return context

    def form_valid(self, form: ActivoForm) -> HttpResponse:
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class ActivoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un activo.

    Permisos: activos.delete_activo
    Auditoría: Registra acción ELIMINAR automáticamente
    Implementa soft delete (marca como eliminado, no borra físicamente)
    """
    model = Activo
    template_name = 'activos/eliminar_activo.html'
    permission_required = 'activos.delete_activo'
    success_url = reverse_lazy('activos:lista_activos')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó activo {obj.codigo} - {obj.nombre}'

    # Mensaje de éxito
    success_message = 'Activo {obj.codigo} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet[Activo]:
        """Solo permite eliminar activos no eliminados."""
        return Activo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Activo {self.object.codigo}'
        context['activo'] = self.object
        # Verificar si tiene movimientos
        context['tiene_movimientos'] = MovimientoActivo.objects.filter(
            activo=self.object, eliminado=False
        ).exists()
        return context


# ==================== VISTAS DE MOVIMIENTOS ====================

class MovimientoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para ver el historial de movimientos de inventario con todos los detalles.

    Permisos: activos.view_movimientoactivo
    """
    model = MovimientoActivo
    template_name = 'activos/lista_movimientos.html'
    context_object_name = 'movimientos'
    permission_required = 'activos.view_movimientoactivo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[MovimientoActivo]:
        """Retorna movimientos con relaciones optimizadas."""
        queryset = MovimientoActivo.objects.filter(eliminado=False).select_related(
            'activo', 'activo__categoria', 'activo__estado', 'activo__marca',
            'estado_nuevo',  # Incluir estado_nuevo para el filtro
            'tipo_movimiento', 'ubicacion_destino', 'taller', 'responsable',
            'proveniencia', 'usuario_registro'
        )

        # Filtros opcionales
        activo_id = self.request.GET.get('activo')
        if activo_id:
            queryset = queryset.filter(activo_id=activo_id)

        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            queryset = queryset.filter(activo__categoria_id=categoria_id)

        estado_id = self.request.GET.get('estado')
        if estado_id:
            # Filtrar por el estado_nuevo del movimiento, no por el estado actual del activo
            queryset = queryset.filter(estado_nuevo_id=estado_id)

        # Filtro de búsqueda
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(activo__codigo__icontains=buscar) |
                Q(activo__nombre__icontains=buscar)
            )

        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Movimientos de Inventario'
        # Agregar catálogos para filtros
        context['categorias'] = CategoriaActivo.objects.filter(activo=True, eliminado=False)
        context['estados'] = EstadoActivo.objects.filter(activo=True, eliminado=False)
        return context


class MovimientoDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de un movimiento.

    Permisos: activos.view_movimientoactivo
    """
    model = MovimientoActivo
    template_name = 'activos/detalle_movimiento.html'
    context_object_name = 'movimiento'
    permission_required = 'activos.view_movimientoactivo'

    def get_queryset(self) -> QuerySet[MovimientoActivo]:
        """Optimiza consultas con select_related."""
        return MovimientoActivo.objects.filter(eliminado=False).select_related(
            'activo', 'tipo_movimiento', 'ubicacion_destino', 'taller',
            'responsable', 'proveniencia', 'usuario_registro'
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Detalle de Movimiento'
        return context


class MovimientoCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para registrar movimientos de activos (uno o múltiples).

    Permisos: activos.add_movimientoactivo
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza integridad de datos
    """
    model = MovimientoActivo
    form_class = MovimientoActivoForm
    template_name = 'activos/form_movimiento.html'
    permission_required = 'activos.add_movimientoactivo'
    success_url = reverse_lazy('activos:lista_movimientos')

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Movimiento(s) de activo registrado(s) exitosamente.'

    def form_valid(self, form: MovimientoActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con transacción atómica.
        
        Maneja tanto movimientos individuales como múltiples activos seleccionados.
        Todos los movimientos comparten los mismos datos (estado, ubicación, responsable, etc.)
        excepto el activo específico.
        
        Actualiza automáticamente el estado del activo cuando se crea un movimiento.
        """
        from django.utils import timezone
        from django.shortcuts import redirect
        from django.urls import reverse
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Obtener estado nuevo del formulario
        estado_nuevo = form.cleaned_data.get('estado_nuevo')
        
        # Validar que estado_nuevo esté presente
        if not estado_nuevo:
            messages.error(self.request, 'Debe seleccionar un nuevo estado para el movimiento.')
            return self.form_invalid(form)
        
        # Obtener lista de activos seleccionados (viene del campo hidden)
        activos_seleccionados_str = self.request.POST.get('activos_seleccionados', '')
        pin_confirmado = self.request.POST.get('pin_confirmado', 'false') == 'true'
        
        logger.info(f'Procesando movimiento: estado_nuevo={estado_nuevo}, activos_seleccionados={activos_seleccionados_str}')
        
        # Si hay múltiples activos seleccionados, procesarlos
        if activos_seleccionados_str:
            try:
                activos_ids = [int(id_str) for id_str in activos_seleccionados_str.split(',') if id_str.strip()]
            except (ValueError, AttributeError) as e:
                logger.error(f'Error al procesar IDs de activos: {str(e)}')
                messages.error(self.request, 'Error al procesar los activos seleccionados.')
                return self.form_invalid(form)
            
            if not activos_ids:
                messages.error(self.request, 'No se seleccionaron activos para el movimiento.')
                return self.form_invalid(form)
            
            # Obtener los activos (siempre obtener el estado más reciente)
            activos = Activo.objects.filter(id__in=activos_ids, activo=True, eliminado=False).select_related('estado')
            
            if not activos.exists():
                messages.error(self.request, 'Los activos seleccionados no están disponibles.')
                return self.form_invalid(form)
            
            if activos.count() != len(activos_ids):
                logger.warning(f'Se solicitaron {len(activos_ids)} activos pero solo se encontraron {activos.count()}')
            
            logger.info(f'Procesando {len(activos_ids)} activo(s) para movimiento con estado_nuevo={estado_nuevo.nombre if estado_nuevo else "N/A"}')
            
            # Datos comunes para todos los movimientos
            # NOTA: Los movimientos de "Baja" se crean normalmente aquí
            # El módulo de bajas de inventario puede referenciar estos movimientos después
            datos_comunes = {
                'estado_nuevo': estado_nuevo,
                'ubicacion_destino': form.cleaned_data.get('ubicacion_destino'),
                'responsable': form.cleaned_data.get('responsable'),
                'taller': form.cleaned_data.get('taller'),
                'proveniencia': form.cleaned_data.get('proveniencia'),
                'observaciones': form.cleaned_data.get('observaciones', ''),
                'usuario_registro': self.request.user,
                'usuario_creacion': self.request.user,
                'usuario_actualizacion': self.request.user,
            }
            
            # Datos de confirmación PIN (solo si hay responsable)
            if pin_confirmado and datos_comunes['responsable']:
                datos_comunes['confirmado_con_pin'] = True
                datos_comunes['fecha_confirmacion_pin'] = timezone.now()
                datos_comunes['ip_confirmacion'] = self.request.META.get('REMOTE_ADDR')
            
            # Crear un movimiento por cada activo seleccionado y actualizar estado del activo
            movimientos_creados = []
            try:
                for activo in activos:
                    # Recargar el activo para obtener el estado más reciente
                    activo.refresh_from_db()
                    
                    # Guardar estado anterior para auditoría
                    estado_anterior = activo.estado
                    estado_anterior_nombre = estado_anterior.nombre if estado_anterior else "N/A"
                    
                    # Crear el movimiento
                    movimiento = MovimientoActivo.objects.create(
                        activo=activo,
                        **datos_comunes
                    )
                    movimientos_creados.append(movimiento)
                    
                    # Actualizar el estado del activo si se proporcionó un estado nuevo
                    if estado_nuevo:
                        # Actualizar el estado del activo
                        activo.estado = estado_nuevo
                        activo.usuario_actualizacion = self.request.user
                        activo.save(update_fields=['estado', 'usuario_actualizacion', 'fecha_actualizacion'])
                        
                        # Recargar el activo desde la BD para verificar que se guardó correctamente
                        activo.refresh_from_db()
                        
                        # Verificar que el estado se actualizó correctamente
                        if activo.estado.id != estado_nuevo.id:
                            logger.error(
                                f'ERROR: El estado del activo {activo.codigo} no se actualizó correctamente. '
                                f'Esperado: {estado_nuevo.id} ({estado_nuevo.nombre}), '
                                f'Obtenido: {activo.estado.id} ({activo.estado.nombre})'
                            )
                            messages.warning(
                                self.request,
                                f'Advertencia: El estado del activo {activo.codigo} puede no haberse actualizado correctamente.'
                            )
                        
                        # Log para debugging
                        logger.info(
                            f'Movimiento creado: Activo {activo.codigo} (ID: {activo.id}) - '
                            f'Estado anterior: {estado_anterior_nombre} - '
                            f'Estado nuevo: {estado_nuevo.nombre} - '
                            f'Estado actual en BD: {activo.estado.nombre if activo.estado else "N/A"}'
                        )
            except Exception as e:
                logger.error(f'Error al crear movimientos: {str(e)}', exc_info=True)
                messages.error(
                    self.request,
                    f'Error al crear los movimientos: {str(e)}'
                )
                return self.form_invalid(form)
            
            # Guardar el primer movimiento como self.object para compatibilidad
            self.object = movimientos_creados[0] if movimientos_creados else None
            
            # Generar descripción para auditoría
            cantidad = len(movimientos_creados)
            descripcion = f'Registró {cantidad} movimiento(s) de activos'
            if datos_comunes['ubicacion_destino']:
                descripcion += f' a {datos_comunes["ubicacion_destino"].nombre}'
            if datos_comunes['responsable']:
                descripcion += f' - Responsable: {datos_comunes["responsable"].get_full_name()}'
            if pin_confirmado:
                descripcion += ' (Confirmado con PIN)'
            
            self.audit_description_template = descripcion
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mensaje de éxito
            messages.success(
                self.request,
                f'Se registraron exitosamente {cantidad} movimiento(s) de activos. '
                'El estado de los activos ha sido actualizado.'
            )
            
            return HttpResponseRedirect(self.get_success_url())
        
        else:
            # Flujo original para un solo activo (compatibilidad con formulario antiguo)
            movimiento = form.save(commit=False)
            movimiento.usuario_registro = self.request.user
            
            # NOTA: Los movimientos de "Baja" se crean normalmente
            # El módulo de bajas de inventario puede referenciar estos movimientos después
            
            # Verificar si se confirmó con PIN
            if pin_confirmado and movimiento.responsable:
                movimiento.confirmado_con_pin = True
                movimiento.fecha_confirmacion_pin = timezone.now()
                movimiento.ip_confirmacion = self.request.META.get('REMOTE_ADDR')
            
            movimiento.save()
            self.object = movimiento
            
            # Actualizar el estado del activo si se proporcionó un estado nuevo
            if estado_nuevo:
                # Guardar estado anterior para logging
                estado_anterior = movimiento.activo.estado
                estado_anterior_nombre = estado_anterior.nombre if estado_anterior else "N/A"
                
                # Actualizar el estado del activo
                movimiento.activo.estado = estado_nuevo
                movimiento.activo.usuario_actualizacion = self.request.user
                movimiento.activo.save(update_fields=['estado', 'usuario_actualizacion', 'fecha_actualizacion'])
                
                # Recargar el activo desde la BD para verificar que se guardó correctamente
                movimiento.activo.refresh_from_db()
                
                # Log para debugging
                logger.info(
                    f'Movimiento creado (flujo individual): Activo {movimiento.activo.codigo} (ID: {movimiento.activo.id}) - '
                    f'Estado anterior: {estado_anterior_nombre} - '
                    f'Estado nuevo: {estado_nuevo.nombre} - '
                    f'Estado actual en BD: {movimiento.activo.estado.nombre if movimiento.activo.estado else "N/A"}'
                )

            # Generar descripción para auditoría
            descripcion = f'Registró movimiento de activo: {movimiento.activo.codigo}'
            if movimiento.ubicacion_destino:
                descripcion += f' a {movimiento.ubicacion_destino.nombre}'
            if movimiento.responsable:
                descripcion += f' - Responsable: {movimiento.responsable.get_full_name()}'
            if movimiento.confirmado_con_pin:
                descripcion += ' (Confirmado con PIN)'

            self.audit_description_template = descripcion

            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mensaje de éxito
            messages.success(
                self.request,
                f'Movimiento de activo {movimiento.activo.codigo} registrado exitosamente. '
                'El estado del activo ha sido actualizado.'
            )
            
            # Redirigir al listado de movimientos
            return HttpResponseRedirect(self.get_success_url())
    
    def form_invalid(self, form: MovimientoActivoForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Muestra los errores del formulario y vuelve a renderizar el template.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)

    def get_initial(self) -> dict[str, Any]:
        """Inicializa el formulario con datos por defecto si viene un activo en la URL."""
        initial = super().get_initial()
        
        # Si viene un activo en la URL, pre-seleccionarlo
        activo_id = self.request.GET.get('activo')
        if activo_id:
            try:
                activo = Activo.objects.get(pk=activo_id, activo=True, eliminado=False)
                initial['activo'] = activo
            except Activo.DoesNotExist:
                pass
        
        return initial
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto, incluyendo categorías y estados para filtros."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Movimiento de Activo'
        context['action'] = 'Registrar'
        
        # Agregar categorías y estados para los filtros de búsqueda
        context['categorias'] = CategoriaActivo.objects.filter(
            activo=True, 
            eliminado=False
        ).order_by('nombre')
        
        context['estados'] = EstadoActivo.objects.filter(
            activo=True, 
            eliminado=False
        ).order_by('nombre')
        
        # Si viene un activo en la URL, agregarlo al contexto
        activo_id = self.request.GET.get('activo')
        if activo_id:
            try:
                context['activo_inicial'] = Activo.objects.get(
                    pk=activo_id, 
                    activo=True, 
                    eliminado=False
                )
            except Activo.DoesNotExist:
                pass
        
        return context


# ==================== VISTAS DE CATEGORÍAS ====================

class CategoriaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar categorías de activos.

    Permisos: activos.view_categoriaactivo
    """
    model = CategoriaActivo
    template_name = 'activos/lista_categorias.html'
    context_object_name = 'categorias'
    permission_required = 'activos.view_categoriaactivo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[CategoriaActivo]:
        """Retorna solo categorías no eliminadas."""
        return CategoriaActivo.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Categorías de Activos'
        return context


class CategoriaCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear una nueva categoría de activo.

    Permisos: activos.add_categoriaactivo
    Auditoría: Registra acción CREAR automáticamente
    """
    model = CategoriaActivo
    form_class = CategoriaActivoForm
    template_name = 'activos/form_categoria.html'
    permission_required = 'activos.add_categoriaactivo'
    success_url = reverse_lazy('activos:lista_categorias')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó categoría {obj.codigo} - {obj.nombre}'
    success_message = 'Categoría {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Categoría'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: CategoriaActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación antes de guardar.
        """
        try:
            # Asignar usuario de creación antes de guardar
            categoria = form.save(commit=False)
            categoria.usuario_creacion = self.request.user
            categoria.usuario_actualizacion = self.request.user
            categoria.save()
            self.object = categoria
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear categoría: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear la categoría: {str(e)}'
            )
            return self.form_invalid(form)


class CategoriaUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una categoría de activo existente.

    Permisos: activos.change_categoriaactivo
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = CategoriaActivo
    form_class = CategoriaActivoForm
    template_name = 'activos/form_categoria.html'
    permission_required = 'activos.change_categoriaactivo'
    success_url = reverse_lazy('activos:lista_categorias')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó categoría {obj.codigo} - {obj.nombre}'
    success_message = 'Categoría {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet[CategoriaActivo]:
        """Solo permite editar categorías no eliminadas."""
        return CategoriaActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Categoría {self.object.codigo}'
        context['action'] = 'Editar'
        context['categoria'] = self.object
        return context

    def form_valid(self, form: CategoriaActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            categoria = form.save(commit=False)
            categoria.usuario_actualizacion = self.request.user
            categoria.save()
            self.object = categoria
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar categoría: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar la categoría: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: CategoriaActivoForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Asegurar que el objeto esté disponible en el contexto
        # Si no está disponible, obtenerlo del pk de la URL
        if not hasattr(self, 'object') or self.object is None:
            pk = self.kwargs.get('pk')
            if pk:
                self.object = self.get_object()
        
        # Renderizar el template con el contexto correcto
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class CategoriaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una categoría de activo.

    Permisos: activos.delete_categoriaactivo
    Auditoría: Registra acción ELIMINAR automáticamente
    Implementa soft delete
    """
    model = CategoriaActivo
    template_name = 'activos/eliminar_categoria.html'
    permission_required = 'activos.delete_categoriaactivo'
    success_url = reverse_lazy('activos:lista_categorias')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó categoría {obj.codigo} - {obj.nombre}'
    success_message = 'Categoría {obj.codigo} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet[CategoriaActivo]:
        """Solo permite eliminar categorías no eliminadas."""
        return CategoriaActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Categoría {self.object.codigo}'
        context['categoria'] = self.object
        return context


# ==================== VISTAS DE ESTADOS DE ACTIVO ====================

class EstadoActivoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar estados de activos."""
    model = EstadoActivo
    template_name = 'activos/lista_estados.html'
    context_object_name = 'estados'
    permission_required = 'activos.view_estadoactivo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[EstadoActivo]:
        """Retorna solo estados no eliminados."""
        return EstadoActivo.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Estados de Activos'
        return context


class EstadoActivoCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear un nuevo estado de activo."""
    model = EstadoActivo
    form_class = EstadoActivoForm
    template_name = 'activos/form_estado.html'
    permission_required = 'activos.add_estadoactivo'
    success_url = reverse_lazy('activos:lista_estados')

    audit_action = 'CREAR'
    audit_description_template = 'Creó estado {obj.codigo} - {obj.nombre}'
    success_message = 'Estado {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Estado'
        context['action'] = 'Crear'
        return context
    
    def form_valid(self, form: EstadoActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear estado: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear el estado: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: EstadoActivoForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Muestra los errores del formulario al usuario.
        """
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        return super().form_invalid(form)


class EstadoActivoUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar un estado de activo existente."""
    model = EstadoActivo
    form_class = EstadoActivoForm
    template_name = 'activos/form_estado.html'
    permission_required = 'activos.change_estadoactivo'
    success_url = reverse_lazy('activos:lista_estados')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó estado {obj.codigo} - {obj.nombre}'
    success_message = 'Estado {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet[EstadoActivo]:
        """Solo permite editar estados no eliminados."""
        return EstadoActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Estado {self.object.codigo}'
        context['action'] = 'Editar'
        context['estado'] = self.object
        return context

    def form_valid(self, form: EstadoActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            estado = form.save(commit=False)
            estado.usuario_actualizacion = self.request.user
            estado.save()
            self.object = estado
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar estado: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar el estado: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: EstadoActivoForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Asegurar que el objeto esté disponible en el contexto
        # Si no está disponible, obtenerlo del pk de la URL
        if not hasattr(self, 'object') or self.object is None:
            pk = self.kwargs.get('pk')
            if pk:
                try:
                    self.object = self.get_object()
                except Exception:
                    # Si no se puede obtener el objeto, redirigir a la lista
                    messages.error(self.request, 'No se pudo encontrar el estado a editar.')
                    return HttpResponseRedirect(reverse_lazy('activos:lista_estados'))
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el contexto correcto
        # Pasar el formulario al contexto explícitamente
        context = self.get_context_data()
        context['form'] = form
        return render(self.request, self.template_name, context)


class EstadoActivoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un estado de activo."""
    model = EstadoActivo
    template_name = 'activos/eliminar_estado.html'
    permission_required = 'activos.delete_estadoactivo'
    success_url = reverse_lazy('activos:lista_estados')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó estado {obj.codigo} - {obj.nombre}'
    success_message = 'Estado {obj.codigo} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet[EstadoActivo]:
        """Solo permite eliminar estados no eliminados."""
        return EstadoActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Estado {self.object.codigo}'
        context['estado'] = self.object
        return context


# ==================== VISTAS DE UBICACIONES ====================

class UbicacionListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar ubicaciones."""
    model = Ubicacion
    template_name = 'activos/lista_ubicaciones.html'
    context_object_name = 'ubicaciones'
    permission_required = 'activos.view_ubicacion'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Ubicacion]:
        """Retorna solo ubicaciones no eliminadas."""
        return Ubicacion.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Ubicaciones'
        return context


class UbicacionCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear una nueva ubicación."""
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'activos/form_ubicacion.html'
    permission_required = 'activos.add_ubicacion'
    success_url = reverse_lazy('activos:lista_ubicaciones')

    audit_action = 'CREAR'
    audit_description_template = 'Creó ubicación {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Ubicación'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: UbicacionForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear ubicación: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear la ubicación: {str(e)}'
            )
            return self.form_invalid(form)


class UbicacionUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar una ubicación existente."""
    model = Ubicacion
    form_class = UbicacionForm
    template_name = 'activos/form_ubicacion.html'
    permission_required = 'activos.change_ubicacion'
    success_url = reverse_lazy('activos:lista_ubicaciones')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó ubicación {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet[Ubicacion]:
        """Solo permite editar ubicaciones no eliminadas."""
        return Ubicacion.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Ubicación {self.object.codigo}'
        context['action'] = 'Editar'
        context['ubicacion'] = self.object
        return context

    def form_valid(self, form: UbicacionForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_actualizacion = self.request.user
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar ubicación: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar la ubicación: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: UbicacionForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class UbicacionDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) una ubicación."""
    model = Ubicacion
    template_name = 'activos/eliminar_ubicacion.html'
    permission_required = 'activos.delete_ubicacion'
    success_url = reverse_lazy('activos:lista_ubicaciones')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó ubicación {obj.codigo} - {obj.nombre}'
    success_message = 'Ubicación {obj.codigo} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet[Ubicacion]:
        """Solo permite eliminar ubicaciones no eliminadas."""
        return Ubicacion.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Ubicación {self.object.codigo}'
        context['ubicacion'] = self.object
        return context


# ==================== VISTAS DE TIPOS DE MOVIMIENTO ====================

class TipoMovimientoListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar tipos de movimiento."""
    model = TipoMovimientoActivo
    template_name = 'activos/lista_tipos_movimiento.html'
    context_object_name = 'tipos_movimiento'
    permission_required = 'activos.view_tipomovimientoactivo'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[TipoMovimientoActivo]:
        """Retorna solo tipos de movimiento no eliminados."""
        return TipoMovimientoActivo.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Tipos de Movimiento'
        return context


class TipoMovimientoCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear un nuevo tipo de movimiento."""
    model = TipoMovimientoActivo
    form_class = TipoMovimientoActivoForm
    template_name = 'activos/form_tipo_movimiento.html'
    permission_required = 'activos.add_tipomovimientoactivo'
    success_url = reverse_lazy('activos:lista_tipos_movimiento')

    audit_action = 'CREAR'
    audit_description_template = 'Creó tipo de movimiento {obj.codigo} - {obj.nombre}'
    success_message = 'Tipo de movimiento {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Tipo de Movimiento'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: TipoMovimientoActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear tipo de movimiento: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear el tipo de movimiento: {str(e)}'
            )
            return self.form_invalid(form)


class TipoMovimientoUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar un tipo de movimiento existente."""
    model = TipoMovimientoActivo
    form_class = TipoMovimientoActivoForm
    template_name = 'activos/form_tipo_movimiento.html'
    permission_required = 'activos.change_tipomovimientoactivo'
    success_url = reverse_lazy('activos:lista_tipos_movimiento')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó tipo de movimiento {obj.codigo} - {obj.nombre}'
    success_message = 'Tipo de movimiento {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet[TipoMovimientoActivo]:
        """Solo permite editar tipos de movimiento no eliminados."""
        return TipoMovimientoActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tipo de Movimiento {self.object.codigo}'
        context['action'] = 'Editar'
        context['tipo_movimiento'] = self.object
        return context

    def form_valid(self, form: TipoMovimientoActivoForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_actualizacion = self.request.user
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar tipo de movimiento: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar el tipo de movimiento: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: TipoMovimientoActivoForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class TipoMovimientoDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un tipo de movimiento."""
    model = TipoMovimientoActivo
    template_name = 'activos/eliminar_tipo_movimiento.html'
    permission_required = 'activos.delete_tipomovimientoactivo'
    success_url = reverse_lazy('activos:lista_tipos_movimiento')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó tipo de movimiento {obj.codigo} - {obj.nombre}'
    success_message = 'Tipo de movimiento {obj.codigo} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet[TipoMovimientoActivo]:
        """Solo permite eliminar tipos de movimiento no eliminados."""
        return TipoMovimientoActivo.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Tipo de Movimiento {self.object.codigo}'
        context['tipo_movimiento'] = self.object
        return context


# ==================== VISTAS DE MARCAS ====================

class MarcaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar marcas."""
    model = Marca
    template_name = 'activos/lista_marcas.html'
    context_object_name = 'marcas'
    permission_required = 'activos.view_marca'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Marca]:
        """Retorna solo marcas no eliminadas."""
        return Marca.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Marcas'
        return context


class MarcaCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear una nueva marca."""
    model = Marca
    form_class = MarcaForm
    template_name = 'activos/form_marca.html'
    permission_required = 'activos.add_marca'
    success_url = reverse_lazy('activos:lista_marcas')

    audit_action = 'CREAR'
    audit_description_template = 'Creó marca {obj.codigo} - {obj.nombre}'
    success_message = 'Marca {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Marca'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: MarcaForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear marca: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear la marca: {str(e)}'
            )
            return self.form_invalid(form)


class MarcaUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar una marca existente."""
    model = Marca
    form_class = MarcaForm
    template_name = 'activos/form_marca.html'
    permission_required = 'activos.change_marca'
    success_url = reverse_lazy('activos:lista_marcas')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó marca {obj.codigo} - {obj.nombre}'
    success_message = 'Marca {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet[Marca]:
        """Solo permite editar marcas no eliminadas."""
        return Marca.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Marca {self.object.codigo}'
        context['action'] = 'Editar'
        context['marca'] = self.object
        return context

    def form_valid(self, form: MarcaForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_actualizacion = self.request.user
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar marca: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar la marca: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: MarcaForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class MarcaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) una marca."""
    model = Marca
    template_name = 'activos/eliminar_marca.html'
    permission_required = 'activos.delete_marca'
    success_url = reverse_lazy('activos:lista_marcas')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó marca {obj.codigo} - {obj.nombre}'
    success_message = 'Marca {obj.codigo} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet[Marca]:
        """Solo permite eliminar marcas no eliminadas."""
        return Marca.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Marca {self.object.codigo}'
        context['marca'] = self.object
        return context


# ==================== VISTAS DE TALLERES ====================

class TallerListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar talleres."""
    model = Taller
    template_name = 'activos/lista_talleres.html'
    context_object_name = 'talleres'
    permission_required = 'activos.view_taller'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Taller]:
        """Retorna solo talleres no eliminados."""
        return Taller.objects.filter(eliminado=False).select_related('responsable').order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Talleres'
        return context


class TallerCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear un nuevo taller."""
    model = Taller
    form_class = TallerForm
    template_name = 'activos/form_taller.html'
    permission_required = 'activos.add_taller'
    success_url = reverse_lazy('activos:lista_talleres')

    audit_action = 'CREAR'
    audit_description_template = 'Creó taller {obj.codigo} - {obj.nombre}'
    success_message = 'Taller {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Taller'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: TallerForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear taller: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear el taller: {str(e)}'
            )
            return self.form_invalid(form)


class TallerUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar un taller existente."""
    model = Taller
    form_class = TallerForm
    template_name = 'activos/form_taller.html'
    permission_required = 'activos.change_taller'
    success_url = reverse_lazy('activos:lista_talleres')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó taller {obj.codigo} - {obj.nombre}'
    success_message = 'Taller {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet[Taller]:
        """Solo permite editar talleres no eliminados."""
        return Taller.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Taller {self.object.codigo}'
        context['action'] = 'Editar'
        context['taller'] = self.object
        return context

    def form_valid(self, form: TallerForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_actualizacion = self.request.user
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar taller: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar el taller: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: TallerForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class TallerDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) un taller."""
    model = Taller
    template_name = 'activos/eliminar_taller.html'
    permission_required = 'activos.delete_taller'
    success_url = reverse_lazy('activos:lista_talleres')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó taller {obj.codigo} - {obj.nombre}'
    success_message = 'Taller {obj.codigo} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet[Taller]:
        """Solo permite eliminar talleres no eliminados."""
        return Taller.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Taller {self.object.codigo}'
        context['taller'] = self.object
        return context


# ==================== VISTAS DE PROVENIENCIAS ====================

class ProvenienciaListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar proveniencias."""
    model = Proveniencia
    template_name = 'activos/lista_proveniencias.html'
    context_object_name = 'proveniencias'
    permission_required = 'activos.view_proveniencia'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Proveniencia]:
        """Retorna solo proveniencias no eliminadas."""
        return Proveniencia.objects.filter(eliminado=False).order_by('codigo')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Proveniencias'
        return context


class ProvenienciaCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear una nueva proveniencia."""
    model = Proveniencia
    form_class = ProvenienciaForm
    template_name = 'activos/form_proveniencia.html'
    permission_required = 'activos.add_proveniencia'
    success_url = reverse_lazy('activos:lista_proveniencias')

    audit_action = 'CREAR'
    audit_description_template = 'Creó proveniencia {obj.codigo} - {obj.nombre}'
    success_message = 'Proveniencia {obj.nombre} creada exitosamente.'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Proveniencia'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form: ProvenienciaForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de creación y actualización antes de guardar.
        """
        try:
            # Asignar usuario de creación y actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_creacion = self.request.user
            self.object.usuario_actualizacion = self.request.user
            
            # Asegurar que los campos del BaseModel estén configurados
            self.object.activo = form.cleaned_data.get('activo', True)
            self.object.eliminado = False
            
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al crear proveniencia: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al crear la proveniencia: {str(e)}'
            )
            return self.form_invalid(form)


class ProvenienciaUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar una proveniencia existente."""
    model = Proveniencia
    form_class = ProvenienciaForm
    template_name = 'activos/form_proveniencia.html'
    permission_required = 'activos.change_proveniencia'
    success_url = reverse_lazy('activos:lista_proveniencias')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó proveniencia {obj.codigo} - {obj.nombre}'
    success_message = 'Proveniencia {obj.nombre} actualizada exitosamente.'

    def get_queryset(self) -> QuerySet[Proveniencia]:
        """Solo permite editar proveniencias no eliminadas."""
        return Proveniencia.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Proveniencia {self.object.codigo}'
        context['action'] = 'Editar'
        context['proveniencia'] = self.object
        return context

    def form_valid(self, form: ProvenienciaForm) -> HttpResponse:
        """
        Procesa el formulario válido con log de auditoría.
        
        Asigna el usuario de actualización antes de guardar.
        """
        try:
            # Asignar usuario de actualización antes de guardar
            self.object = form.save(commit=False)
            self.object.usuario_actualizacion = self.request.user
            self.object.save()
            
            # Registrar log de auditoría
            self.log_action(self.object, self.request)
            
            # Mostrar mensaje de éxito y redirigir
            messages.success(self.request, self.get_success_message(self.object))
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            # Si hay un error, mostrar mensaje y volver a mostrar el formulario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al actualizar proveniencia: {str(e)}', exc_info=True)
            messages.error(
                self.request,
                f'Error al actualizar la proveniencia: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form: ProvenienciaForm) -> HttpResponse:
        """
        Maneja el caso cuando el formulario no es válido.
        
        Renderiza el template de edición con los errores, manteniendo el contexto correcto.
        """
        from django.shortcuts import render
        
        # Mostrar errores de validación
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        else:
            messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        
        # Renderizar el template con el formulario y errores
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)


class ProvenienciaDeleteView(BaseAuditedViewMixin, SoftDeleteMixin, DeleteView):
    """Vista para eliminar (soft delete) una proveniencia."""
    model = Proveniencia
    template_name = 'activos/eliminar_proveniencia.html'
    permission_required = 'activos.delete_proveniencia'
    success_url = reverse_lazy('activos:lista_proveniencias')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó proveniencia {obj.codigo} - {obj.nombre}'
    success_message = 'Proveniencia {obj.codigo} eliminada exitosamente.'

    def get_queryset(self) -> QuerySet[Proveniencia]:
        """Solo permite eliminar proveniencias no eliminadas."""
        return Proveniencia.objects.filter(eliminado=False)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Proveniencia {self.object.codigo}'
        context['proveniencia'] = self.object
        return context


# ==================== NOTA ====================
# Los activos no requieren unidad de medida ya que cada activo es único
# y no maneja cantidades. No existe el modelo UbicacionActual ya que
# la ubicación se rastrea mediante MovimientoActivo.


# ==================== VISTAS AJAX PARA PIN ====================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


@login_required
@require_http_methods(["POST"])
def validar_pin_responsable(request):
    """
    Vista AJAX para validar el PIN del responsable antes de confirmar un movimiento.
    
    Recibe:
        - responsable_id: ID del usuario responsable
        - pin: PIN de 4 dígitos ingresado
    
    Retorna:
        - success: True si el PIN es válido, False si no
        - message: Mensaje descriptivo
        - intentos_restantes: Número de intentos restantes (si aplica)
        - bloqueado: True si el usuario quedó bloqueado
    """
    try:
        # Leer datos desde request.POST (form-urlencoded)
        responsable_id = request.POST.get('responsable_id')
        pin_ingresado = request.POST.get('pin', '').strip()
        
        if not responsable_id or not pin_ingresado:
            return JsonResponse({
                'success': False,
                'message': 'Debe proporcionar el ID del responsable y el PIN.'
            }, status=400)
        
        # Validar que el PIN sea de 4 dígitos numéricos
        if not pin_ingresado.isdigit() or len(pin_ingresado) != 4:
            return JsonResponse({
                'success': False,
                'message': 'El PIN debe ser de 4 dígitos numéricos.'
            }, status=400)
        
        # Convertir responsable_id a entero
        try:
            responsable_id = int(responsable_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'ID de responsable inválido.'
            }, status=400)
        
        # Obtener el usuario responsable
        try:
            from django.contrib.auth.models import User
            responsable = User.objects.get(pk=responsable_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario responsable no encontrado.'
            }, status=404)
        
        # Obtener la configuración de seguridad del usuario
        try:
            from apps.accounts.models import UserSecure, AuditoriaPin
            user_secure = UserSecure.objects.get(user=responsable, activo=True, eliminado=False)
        except UserSecure.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'El usuario {responsable.get_full_name()} no tiene un PIN configurado.'
            }, status=400)
        
        # Verificar si el usuario está bloqueado
        if user_secure.bloqueado:
            # Registrar intento en auditoría
            AuditoriaPin.objects.create(
                usuario=responsable,
                accion='INTENTO_BLOQUEADO',
                exitoso=False,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalles={'mensaje': 'Intento de uso con usuario bloqueado'},
                usuario_creacion=request.user,
                usuario_actualizacion=request.user
            )
            
            return JsonResponse({
                'success': False,
                'message': f'El usuario {responsable.get_full_name()} está bloqueado. Contacte al administrador.',
                'bloqueado': True
            }, status=403)
        
        # Verificar el PIN
        pin_valido = user_secure.verificar_pin(pin_ingresado)
        
        if pin_valido:
            # PIN correcto - resetear intentos fallidos
            user_secure.resetear_intentos()
            
            # Registrar en auditoría
            AuditoriaPin.objects.create(
                usuario=responsable,
                accion='CONFIRMACION_ENTREGA',
                exitoso=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalles={'mensaje': 'PIN validado correctamente para movimiento de activo'},
                usuario_creacion=request.user,
                usuario_actualizacion=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'PIN validado correctamente. Movimiento confirmado por {responsable.get_full_name()}.'
            })
        else:
            # PIN incorrecto - registrar intento fallido
            user_secure.registrar_intento_fallido()
            intentos_restantes = max(0, 3 - user_secure.intentos_fallidos)
            
            # Registrar en auditoría
            AuditoriaPin.objects.create(
                usuario=responsable,
                accion='INTENTO_FALLIDO',
                exitoso=False,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalles={
                    'mensaje': 'PIN incorrecto',
                    'intentos_fallidos': user_secure.intentos_fallidos,
                    'bloqueado': user_secure.bloqueado
                },
                usuario_creacion=request.user,
                usuario_actualizacion=request.user
            )
            
            if user_secure.bloqueado:
                return JsonResponse({
                    'success': False,
                    'message': f'PIN incorrecto. El usuario {responsable.get_full_name()} ha sido bloqueado tras 3 intentos fallidos.',
                    'intentos_restantes': 0,
                    'bloqueado': True
                }, status=403)
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'PIN incorrecto. Le quedan {intentos_restantes} intentos.',
                    'intentos_restantes': intentos_restantes,
                    'bloqueado': False
                }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error inesperado: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def buscar_activos_similares(request):
    """
    Vista AJAX para buscar activos similares disponibles.
    
    Busca activos por nombre, categoría, marca, etc. y devuelve los disponibles
    para selección múltiple en movimientos.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Obtener parámetros de búsqueda
    termino_busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    estado_id = request.GET.get('estado', '')
    pagina = request.GET.get('page', 1)
    por_pagina = int(request.GET.get('per_page', 10))
    
    # Construir query base - solo activos activos y no eliminados
    # IMPORTANTE: No usar cache aquí, siempre obtener el estado más reciente
    activos = Activo.objects.filter(
        activo=True,
        eliminado=False
    ).select_related('categoria', 'estado', 'marca').order_by('codigo')
    
    # Filtrar por término de búsqueda (nombre, código, número de serie)
    if termino_busqueda:
        activos = activos.filter(
            Q(nombre__icontains=termino_busqueda) |
            Q(codigo__icontains=termino_busqueda) |
            Q(numero_serie__icontains=termino_busqueda) |
            Q(descripcion__icontains=termino_busqueda)
        )
    
    # Filtrar por categoría
    if categoria_id:
        activos = activos.filter(categoria_id=categoria_id)
    
    # Filtrar por estado
    if estado_id:
        activos = activos.filter(estado_id=estado_id)
    
    # Ordenar por código
    activos = activos.order_by('codigo')
    
    # Paginar resultados
    paginator = Paginator(activos, por_pagina)
    pagina_obj = paginator.get_page(pagina)
    
    # Construir respuesta JSON
    activos_data = []
    for activo in pagina_obj:
        activos_data.append({
            'id': activo.id,
            'codigo': activo.codigo,
            'nombre': activo.nombre,
            'categoria': activo.categoria.nombre if activo.categoria else '',
            'estado': activo.estado.nombre if activo.estado else '',
            'estado_id': activo.estado.id if activo.estado else None,
            'estado_codigo': activo.estado.codigo if activo.estado else '',
            'marca': activo.marca.nombre if activo.marca else '',
            'numero_serie': activo.numero_serie or 'N/A',
            'descripcion': activo.descripcion or ''
        })
    
    return JsonResponse({
        'success': True,
        'activos': activos_data,
        'total': paginator.count,
        'pagina_actual': pagina_obj.number,
        'total_paginas': paginator.num_pages,
        'tiene_anterior': pagina_obj.has_previous(),
        'tiene_siguiente': pagina_obj.has_next()
    })