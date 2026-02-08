"""
Class-Based Views para el módulo de compras.

Este archivo implementa todas las vistas usando CBVs siguiendo SOLID y DRY:
- Reutilización de mixins de core.mixins
- Separación de responsabilidades (Repository Pattern + Service Layer)
- Código limpio y mantenible
- Type hints completos
- Auditoría automática
"""
from typing import Any
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from decimal import Decimal
from core.mixins import (
    BaseAuditedViewMixin, AtomicTransactionMixin, SoftDeleteMixin,
    PaginatedListMixin, FilteredListMixin
)
from .models import (
    Proveedor, OrdenCompra, DetalleOrdenCompraArticulo, DetalleOrdenCompra,
    EstadoOrdenCompra
)
from .forms import (
    ProveedorForm, OrdenCompraForm, DetalleOrdenCompraArticuloForm,
    DetalleOrdenCompraActivoForm, OrdenCompraFiltroForm, EstadoOrdenCompraForm
)
from .repositories import (
    ProveedorRepository, OrdenCompraRepository, EstadoOrdenCompraRepository
)
from .services import (
    ProveedorService, OrdenCompraService
)
from apps.bodega.models import Bodega, Articulo, Movimiento, TipoMovimiento
from apps.solicitudes.repositories import SolicitudRepository, EstadoSolicitudRepository


# ==================== VISTA MENÚ PRINCIPAL ====================

class MenuComprasView(BaseAuditedViewMixin, TemplateView):
    """
    Vista del menú principal del módulo de compras.

    Muestra estadísticas y accesos rápidos basados en permisos del usuario.
    Permisos: compras.view_ordencompra
    Utiliza: Repositories para acceso a datos optimizado
    """
    template_name = 'compras/menu_compras.html'
    permission_required = 'compras.view_ordencompra'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega estadísticas y permisos al contexto usando repositories."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Inicializar repositories
        orden_repo = OrdenCompraRepository()
        proveedor_repo = ProveedorRepository()
        estado_repo = EstadoOrdenCompraRepository()
        solicitud_repo = SolicitudRepository()
        estado_solicitud_repo = EstadoSolicitudRepository()

        # Estadísticas del módulo usando repositories
        estado_pendiente = estado_repo.get_by_codigo('PENDIENTE')
        ordenes_pendientes_count = 0
        if estado_pendiente:
            ordenes_pendientes_count = orden_repo.filter_by_estado(estado_pendiente).count()

        # Obtener solicitudes en estado COMPRAR sin órdenes de compra asociadas
        estado_comprar = estado_solicitud_repo.get_by_codigo('COMPRAR')
        solicitudes_pendientes_count = 0
        if estado_comprar:
            # Obtener solicitudes para comprar que no tienen órdenes de compra asociadas
            solicitudes_comprar = solicitud_repo.filter_by_estado(estado_comprar)
            solicitudes_pendientes_count = solicitudes_comprar.filter(ordenes_compra__isnull=True).count()

        context['stats'] = {
            'total_ordenes': orden_repo.get_all().count(),
            'ordenes_pendientes': ordenes_pendientes_count,
            'proveedores_activos': proveedor_repo.get_active().count(),
            'solicitudes_pendientes': solicitudes_pendientes_count,
        }

        # Permisos del usuario
        context['permisos'] = {
            'puede_crear': user.has_perm('compras.add_ordencompra'),
            'puede_gestionar': user.has_perm('compras.change_ordencompra'),
        }

        context['titulo'] = 'Módulo de Compras'
        return context


# ==================== VISTAS DE PROVEEDORES ====================

class ProveedorListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """
    Vista para listar proveedores.

    Permisos: compras.view_proveedor
    Utiliza: ProveedorRepository para acceso a datos
    """
    model = Proveedor
    template_name = 'compras/proveedor/lista.html'
    context_object_name = 'proveedores'
    permission_required = 'compras.view_proveedor'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        """Retorna proveedores usando repository."""
        proveedor_repo = ProveedorRepository()

        # Búsqueda por query string
        query = self.request.GET.get('q', '').strip()
        if query:
            return proveedor_repo.search(query)

        return proveedor_repo.get_all()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Proveedores'
        return context


class ProveedorCreateView(BaseAuditedViewMixin, CreateView):
    """
    Vista para crear un nuevo proveedor.

    Permisos: compras.add_proveedor
    Auditoría: Registra acción CREAR automáticamente
    """
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'compras/proveedor/form.html'
    permission_required = 'compras.add_proveedor'
    success_url = reverse_lazy('compras:proveedor_lista')

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó proveedor {obj.rut} - {obj.razon_social}'

    # Mensaje de éxito
    success_message = 'Proveedor {obj.razon_social} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Proveedor'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class ProveedorUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar un proveedor existente.

    Permisos: compras.change_proveedor
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'compras/proveedor/form.html'
    permission_required = 'compras.change_proveedor'
    success_url = reverse_lazy('compras:proveedor_lista')

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó proveedor {obj.rut} - {obj.razon_social}'

    # Mensaje de éxito
    success_message = 'Proveedor {obj.razon_social} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite editar proveedores no eliminados."""
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Proveedor {self.object.razon_social}'
        context['action'] = 'Actualizar'
        context['proveedor'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class ProveedorDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un proveedor.

    Permisos: compras.delete_proveedor
    Auditoría: Registra acción ELIMINAR automáticamente
    Utiliza: ProveedorService para validaciones y eliminación
    """
    model = Proveedor
    template_name = 'compras/proveedor/eliminar.html'
    permission_required = 'compras.delete_proveedor'
    success_url = reverse_lazy('compras:proveedor_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó proveedor {obj.rut} - {obj.razon_social}'

    # Mensaje de éxito
    success_message = 'Proveedor {obj.razon_social} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        """Solo permite eliminar proveedores no eliminados."""
        proveedor_repo = ProveedorRepository()
        return proveedor_repo.get_all()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Proveedor {self.object.razon_social}'
        context['proveedor'] = self.object
        return context

    def delete(self, request, *args, **kwargs):
        """Elimina usando service con validaciones."""
        self.object = self.get_object()
        proveedor_service = ProveedorService()

        try:
            proveedor_service.eliminar_proveedor(self.object)
            messages.success(request, self.get_success_message(self.object))
            self.log_action(self.object, request)
            return redirect(self.success_url)
        except ValidationError as e:
            messages.error(request, str(e.message_dict.get('__all__', [e])[0]))
            return redirect('compras:proveedor_lista')


# ==================== VISTAS DE ÓRDENES DE COMPRA ====================

class OrdenCompraListView(BaseAuditedViewMixin, PaginatedListMixin, FilteredListMixin, ListView):
    """
    Vista para listar órdenes de compra con filtros.

    Permisos: compras.view_ordencompra
    Filtros: Estado, proveedor, búsqueda por número
    Utiliza: OrdenCompraRepository para acceso a datos optimizado
    """
    model = OrdenCompra
    template_name = 'compras/orden/lista.html'
    context_object_name = 'ordenes'
    permission_required = 'compras.view_ordencompra'
    paginate_by = 25
    filter_form_class = OrdenCompraFiltroForm

    def get_queryset(self) -> QuerySet:
        """Retorna órdenes usando repository con filtros."""
        orden_repo = OrdenCompraRepository()
        queryset = orden_repo.get_all()

        # Aplicar filtros del formulario
        form = self.filter_form_class(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data

            # Filtro de búsqueda
            if data.get('q'):
                queryset = orden_repo.search(data['q'])

            # Filtro por estado
            if data.get('estado'):
                queryset = queryset.filter(estado=data['estado'])

            # Filtro por proveedor
            if data.get('proveedor'):
                queryset = queryset.filter(proveedor=data['proveedor'])

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Órdenes de Compra'
        context['form'] = self.filter_form_class(self.request.GET)
        return context


class OrdenCompraDetailView(BaseAuditedViewMixin, DetailView):
    """
    Vista para ver el detalle de una orden de compra.

    Permisos: compras.view_ordencompra
    """
    model = OrdenCompra
    template_name = 'compras/orden/detalle.html'
    context_object_name = 'orden'
    permission_required = 'compras.view_ordencompra'

    def get_queryset(self) -> QuerySet:
        """Optimiza consultas con select_related."""
        return super().get_queryset().select_related(
            'proveedor', 'estado', 'solicitante', 'aprobador', 'bodega_destino'
        )

    def get_context_data(self, **kwargs) -> dict:
        """Agrega detalles al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Orden de Compra {self.object.numero}'

        # Detalles de artículos
        context['detalles_articulos'] = self.object.detalles_articulos.filter(
            eliminado=False
        ).select_related('articulo', 'articulo__categoria')

        # Detalles de activos
        context['detalles_activos'] = self.object.detalles.filter(
            eliminado=False
        ).select_related('activo')

        return context

    def render_to_response(self, context, **response_kwargs):
        """Renderiza template parcial si es petición AJAX."""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.template_name = 'compras/partials/modal_detalle.html'
        return super().render_to_response(context, **response_kwargs)


class OrdenCompraCreateView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para crear una nueva orden de compra.

    Permisos: compras.add_ordencompra
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza que el número se genere correctamente
    """
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'compras/orden/form.html'
    permission_required = 'compras.add_ordencompra'

    # Configuración de auditoría
    audit_action = 'CREAR'
    audit_description_template = 'Creó orden de compra {obj.numero}'

    # Mensaje de éxito
    success_message = 'Orden de compra {obj.numero} creada exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la orden creada."""
        return reverse_lazy('compras:orden_compra_detalle', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        from apps.bodega.models import Articulo
        from apps.activos.models import Activo

        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Orden de Compra'
        context['action'] = 'Crear'

        # Pasar artículos y activos disponibles para los modales
        context['articulos_disponibles'] = Articulo.objects.filter(
            activo=True, eliminado=False
        ).select_related('categoria', 'unidad_medida').order_by('nombre')

        context['activos_disponibles'] = Activo.objects.filter(
            activo=True, eliminado=False
        ).select_related('categoria').order_by('nombre')

        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría y genera número automático."""
        import json
        from decimal import Decimal
        from core.utils.business import generar_codigo_con_anio
        from apps.solicitudes.models import DetalleSolicitud
        from apps.bodega.models import Articulo
        from apps.activos.models import Activo

        # Asignar solicitante
        form.instance.solicitante = self.request.user

        # Generar número de orden automáticamente con año
        form.instance.numero = generar_codigo_con_anio('OC', OrdenCompra, 'numero', longitud=6)

        response = super().form_valid(form)

        # Actualizar estado de solicitudes asociadas a "En Proceso"
        solicitudes_asociadas = self.object.solicitudes.all()
        if solicitudes_asociadas.exists():
            from apps.solicitudes.models import EstadoSolicitud
            try:
                estado_proceso = EstadoSolicitud.objects.get(codigo='PROCESO', activo=True)
                solicitudes_actualizadas = 0
                for solicitud in solicitudes_asociadas:
                    if solicitud.estado.codigo != 'PROCESO':
                        solicitud.estado = estado_proceso
                        solicitud.save()
                        solicitudes_actualizadas += 1
                        print(f"DEBUG: Solicitud {solicitud.numero} actualizada a estado 'En Proceso'")
                if solicitudes_actualizadas > 0:
                    print(f"DEBUG: {solicitudes_actualizadas} solicitud(es) actualizada(s) a 'En Proceso'")
            except EstadoSolicitud.DoesNotExist:
                print("ERROR: No se encontró el estado 'PROCESO' para solicitudes")

        # NOTA: Ya NO creamos detalles automáticamente desde solicitudes
        # porque el JavaScript ahora carga los items en tablas editables
        # y los valores editados se envían vía JSON

        # Procesar artículos agregados (tanto manuales como de solicitudes)
        articulos_json = self.request.POST.get('articulos_json', '')
        print(f"DEBUG: articulos_json recibido: '{articulos_json}'")
        if articulos_json:
            try:
                articulos_data = json.loads(articulos_json)
                print(f"DEBUG: Artículos parseados: {articulos_data}")
                for item in articulos_data:
                    articulo = Articulo.objects.get(pk=item['articulo_id'])
                    detalle = DetalleOrdenCompraArticulo.objects.create(
                        orden_compra=self.object,
                        articulo=articulo,
                        cantidad=item['cantidad'],
                        precio_unitario=Decimal(str(item.get('precio_unitario', 0))),
                        descuento=Decimal(str(item.get('descuento', 0)))
                    )
                    print(f"DEBUG: Creado detalle artículo ID {detalle.id} para orden {self.object.numero}")
            except (json.JSONDecodeError, Articulo.DoesNotExist, KeyError, ValueError) as e:
                # Log error but continue
                print(f"ERROR procesando artículos: {e}")
                import traceback
                traceback.print_exc()

        # Procesar bienes/activos agregados manualmente
        bienes_json = self.request.POST.get('bienes_json', '')
        print(f"DEBUG: bienes_json recibido: '{bienes_json}'")
        if bienes_json:
            try:
                bienes_data = json.loads(bienes_json)
                print(f"DEBUG: Bienes parseados: {bienes_data}")
                for item in bienes_data:
                    activo = Activo.objects.get(pk=item['activo_id'])
                    detalle = DetalleOrdenCompra.objects.create(
                        orden_compra=self.object,
                        activo=activo,
                        cantidad=item['cantidad'],
                        precio_unitario=Decimal(str(item.get('precio_unitario', 0))),
                        descuento=Decimal(str(item.get('descuento', 0)))
                    )
                    print(f"DEBUG: Creado detalle bien ID {detalle.id} para orden {self.object.numero}")
            except (json.JSONDecodeError, Activo.DoesNotExist, KeyError, ValueError) as e:
                # Log error but continue
                print(f"ERROR procesando bienes: {e}")
                import traceback
                traceback.print_exc()

        # Recalcular totales de la orden (solo si hubo artículos/bienes)
        if articulos_json or bienes_json:
            orden_service = OrdenCompraService()
            orden_service.recalcular_totales(self.object)

        self.log_action(self.object, self.request)
        return response


class OrdenCompraUpdateView(BaseAuditedViewMixin, UpdateView):
    """
    Vista para editar una orden de compra existente.

    Permisos: compras.change_ordencompra
    Auditoría: Registra acción EDITAR automáticamente
    """
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'compras/orden/form.html'
    permission_required = 'compras.change_ordencompra'

    # Configuración de auditoría
    audit_action = 'EDITAR'
    audit_description_template = 'Editó orden de compra {obj.numero}'

    # Mensaje de éxito
    success_message = 'Orden de compra {obj.numero} actualizada exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la orden editada."""
        return reverse_lazy('compras:orden_compra_detalle', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Orden de Compra {self.object.numero}'
        context['action'] = 'Actualizar'
        context['orden'] = self.object
        return context

    def form_valid(self, form):
        """Procesa el formulario válido con log de auditoría."""
        response = super().form_valid(form)
        self.log_action(self.object, self.request)
        return response


class OrdenCompraDeleteView(BaseAuditedViewMixin, DeleteView):
    """
    Vista para eliminar una orden de compra (soft delete de detalles).

    Permisos: compras.delete_ordencompra
    Auditoría: Registra acción ELIMINAR automáticamente
    """
    model = OrdenCompra
    template_name = 'compras/orden/eliminar.html'
    permission_required = 'compras.delete_ordencompra'
    success_url = reverse_lazy('compras:orden_compra_lista')

    # Configuración de auditoría
    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó orden de compra {obj.numero}'

    # Mensaje de éxito
    success_message = 'Orden de compra {obj.numero} eliminada exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Orden de Compra {self.object.numero}'
        context['orden'] = self.object
        # Verificar si puede eliminar
        context['es_final'] = self.object.estado.es_final if self.object.estado else False
        return context

    def delete(self, request, *args, **kwargs):
        """Sobrescribe delete para hacer soft delete de detalles."""
        self.object = self.get_object()

        # Verificar que se pueda eliminar
        if self.object.estado and self.object.estado.es_final:
            messages.error(request, 'No se puede eliminar una orden en estado final.')
            return redirect('compras:orden_compra_lista')

        # Soft delete de los detalles
        self.object.detalles_articulos.update(eliminado=True, activo=False)
        self.object.detalles.update(eliminado=True, activo=False)

        # Log de auditoría
        if hasattr(self, 'log_action'):
            self.log_action(self.object, request)

        messages.success(request, self.get_success_message(self.object))
        return redirect(self.success_url)


class ObtenerDetallesSolicitudesView(View):
    """
    Vista AJAX para obtener los detalles de solicitudes seleccionadas.
    Retorna JSON con los artículos/activos de las solicitudes.
    """

    def get(self, request, *args, **kwargs):
        """Retorna los detalles de las solicitudes en formato JSON."""
        from django.http import JsonResponse
        from apps.solicitudes.models import Solicitud

        solicitud_ids = request.GET.getlist('solicitudes[]')

        if not solicitud_ids:
            return JsonResponse({'detalles': []})

        detalles_data = []

        for solicitud_id in solicitud_ids:
            try:
                solicitud = Solicitud.objects.get(id=solicitud_id, eliminado=False)
                # Obtener detalles con cantidad aprobada o solicitada > 0
                detalles = solicitud.detalles.filter(eliminado=False)

                for detalle in detalles:
                    # Usar cantidad aprobada si existe, sino usar cantidad solicitada
                    cantidad = detalle.cantidad_aprobada if detalle.cantidad_aprobada > 0 else detalle.cantidad_solicitada

                    detalle_info = {
                        'solicitud_id': solicitud.id,
                        'solicitud_numero': solicitud.numero,
                        'tipo': 'articulo' if detalle.articulo else 'activo',
                        'codigo': detalle.producto_codigo,
                        'nombre': detalle.producto_nombre,
                        'cantidad_aprobada': str(cantidad),
                    }

                    if detalle.articulo:
                        # Obtener unidad de medida del artículo
                        detalle_info['articulo_id'] = detalle.articulo.id
                        detalle_info['unidad_medida'] = detalle.articulo.unidad_medida.simbolo if detalle.articulo.unidad_medida else 'unidad'
                        detalle_info['precio_unitario'] = '0'
                        detalle_info['categoria'] = detalle.articulo.categoria.nombre if detalle.articulo.categoria else 'Sin categoría'
                    else:
                        # Los activos son bienes únicos sin unidad de medida
                        detalle_info['activo_id'] = detalle.activo.id
                        detalle_info['unidad_medida'] = 'unidad'
                        detalle_info['precio_unitario'] = '0'
                        detalle_info['categoria'] = detalle.activo.categoria.nombre if detalle.activo.categoria else 'Sin categoría'

                    detalles_data.append(detalle_info)

            except Solicitud.DoesNotExist:
                continue

        return JsonResponse({'detalles': detalles_data})


class ObtenerArticulosOrdenCompraView(View):
    """
    Vista AJAX para obtener los artículos de una orden de compra.
    Retorna JSON con los artículos de la orden seleccionada.
    """

    def get(self, request, *args, **kwargs):
        """Retorna los artículos de la orden de compra en formato JSON."""
        from django.http import JsonResponse

        orden_id = request.GET.get('orden_id')

        if not orden_id:
            return JsonResponse({'articulos': []})

        try:
            orden = OrdenCompra.objects.get(id=orden_id)
            articulos_data = []

            # Obtener artículos de bodega
            detalles_articulos = orden.detalles_articulos.all().select_related('articulo', 'articulo__unidad_medida')
            for detalle in detalles_articulos:
                # Obtener unidad de medida (ForeignKey, no ManyToMany)
                unidad_medida = detalle.articulo.unidad_medida.simbolo if detalle.articulo.unidad_medida else 'unidad'

                articulos_data.append({
                    'id': detalle.articulo.id,
                    'sku': detalle.articulo.codigo,
                    'codigo': detalle.articulo.codigo,
                    'nombre': detalle.articulo.nombre,
                    'cantidad': str(detalle.cantidad),
                    'unidad_medida': unidad_medida,
                    'tipo': 'articulo'
                })

            # Obtener activos (los activos no tienen unidad_medida, son bienes únicos)
            detalles_activos = orden.detalles.all().select_related('activo')
            for detalle in detalles_activos:
                articulos_data.append({
                    'id': detalle.activo.id,
                    'sku': detalle.activo.codigo,
                    'codigo': detalle.activo.codigo,
                    'nombre': detalle.activo.nombre,
                    'cantidad': str(detalle.cantidad),
                    'unidad_medida': 'unidad',  # Activos son bienes únicos sin unidad de medida
                    'tipo': 'activo'
                })

            return JsonResponse({'articulos': articulos_data})

        except OrdenCompra.DoesNotExist:
            return JsonResponse({'articulos': [], 'error': 'Orden de compra no encontrada'}, status=404)


class ObtenerActivosOrdenCompraView(View):
    """
    Vista AJAX para obtener los activos de una orden de compra.
    Retorna JSON con los activos de la orden seleccionada.
    """

    def get(self, request, *args, **kwargs):
        """Retorna los activos de la orden de compra en formato JSON."""
        from django.http import JsonResponse

        orden_id = request.GET.get('orden_id')

        if not orden_id:
            return JsonResponse({'activos': []})

        try:
            orden = OrdenCompra.objects.get(id=orden_id)
            activos_data = []

            # Obtener solo activos (no artículos)
            detalles_activos = orden.detalles.filter(eliminado=False).select_related('activo', 'activo__categoria')
            for detalle in detalles_activos:
                activos_data.append({
                    'id': detalle.activo.id,
                    'codigo': detalle.activo.codigo,
                    'nombre': detalle.activo.nombre,
                    'cantidad': str(detalle.cantidad),
                    'requiere_serie': detalle.activo.requiere_serie,
                    'categoria': detalle.activo.categoria.nombre if detalle.activo.categoria else ''
                })

            return JsonResponse({'activos': activos_data})

        except OrdenCompra.DoesNotExist:
            return JsonResponse({'activos': [], 'error': 'Orden de compra no encontrada'}, status=404)


class OrdenCompraAgregarArticuloView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para agregar un artículo a una orden de compra.

    Permisos: compras.add_detalleordencompraarticulo
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza que se actualicen los totales correctamente
    Utiliza: OrdenCompraService para recalcular totales
    """
    model = DetalleOrdenCompraArticulo
    form_class = DetalleOrdenCompraArticuloForm
    template_name = 'compras/orden/agregar_articulo.html'
    permission_required = 'compras.add_detalleordencompraarticulo'

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Artículo agregado exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la orden."""
        return reverse_lazy('compras:orden_compra_detalle', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        orden_repo = OrdenCompraRepository()
        orden = orden_repo.get_by_id(self.kwargs['pk'])
        context['orden'] = orden
        context['titulo'] = 'Agregar Artículo'
        context['action'] = 'Agregar'
        return context

    def form_valid(self, form):
        """Procesa el formulario y actualiza totales usando service."""
        orden_repo = OrdenCompraRepository()
        orden = orden_repo.get_by_id(self.kwargs['pk'])
        form.instance.orden_compra = orden
        response = super().form_valid(form)

        # Recalcular totales usando service
        orden_service = OrdenCompraService()
        orden_service.recalcular_totales(orden)

        # Log de auditoría
        self.audit_description_template = f'Agregó artículo {self.object.articulo.codigo} a orden {orden.numero}'
        self.log_action(self.object, self.request)

        return response


class OrdenCompraAgregarActivoView(BaseAuditedViewMixin, AtomicTransactionMixin, CreateView):
    """
    Vista para agregar un activo/bien a una orden de compra.

    Permisos: compras.add_detalleordencompra
    Auditoría: Registra acción CREAR automáticamente
    Transacción atómica: Garantiza que se actualicen los totales correctamente
    Utiliza: OrdenCompraService para recalcular totales
    """
    model = DetalleOrdenCompra
    form_class = DetalleOrdenCompraActivoForm
    template_name = 'compras/orden/agregar_activo.html'
    permission_required = 'compras.add_detalleordencompra'

    # Configuración de auditoría
    audit_action = 'CREAR'
    success_message = 'Activo agregado exitosamente.'

    def get_success_url(self) -> str:
        """Redirige al detalle de la orden."""
        return reverse_lazy('compras:orden_compra_detalle', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs) -> dict:
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        orden_repo = OrdenCompraRepository()
        orden = orden_repo.get_by_id(self.kwargs['pk'])
        context['orden'] = orden
        context['titulo'] = 'Agregar Activo/Bien'
        context['action'] = 'Agregar'
        return context

    def form_valid(self, form):
        """Procesa el formulario y actualiza totales usando service."""
        orden_repo = OrdenCompraRepository()
        orden = orden_repo.get_by_id(self.kwargs['pk'])
        form.instance.orden_compra = orden
        response = super().form_valid(form)

        # Recalcular totales usando service
        orden_service = OrdenCompraService()
        orden_service.recalcular_totales(orden)

        # Log de auditoría
        self.audit_description_template = f'Agregó activo {self.object.activo.codigo} a orden {orden.numero}'
        self.log_action(self.object, self.request)

        return response


# ==================== VISTAS MANTENEDORES: ESTADO ORDEN COMPRA ====================


class EstadoOrdenCompraListView(BaseAuditedViewMixin, PaginatedListMixin, ListView):
    """Vista para listar estados de orden de compra."""
    model = EstadoOrdenCompra
    template_name = 'compras/mantenedores/estado_orden_compra/lista.html'
    context_object_name = 'estados'
    permission_required = 'compras.view_estadoordencompra'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        queryset = EstadoOrdenCompra.objects.filter(eliminado=False).order_by('codigo')

        query = self.request.GET.get('q', '').strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Estados de Orden de Compra'
        context['puede_crear'] = self.request.user.has_perm('compras.add_estadoordencompra')
        context['query'] = self.request.GET.get('q', '')
        return context


class EstadoOrdenCompraCreateView(BaseAuditedViewMixin, CreateView):
    """Vista para crear un nuevo estado de orden de compra."""
    model = EstadoOrdenCompra
    form_class = EstadoOrdenCompraForm
    template_name = 'compras/mantenedores/estado_orden_compra/form.html'
    permission_required = 'compras.add_estadoordencompra'
    success_url = reverse_lazy('compras:estado_orden_compra_lista')

    audit_action = 'CREAR'
    audit_description_template = 'Creó estado de orden de compra {obj.codigo} - {obj.nombre}'
    success_message = 'Estado de orden de compra {obj.nombre} creado exitosamente.'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Estado de Orden de Compra'
        context['action'] = 'Crear'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class EstadoOrdenCompraUpdateView(BaseAuditedViewMixin, UpdateView):
    """Vista para editar un estado de orden de compra."""
    model = EstadoOrdenCompra
    form_class = EstadoOrdenCompraForm
    template_name = 'compras/mantenedores/estado_orden_compra/form.html'
    permission_required = 'compras.change_estadoordencompra'
    success_url = reverse_lazy('compras:estado_orden_compra_lista')

    audit_action = 'EDITAR'
    audit_description_template = 'Editó estado de orden de compra {obj.codigo} - {obj.nombre}'
    success_message = 'Estado de orden de compra {obj.nombre} actualizado exitosamente.'

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Estado: {self.object.nombre}'
        context['action'] = 'Actualizar'
        context['estado'] = self.object
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message(self.object))
        self.log_action(self.object, self.request)
        return response


class EstadoOrdenCompraDeleteView(BaseAuditedViewMixin, DeleteView):
    """Vista para eliminar (soft delete) un estado de orden de compra."""
    model = EstadoOrdenCompra
    template_name = 'compras/mantenedores/estado_orden_compra/eliminar.html'
    permission_required = 'compras.delete_estadoordencompra'
    success_url = reverse_lazy('compras:estado_orden_compra_lista')

    audit_action = 'ELIMINAR'
    audit_description_template = 'Eliminó estado de orden de compra {obj.codigo} - {obj.nombre}'
    success_message = 'Estado de orden de compra {obj.nombre} eliminado exitosamente.'

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(eliminado=False)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Estado: {self.object.nombre}'
        context['estado'] = self.object

        # Verificar órdenes de compra asociadas
        context['tiene_ordenes'] = self.object.ordenes_compra.filter(eliminado=False).exists()
        context['count_ordenes'] = self.object.ordenes_compra.filter(eliminado=False).count()

        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.ordenes_compra.filter(eliminado=False).exists():
            messages.error(
                request,
                f'No se puede eliminar el estado "{self.object.nombre}" porque tiene órdenes de compra asociadas. '
                'Desactívelo en su lugar.'
            )
            return redirect('compras:estado_orden_compra_lista')

        self.object.eliminado = True
        self.object.activo = False
        self.object.save()

        messages.success(request, self.get_success_message(self.object))
        self.log_action(self.object, request)

        return redirect(self.success_url)


# ==================== IMPORTACION EXCEL PARA MANTENEDORES ====================

from apps.bodega.excel_services.importacion_excel import ImportacionExcelService
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required



@login_required
def estado_orden_compra_descargar_plantilla(request):
    """Vista para descargar plantilla Excel de estados de orden de compra."""
    contenido = ImportacionExcelService.generar_plantilla_estados_orden_compra()
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_estados_orden_compra.xlsx"'
    return response


@login_required
def estado_orden_compra_importar_excel(request):
    """Vista para importar estados de orden de compra desde Excel."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporciono archivo'}, status=400)
    archivo = request.FILES['archivo']
    es_valido, mensaje_error = ImportacionExcelService.validar_archivo_excel(archivo)
    if not es_valido:
        return JsonResponse({'error': mensaje_error}, status=400)
    try:
        creadas, actualizadas, errores = ImportacionExcelService.importar_estados_orden_compra(archivo, request.user)
        mensaje = f"Importacion completada: {creadas} estados creados, {actualizadas} actualizados"
        if errores:
            mensaje += f". Errores: {len(errores)}"
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'creadas': creadas,
            'actualizadas': actualizadas,
            'errores': errores[:10]
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al importar: {str(e)}'}, status=500)