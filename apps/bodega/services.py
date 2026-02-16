"""
Service Layer para el módulo de bodega.

Contiene la lógica de negocio y coordina los repositories,
siguiendo el principio de Single Responsibility (SOLID).
"""
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Categoria, Articulo, TipoMovimiento, Movimiento, Bodega,
    EstadoEntrega, TipoEntrega, EntregaArticulo, DetalleEntregaArticulo,
    EntregaBien, DetalleEntregaBien,
    EstadoRecepcion, RecepcionArticulo, DetalleRecepcionArticulo,
    RecepcionActivo, DetalleRecepcionActivo
)
from .repositories import (
    CategoriaRepository,
    ArticuloRepository,
    TipoMovimientoRepository,
    MovimientoRepository,
    OperacionRepository,
    BodegaRepository,
    EstadoEntregaRepository,
    TipoEntregaRepository,
    EntregaArticuloRepository,
    DetalleEntregaArticuloRepository,
    EntregaBienRepository,
    DetalleEntregaBienRepository,
    EstadoRecepcionRepository,
    RecepcionArticuloRepository,
    DetalleRecepcionArticuloRepository,
    RecepcionActivoRepository,
    DetalleRecepcionActivoRepository
)
from core.utils import generar_codigo_unico
from apps.compras.models import OrdenCompra
from apps.activos.models import Activo
from apps.activos.repositories import ActivoRepository


# ==================== CATEGORÍA SERVICE ====================

class CategoriaService:
    """
    Service para lógica de negocio de Categoría.

    Coordina operaciones complejas y validaciones de negocio.
    """

    def __init__(self):
        self.repository = CategoriaRepository()

    def crear_categoria(
        self,
        codigo: str,
        nombre: str,
        descripcion: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> Categoria:
        """
        Crea una nueva categoría validando que no exista el código.

        Args:
            codigo: Código único de la categoría
            nombre: Nombre de la categoría
            descripcion: Descripción opcional
            observaciones: Observaciones opcionales

        Returns:
            Categoría creada

        Raises:
            ValidationError: Si el código ya existe
        """
        # Validar unicidad del código
        if self.repository.exists_by_codigo(codigo):
            raise ValidationError(
                f'Ya existe una categoría con el código "{codigo}".'
            )

        # Crear categoría
        categoria = Categoria.objects.create(
            codigo=codigo.strip().upper(),
            nombre=nombre.strip(),
            descripcion=descripcion,
            observaciones=observaciones
        )

        return categoria

    def actualizar_categoria(
        self,
        categoria: Categoria,
        codigo: Optional[str] = None,
        nombre: Optional[str] = None,
        descripcion: Optional[str] = None,
        observaciones: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> Categoria:
        """
        Actualiza una categoría existente.

        Args:
            categoria: Categoría a actualizar
            codigo: Nuevo código (opcional)
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            observaciones: Nuevas observaciones (opcional)
            activo: Nuevo estado activo (opcional)

        Returns:
            Categoría actualizada

        Raises:
            ValidationError: Si el nuevo código ya existe
        """
        # Validar código si se está actualizando
        if codigo and codigo != categoria.codigo:
            if self.repository.exists_by_codigo(codigo, exclude_id=categoria.id):
                raise ValidationError(
                    f'Ya existe una categoría con el código "{codigo}".'
                )
            categoria.codigo = codigo.strip().upper()

        # Actualizar campos
        if nombre:
            categoria.nombre = nombre.strip()
        if descripcion is not None:
            categoria.descripcion = descripcion
        if observaciones is not None:
            categoria.observaciones = observaciones
        if activo is not None:
            categoria.activo = activo

        categoria.save()
        return categoria

    def eliminar_categoria(self, categoria: Categoria) -> Tuple[bool, str]:
        """
        Elimina lógicamente una categoría (soft delete).

        Valida que no tenga artículos asociados activos.

        Args:
            categoria: Categoría a eliminar

        Returns:
            Tupla (éxito, mensaje)
        """
        # Verificar si tiene artículos activos
        articulos_activos = ArticuloRepository.filter_by_categoria(categoria).filter(
            activo=True
        )

        if articulos_activos.exists():
            count = articulos_activos.count()
            return (
                False,
                f'No se puede eliminar la categoría porque tiene {count} '
                f'artículo(s) activo(s) asociado(s).'
            )

        # Soft delete
        categoria.eliminado = True
        categoria.activo = False
        categoria.save()

        return (True, f'Categoría "{categoria.nombre}" eliminada exitosamente.')


# ==================== ARTÍCULO SERVICE ====================

class ArticuloService:
    """
    Service para lógica de negocio de Artículo.

    Coordina operaciones complejas y validaciones de negocio.
    """

    def __init__(self):
        self.repository = ArticuloRepository()

    def crear_articulo(
        self,
        codigo: str,
        nombre: str,
        categoria: Categoria,
        ubicacion_fisica: Bodega,
        unidad_medida: str,
        stock_minimo: Decimal = Decimal('0'),
        stock_maximo: Optional[Decimal] = None,
        punto_reorden: Optional[Decimal] = None,
        descripcion: Optional[str] = None,
        marca: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> Articulo:
        """
        Crea un nuevo artículo validando que no exista el código.

        Args:
            codigo: Código único del artículo
            nombre: Nombre del artículo
            categoria: Categoría del artículo
            ubicacion_fisica: Bodega donde se almacena
            unidad_medida: Unidad de medida
            stock_minimo: Stock mínimo permitido
            stock_maximo: Stock máximo permitido (opcional)
            punto_reorden: Punto de reorden (opcional)
            descripcion: Descripción (opcional)
            marca: Marca (opcional)
            observaciones: Observaciones (opcional)

        Returns:
            Artículo creado

        Raises:
            ValidationError: Si el código ya existe o hay errores de validación
        """
        # Validar unicidad del código
        if self.repository.exists_by_codigo(codigo):
            raise ValidationError(
                f'Ya existe un artículo con el código "{codigo}".'
            )

        # Validar stock_maximo > stock_minimo
        if stock_maximo and stock_maximo < stock_minimo:
            raise ValidationError(
                'El stock máximo no puede ser menor que el stock mínimo.'
            )

        # Validar punto_reorden >= stock_minimo
        if punto_reorden and punto_reorden < stock_minimo:
            raise ValidationError(
                'El punto de reorden no puede ser menor que el stock mínimo.'
            )

        # Crear artículo
        articulo = Articulo.objects.create(
            codigo=codigo.strip().upper(),
            nombre=nombre.strip(),
            categoria=categoria,
            ubicacion_fisica=ubicacion_fisica,
            unidad_medida=unidad_medida.strip(),
            stock_minimo=stock_minimo,
            stock_maximo=stock_maximo,
            punto_reorden=punto_reorden,
            descripcion=descripcion,
            marca=marca,
            observaciones=observaciones
        )

        return articulo

    def actualizar_articulo(
        self,
        articulo: Articulo,
        datos: Dict[str, Any]
    ) -> Articulo:
        """
        Actualiza un artículo existente.

        Args:
            articulo: Artículo a actualizar
            datos: Diccionario con los datos a actualizar

        Returns:
            Artículo actualizado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar código si se está actualizando
        if 'codigo' in datos and datos['codigo'] != articulo.codigo:
            if self.repository.exists_by_codigo(datos['codigo'], exclude_id=articulo.id):
                raise ValidationError(
                    f'Ya existe un artículo con el código "{datos["codigo"]}".'
                )

        # Validar stocks
        stock_min = datos.get('stock_minimo', articulo.stock_minimo)
        stock_max = datos.get('stock_maximo', articulo.stock_maximo)
        punto_reorden = datos.get('punto_reorden', articulo.punto_reorden)

        if stock_max and stock_max < stock_min:
            raise ValidationError(
                'El stock máximo no puede ser menor que el stock mínimo.'
            )

        if punto_reorden and punto_reorden < stock_min:
            raise ValidationError(
                'El punto de reorden no puede ser menor que el stock mínimo.'
            )

        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(articulo, campo):
                if campo in ['codigo', 'nombre', 'unidad_medida'] and isinstance(valor, str):
                    valor = valor.strip().upper() if campo == 'codigo' else valor.strip()
                setattr(articulo, campo, valor)

        articulo.save()
        return articulo

    def obtener_articulos_bajo_stock(self) -> list[Articulo]:
        """
        Retorna lista de artículos con stock bajo el mínimo.

        Returns:
            Lista de artículos con stock crítico
        """
        return list(self.repository.get_low_stock())

    def obtener_articulos_punto_reorden(self) -> list[Articulo]:
        """
        Retorna lista de artículos que alcanzaron el punto de reorden.

        Returns:
            Lista de artículos que requieren reorden
        """
        return list(self.repository.get_reorder_point())


# ==================== MOVIMIENTO SERVICE ====================

class MovimientoService:
    """
    Service para lógica de negocio de Movimiento.

    Coordina operaciones complejas de movimientos de inventario
    con actualización atómica de stock.
    """

    def __init__(self):
        self.movimiento_repo = MovimientoRepository()
        self.articulo_repo = ArticuloRepository()
        self.tipo_repo = TipoMovimientoRepository()

    @transaction.atomic
    def registrar_entrada(
        self,
        articulo: Articulo,
        tipo: TipoMovimiento,
        cantidad: Decimal,
        usuario: User,
        motivo: str
    ) -> Movimiento:
        """
        Registra una entrada de inventario (aumenta stock).

        Esta operación es atómica: todo o nada.

        Args:
            articulo: Artículo a mover
            tipo: Tipo de movimiento
            cantidad: Cantidad a ingresar
            usuario: Usuario que realiza la operación
            motivo: Motivo del movimiento

        Returns:
            Movimiento creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar cantidad
        if cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')

        # Calcular nuevo stock
        stock_anterior = articulo.stock_actual
        stock_nuevo = stock_anterior + cantidad

        # Validar stock máximo si está definido
        if articulo.stock_maximo and stock_nuevo > articulo.stock_maximo:
            raise ValidationError(
                f'La cantidad excede el stock máximo permitido '
                f'({articulo.stock_maximo}). Stock actual: {stock_anterior}, '
                f'intentando agregar: {cantidad}.'
            )

        # Obtener operación de entrada
        operacion_entrada = self.operacion_repo.get_entrada()
        if not operacion_entrada:
            raise ValidationError('No se encontró una operación de tipo ENTRADA activa.')

        # Crear movimiento
        movimiento = self.movimiento_repo.create(
            articulo=articulo,
            tipo=tipo,
            cantidad=cantidad,
            operacion=operacion_entrada,
            usuario=usuario,
            motivo=motivo,
            stock_antes=stock_anterior,
            stock_despues=stock_nuevo
        )

        # Actualizar stock del artículo
        self.articulo_repo.update_stock(articulo, stock_nuevo)

        return movimiento

    @transaction.atomic
    def registrar_salida(
        self,
        articulo: Articulo,
        tipo: TipoMovimiento,
        cantidad: Decimal,
        usuario: User,
        motivo: str
    ) -> Movimiento:
        """
        Registra una salida de inventario (disminuye stock).

        Esta operación es atómica: todo o nada.

        Args:
            articulo: Artículo a mover
            tipo: Tipo de movimiento
            cantidad: Cantidad a sacar
            usuario: Usuario que realiza la operación
            motivo: Motivo del movimiento

        Returns:
            Movimiento creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar cantidad
        if cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')

        # Calcular nuevo stock
        stock_anterior = articulo.stock_actual
        stock_nuevo = stock_anterior - cantidad

        # Validar que no quede en negativo
        if stock_nuevo < 0:
            raise ValidationError(
                f'Stock insuficiente. Stock actual: {stock_anterior}, '
                f'intentando sacar: {cantidad}.'
            )

        # Obtener operación de salida
        operacion_salida = self.operacion_repo.get_salida()
        if not operacion_salida:
            raise ValidationError('No se encontró una operación de tipo SALIDA activa.')

        # Crear movimiento
        movimiento = self.movimiento_repo.create(
            articulo=articulo,
            tipo=tipo,
            cantidad=cantidad,
            operacion=operacion_salida,
            usuario=usuario,
            motivo=motivo,
            stock_antes=stock_anterior,
            stock_despues=stock_nuevo
        )

        # Actualizar stock del artículo
        self.articulo_repo.update_stock(articulo, stock_nuevo)

        return movimiento

    @transaction.atomic
    def registrar_movimiento(
        self,
        articulo: Articulo,
        tipo: TipoMovimiento,
        cantidad: Decimal,
        operacion: str,
        usuario: User,
        motivo: str
    ) -> Movimiento:
        """
        Registra un movimiento (entrada o salida) según la operación.

        Esta operación es atómica: todo o nada.

        Args:
            articulo: Artículo a mover
            tipo: Tipo de movimiento
            cantidad: Cantidad a mover
            operacion: 'ENTRADA' o 'SALIDA'
            usuario: Usuario que realiza la operación
            motivo: Motivo del movimiento

        Returns:
            Movimiento creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        if operacion == 'ENTRADA':
            return self.registrar_entrada(articulo, tipo, cantidad, usuario, motivo)
        elif operacion == 'SALIDA':
            return self.registrar_salida(articulo, tipo, cantidad, usuario, motivo)
        else:
            raise ValidationError(
                f'Operación inválida: "{operacion}". '
                f'Debe ser "ENTRADA" o "SALIDA".'
            )

    def obtener_historial_articulo(
        self,
        articulo: Articulo,
        limit: int = 20
    ) -> list[Movimiento]:
        """
        Obtiene el historial de movimientos de un artículo.

        Args:
            articulo: Artículo del cual obtener el historial
            limit: Número máximo de movimientos a retornar

        Returns:
            Lista de movimientos ordenados por fecha descendente
        """
        return list(self.movimiento_repo.filter_by_articulo(articulo, limit))


# ==================== ENTREGA SERVICE ====================

class EntregaArticuloService:
    """
    Service para lógica de negocio de EntregaArticulo.

    Coordina operaciones complejas de entregas de artículos
    con actualización atómica de stock y validaciones.
    """

    def __init__(self):
        self.entrega_repo = EntregaArticuloRepository()
        self.articulo_repo = ArticuloRepository()
        self.estado_repo = EstadoEntregaRepository()
        self.tipo_repo = TipoEntregaRepository()
        self.movimiento_repo = MovimientoRepository()
        self.operacion_repo = OperacionRepository()

    def generar_numero_entrega(self) -> str:
        """
        Genera un número único para la entrega.

        Returns:
            Número de entrega en formato ENT-ART-YYYYMMDD-XXX
        """
        from django.utils import timezone
        fecha_actual = timezone.now()
        prefijo = f"ENT-ART-{fecha_actual.strftime('%Y%m%d')}"

        # Buscar el último número del día
        ultimas_entregas = EntregaArticulo.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero')[:1]

        if ultimas_entregas.exists():
            ultimo_numero = ultimas_entregas[0].numero
            secuencia = int(ultimo_numero.split('-')[-1]) + 1
        else:
            secuencia = 1

        return f"{prefijo}-{secuencia:03d}"

    @transaction.atomic
    def crear_entrega(
        self,
        bodega_origen: Bodega,
        tipo: TipoEntrega,
        entregado_por: User,
        recibido_por: User,
        motivo: str,
        detalles: list[Dict[str, Any]],
        departamento_destino = None,
        observaciones: Optional[str] = None,
        solicitud = None
    ) -> EntregaArticulo:
        """
        Crea una nueva entrega de artículos con sus detalles.

        Esta operación es atómica: todo o nada.

        Args:
            bodega_origen: Bodega de donde salen los artículos
            tipo: Tipo de entrega
            entregado_por: Usuario que entrega
            recibido_por: Usuario que recibe
            motivo: Motivo de la entrega
            detalles: Lista de dicts con 'articulo_id', 'cantidad', 'lote' (opcional),
                     'observaciones' (opcional), 'detalle_solicitud_id' (opcional)
            departamento_destino: Departamento destino (opcional)
            observaciones: Observaciones generales (opcional)
            solicitud: Solicitud asociada (opcional)

        Returns:
            EntregaArticulo creada con sus detalles

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar que haya detalles
        if not detalles or len(detalles) == 0:
            raise ValidationError('Debe agregar al menos un artículo a la entrega.')

        # Obtener estado inicial (temporal, se actualizará después)
        estado_inicial = self.estado_repo.get_inicial()
        if not estado_inicial:
            raise ValidationError(
                'No se encontró un estado inicial para las entregas. '
                'Configure los estados en el sistema.'
            )

        # Generar número de entrega
        numero = self.generar_numero_entrega()

        # Crear entrega con estado inicial temporal
        entrega = EntregaArticulo.objects.create(
            numero=numero,
            bodega_origen=bodega_origen,
            tipo=tipo,
            estado=estado_inicial,
            entregado_por=entregado_por,
            recibido_por=recibido_por,
            departamento_destino=departamento_destino,
            motivo=motivo,
            observaciones=observaciones,
            solicitud=solicitud
        )

        # Procesar detalles y actualizar stock
        for detalle_data in detalles:
            articulo_id = detalle_data.get('articulo_id')
            cantidad = Decimal(str(detalle_data.get('cantidad', 0)))
            lote = detalle_data.get('lote')
            obs_detalle = detalle_data.get('observaciones')
            detalle_solicitud_id = detalle_data.get('detalle_solicitud_id')

            # Obtener artículo
            articulo = self.articulo_repo.get_by_id(articulo_id)
            if not articulo:
                raise ValidationError(f'No se encontró el artículo con ID {articulo_id}.')

            # Si hay detalle de solicitud, validar cantidad pendiente
            detalle_solicitud = None
            if detalle_solicitud_id:
                from apps.solicitudes.models import DetalleSolicitud
                try:
                    detalle_solicitud = DetalleSolicitud.objects.get(
                        id=detalle_solicitud_id,
                        eliminado=False
                    )

                    # Validar que la cantidad no exceda la pendiente
                    cantidad_pendiente = detalle_solicitud.cantidad_aprobada - detalle_solicitud.cantidad_despachada
                    if cantidad > cantidad_pendiente:
                        raise ValidationError(
                            f'La cantidad a entregar ({cantidad}) excede la cantidad pendiente '
                            f'({cantidad_pendiente}) del artículo {articulo.codigo} en la solicitud.'
                        )
                except DetalleSolicitud.DoesNotExist:
                    raise ValidationError(
                        f'No se encontró el detalle de solicitud con ID {detalle_solicitud_id}.'
                    )

            # Validar stock disponible
            if articulo.stock_actual < cantidad:
                raise ValidationError(
                    f'Stock insuficiente del artículo {articulo.codigo}. '
                    f'Disponible: {articulo.stock_actual}, Solicitado: {cantidad}'
                )

            # Crear detalle de entrega
            DetalleEntregaArticulo.objects.create(
                entrega=entrega,
                articulo=articulo,
                cantidad=cantidad,
                lote=lote,
                observaciones=obs_detalle,
                detalle_solicitud=detalle_solicitud
            )

            # Actualizar stock (restar)
            stock_anterior = articulo.stock_actual
            stock_nuevo = stock_anterior - cantidad
            self.articulo_repo.update_stock(articulo, stock_nuevo)

            # Si hay detalle de solicitud, actualizar cantidad despachada
            if detalle_solicitud:
                detalle_solicitud.cantidad_despachada += cantidad
                detalle_solicitud.save()

            # Registrar movimiento de salida
            tipo_mov_entrega = TipoMovimiento.objects.filter(
                codigo='ENTREGA'
            ).first()

            if not tipo_mov_entrega:
                # Si no existe, usar un tipo genérico de salida
                tipo_mov_entrega = TipoMovimiento.objects.filter(
                    activo=True, eliminado=False
                ).first()

            if tipo_mov_entrega:
                # Obtener operación de salida
                operacion_salida = self.operacion_repo.get_salida()
                if operacion_salida:
                    self.movimiento_repo.create(
                        articulo=articulo,
                        tipo=tipo_mov_entrega,
                        cantidad=cantidad,
                        operacion=operacion_salida,
                        usuario=entregado_por,
                        motivo=f'Entrega {numero} - {motivo}',
                        stock_antes=stock_anterior,
                        stock_despues=stock_nuevo
                    )

        # Determinar y actualizar el estado correcto de la entrega
        estado_correcto = self._determinar_estado_entrega(entrega, solicitud)
        if estado_correcto:
            entrega.estado = estado_correcto
            entrega.save()

        # Si hay solicitud asociada, verificar si está completamente despachada
        if solicitud:
            self._verificar_y_actualizar_estado_solicitud(solicitud)

        return entrega

    def _determinar_estado_entrega(self, entrega, solicitud):
        """
        Determina el estado correcto de la entrega según la lógica de negocio:
        - Sin solicitud → DESPACHADO
        - Con solicitud y entrega completa → DESPACHADO
        - Con solicitud y entrega parcial → DESPACHO_PARCIAL

        Args:
            entrega: Entrega de artículos creada
            solicitud: Solicitud asociada (opcional)

        Returns:
            EstadoEntrega correcto o None si no se puede determinar
        """
        # Si no hay solicitud asociada → DESPACHADO
        if not solicitud:
            estado_despachado = self.estado_repo.get_despachado()
            if not estado_despachado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHADO'")
            return estado_despachado

        # Si hay solicitud, verificar si la entrega es completa o parcial
        from apps.solicitudes.models import DetalleSolicitud

        detalles_solicitud = solicitud.detalles.filter(
            eliminado=False,
            articulo__isnull=False  # Solo artículos
        )

        # Verificar si todos los artículos están completamente despachados
        todos_completos = True
        alguno_parcial = False

        for detalle_sol in detalles_solicitud:
            cantidad_pendiente = detalle_sol.cantidad_aprobada - detalle_sol.cantidad_despachada

            if cantidad_pendiente > 0:
                todos_completos = False

            if detalle_sol.cantidad_despachada > 0 and cantidad_pendiente > 0:
                alguno_parcial = True

        # Determinar estado según las cantidades
        if todos_completos:
            # Todos los artículos fueron despachados completamente → DESPACHADO
            estado = self.estado_repo.get_despachado()
            if not estado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHADO'")
            return estado
        else:
            # Hay artículos con despacho parcial → DESPACHO_PARCIAL
            estado = self.estado_repo.get_despacho_parcial()
            if not estado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHO_PARCIAL'")
            return estado

    def _verificar_y_actualizar_estado_solicitud(self, solicitud):
        """
        Verifica si todos los artículos de una solicitud están completamente despachados
        y actualiza el estado si corresponde.

        Args:
            solicitud: Solicitud a verificar
        """
        from apps.solicitudes.models import EstadoSolicitud

        # Verificar si todos los detalles están completamente despachados
        detalles = solicitud.detalles.filter(eliminado=False)
        todos_despachados = all(
            detalle.cantidad_despachada >= detalle.cantidad_aprobada
            for detalle in detalles
            if detalle.articulo  # Solo artículos
        )

        if todos_despachados:
            # Buscar estado "Completado" o similar
            estado_completado = EstadoSolicitud.objects.filter(
                es_final=True,
                activo=True,
                eliminado=False
            ).first()

            if estado_completado:
                solicitud.estado = estado_completado
                solicitud.save()


class EntregaBienService:
    """
    Service para lógica de negocio de EntregaBien.

    Coordina operaciones complejas de entregas de bienes/activos.
    """

    def __init__(self):
        self.entrega_repo = EntregaBienRepository()
        self.estado_repo = EstadoEntregaRepository()
        self.tipo_repo = TipoEntregaRepository()

    def generar_numero_entrega(self) -> str:
        """
        Genera un número único para la entrega de bien.

        Returns:
            Número de entrega en formato ENT-BIEN-YYYYMMDD-XXX
        """
        from django.utils import timezone
        fecha_actual = timezone.now()
        prefijo = f"ENT-BIEN-{fecha_actual.strftime('%Y%m%d')}"

        # Buscar el último número del día
        ultimas_entregas = EntregaBien.objects.filter(
            numero__startswith=prefijo
        ).order_by('-numero')[:1]

        if ultimas_entregas.exists():
            ultimo_numero = ultimas_entregas[0].numero
            secuencia = int(ultimo_numero.split('-')[-1]) + 1
        else:
            secuencia = 1

        return f"{prefijo}-{secuencia:03d}"

    @transaction.atomic
    def crear_entrega(
        self,
        tipo: TipoEntrega,
        entregado_por: User,
        recibido_por: User,
        motivo: str,
        detalles: list[Dict[str, Any]],
        departamento_destino = None,
        observaciones: Optional[str] = None,
        solicitud = None
    ) -> EntregaBien:
        """
        Crea una nueva entrega de bienes con sus detalles.

        Esta operación es atómica: todo o nada.

        Args:
            tipo: Tipo de entrega
            entregado_por: Usuario que entrega
            recibido_por: Usuario que recibe
            motivo: Motivo de la entrega
            detalles: Lista de dicts con 'equipo_id', 'cantidad', 'numero_serie' (opcional), 'estado_fisico' (opcional), 'observaciones' (opcional)
            departamento_destino: Departamento destino (opcional)
            observaciones: Observaciones generales (opcional)

        Returns:
            EntregaBien creada con sus detalles

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar que haya detalles
        if not detalles or len(detalles) == 0:
            raise ValidationError('Debe agregar al menos un bien a la entrega.')

        # Obtener estado inicial (temporal, se actualizará después)
        estado_inicial = self.estado_repo.get_inicial()
        if not estado_inicial:
            raise ValidationError(
                'No se encontró un estado inicial para las entregas. '
                'Configure los estados en el sistema.'
            )

        # Generar número de entrega
        numero = self.generar_numero_entrega()

        # Crear entrega con estado inicial temporal
        entrega = EntregaBien.objects.create(
            numero=numero,
            tipo=tipo,
            estado=estado_inicial,
            entregado_por=entregado_por,
            recibido_por=recibido_por,
            departamento_destino=departamento_destino,
            motivo=motivo,
            observaciones=observaciones,
            solicitud=solicitud
        )

        # Procesar detalles
        for detalle_data in detalles:
            equipo_id = detalle_data.get('equipo_id')
            cantidad = Decimal(str(detalle_data.get('cantidad', 0)))
            numero_serie = detalle_data.get('numero_serie')
            estado_fisico = detalle_data.get('estado_fisico')
            obs_detalle = detalle_data.get('observaciones')

            # Obtener activo - necesitamos importar el modelo
            from apps.activos.models import Activo
            try:
                activo = Activo.objects.get(id=equipo_id, eliminado=False)
            except Activo.DoesNotExist:
                raise ValidationError(f'No se encontró el activo/bien con ID {equipo_id}.')

            # Crear detalle de entrega
            DetalleEntregaBien.objects.create(
                entrega=entrega,
                activo=activo,
                cantidad=cantidad,
                numero_serie=numero_serie,
                estado_fisico=estado_fisico,
                observaciones=obs_detalle
            )

        # Determinar y actualizar el estado correcto de la entrega
        estado_correcto = self._determinar_estado_entrega(entrega, solicitud)
        if estado_correcto:
            entrega.estado = estado_correcto
            entrega.save()

        return entrega

    def _determinar_estado_entrega(self, entrega, solicitud):
        """
        Determina el estado correcto de la entrega según la lógica de negocio:
        - Sin solicitud → DESPACHADO
        - Con solicitud y entrega completa → DESPACHADO
        - Con solicitud y entrega parcial → DESPACHO_PARCIAL

        Args:
            entrega: Entrega de bienes creada
            solicitud: Solicitud asociada (opcional)

        Returns:
            EstadoEntrega correcto o None si no se puede determinar
        """
        # Si no hay solicitud asociada → DESPACHADO
        if not solicitud:
            estado_despachado = self.estado_repo.get_despachado()
            if not estado_despachado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHADO'")
            return estado_despachado

        # Si hay solicitud, verificar si la entrega es completa o parcial
        from apps.solicitudes.models import DetalleSolicitud

        detalles_solicitud = solicitud.detalles.filter(
            eliminado=False,
            activo__isnull=False  # Solo activos/bienes
        )

        # Verificar si todos los bienes están completamente despachados
        todos_completos = True

        for detalle_sol in detalles_solicitud:
            cantidad_pendiente = detalle_sol.cantidad_aprobada - detalle_sol.cantidad_despachada

            if cantidad_pendiente > 0:
                todos_completos = False
                break

        # Determinar estado según las cantidades
        if todos_completos:
            # Todos los bienes fueron despachados completamente → DESPACHADO
            estado = self.estado_repo.get_despachado()
            if not estado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHADO'")
            return estado
        else:
            # Hay bienes con despacho parcial → DESPACHO_PARCIAL
            estado = self.estado_repo.get_despacho_parcial()
            if not estado:
                print("ADVERTENCIA: No se encontró el estado 'DESPACHO_PARCIAL'")
            return estado


# ==================== RECEPCIÓN SERVICE BASE (DRY) ====================

class RecepcionServiceBase:
    """
    Clase base abstracta para servicios de recepción.

    Implementa el patrón Template Method para reutilizar lógica común
    entre RecepcionArticuloService y RecepcionActivoService.
    """

    # Clases a sobrescribir por subclases
    model_class = None
    detalle_model_class = None
    repository_class = None
    detalle_repository_class = None
    item_repository_class = None

    def __init__(self):
        if not self.repository_class or not self.detalle_repository_class:
            raise NotImplementedError("Subclases deben definir repository_class y detalle_repository_class")

        self.recepcion_repo = self.repository_class()
        self.detalle_repo = self.detalle_repository_class()
        self.estado_repo = EstadoRecepcionRepository()
        self.item_repo = self.item_repository_class() if self.item_repository_class else None

    def _get_prefijo_numero(self) -> str:
        """Retorna el prefijo para generar el número de recepción."""
        raise NotImplementedError("Subclases deben implementar _get_prefijo_numero()")

    def _requiere_bodega(self) -> bool:
        """Indica si este tipo de recepción requiere bodega."""
        return False

    def _get_campos_especificos_recepcion(self, **kwargs) -> Dict[str, Any]:
        """
        Retorna campos específicos del modelo de recepción.

        Returns:
            Dict con campos adicionales específicos del tipo de recepción
        """
        return {}

    def _validar_campos_especificos(self, **kwargs) -> None:
        """
        Valida campos específicos antes de crear la recepción.

        Raises:
            ValidationError: Si hay errores de validación
        """
        pass

    @transaction.atomic
    def crear_recepcion(
        self,
        recibido_por: User,
        orden_compra: Optional[OrdenCompra] = None,
        numero: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Crea una nueva recepción (Template Method).

        Args:
            recibido_por: Usuario que recibe
            orden_compra: Orden de compra asociada (opcional)
            numero: Número de recepción (opcional, se genera automático)
            **kwargs: Campos opcionales (bodega para artículos, etc.)

        Returns:
            Recepción creada (RecepcionArticulo o RecepcionActivo)

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar campos específicos
        self._validar_campos_especificos(**kwargs)

        # Generar número si no se proporciona
        if not numero:
            prefijo = self._get_prefijo_numero()
            numero = generar_codigo_unico(prefijo, self.model_class, 'numero', longitud=8)
        else:
            if self.recepcion_repo.exists_by_numero(numero):
                raise ValidationError({'numero': 'Ya existe una recepción con este número'})

        # Obtener estado inicial
        estado_inicial = self.estado_repo.get_inicial()
        if not estado_inicial:
            raise ValidationError('No se ha configurado un estado inicial para recepciones')

        # Preparar campos comunes
        campos_comunes = {
            'numero': numero,
            'orden_compra': orden_compra,
            'estado': estado_inicial,
            'recibido_por': recibido_por,
            'documento_referencia': kwargs.get('documento_referencia', ''),
            'observaciones': kwargs.get('observaciones', '')
        }

        # Agregar campos específicos de la subclase
        campos_especificos = self._get_campos_especificos_recepcion(**kwargs)
        campos_comunes.update(campos_especificos)

        # Crear recepción
        recepcion = self.model_class.objects.create(**campos_comunes)

        return recepcion

    @transaction.atomic
    def agregar_detalle(
        self,
        recepcion,
        item,
        cantidad: Decimal,
        **kwargs: Any
    ):
        """
        Agrega un detalle a la recepción (Template Method).

        Args:
            recepcion: Recepción
            item: Item recibido (Articulo o Activo)
            cantidad: Cantidad recibida
            **kwargs: Campos opcionales específicos

        Returns:
            Detalle creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar cantidad
        if cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})

        # Validar que la recepción no esté finalizada
        # Estados finales: COMPLETADA, CANCELADA
        estados_finales_recepcion = ['COMPLETADA', 'CANCELADA', 'CERRADA']
        if recepcion.estado.codigo in estados_finales_recepcion:
            raise ValidationError(f'No se pueden agregar detalles a una recepción en estado {recepcion.estado.nombre}')

        # Validaciones específicas antes de crear detalle
        self._validar_antes_crear_detalle(recepcion, item, cantidad, **kwargs)

        # Crear detalle
        detalle = self._crear_detalle_interno(recepcion, item, cantidad, **kwargs)

        # Actualizar stock si aplica (solo para artículos)
        self._post_crear_detalle(recepcion, item, cantidad, **kwargs)

        # Si hay orden de compra, actualizar cantidad recibida
        if recepcion.orden_compra:
            self._actualizar_cantidad_recibida_orden(recepcion.orden_compra, item, cantidad)

        return detalle

    def _validar_antes_crear_detalle(self, recepcion, item, cantidad: Decimal, **kwargs) -> None:
        """
        Hook method para validaciones específicas antes de crear detalle.

        Args:
            recepcion: Recepción
            item: Item a recibir
            cantidad: Cantidad
            **kwargs: Campos adicionales

        Raises:
            ValidationError: Si hay errores de validación
        """
        pass

    def _crear_detalle_interno(self, recepcion, item, cantidad: Decimal, **kwargs):
        """
        Crea el detalle de recepción con campos específicos.

        Args:
            recepcion: Recepción
            item: Item recibido
            cantidad: Cantidad
            **kwargs: Campos específicos

        Returns:
            Detalle creado
        """
        raise NotImplementedError("Subclases deben implementar _crear_detalle_interno()")

    def _post_crear_detalle(self, recepcion, item, cantidad: Decimal, **kwargs) -> None:
        """
        Hook method para acciones después de crear el detalle.

        Por ejemplo, actualizar stock para artículos.

        Args:
            recepcion: Recepción
            item: Item recibido
            cantidad: Cantidad
            **kwargs: Campos adicionales
        """
        pass

    def _actualizar_cantidad_recibida_orden(
        self,
        orden: OrdenCompra,
        item,
        cantidad_adicional: Decimal
    ) -> None:
        """
        Actualiza la cantidad recibida en el detalle de la orden de compra.

        Método genérico que funciona para artículos y activos.

        Args:
            orden: Orden de compra
            item: Item recibido (Articulo o Activo)
            cantidad_adicional: Cantidad adicional recibida
        """
        # Determinar qué repositorio usar basándose en el tipo de item
        if hasattr(item, 'stock_actual'):  # Es un Artículo
            from apps.compras.repositories import DetalleOrdenCompraArticuloRepository
            detalle_orden_repo = DetalleOrdenCompraArticuloRepository()
            detalles = detalle_orden_repo.filter_by_orden(orden)
            campo_item = 'articulo'
        else:  # Es un Activo
            from apps.compras.repositories import DetalleOrdenCompraRepository
            detalle_orden_repo = DetalleOrdenCompraRepository()
            detalles = detalle_orden_repo.filter_by_orden(orden)
            campo_item = 'activo'

        # Buscar el detalle del item
        for detalle in detalles:
            if getattr(detalle, campo_item).id == item.id:
                detalle.cantidad_recibida += cantidad_adicional
                detalle.save()
                break


# ==================== RECEPCIÓN ARTÍCULO SERVICE ====================

class RecepcionArticuloService(RecepcionServiceBase):
    """Service para lógica de negocio de Recepciones de Artículos."""

    # Configuración de modelos y repositorios
    model_class = RecepcionArticulo
    detalle_model_class = DetalleRecepcionArticulo
    repository_class = RecepcionArticuloRepository
    detalle_repository_class = DetalleRecepcionArticuloRepository
    item_repository_class = ArticuloRepository

    def _get_prefijo_numero(self) -> str:
        """Retorna el prefijo para el número de recepción de artículos."""
        return 'RART'

    def _requiere_bodega(self) -> bool:
        """Los artículos requieren bodega."""
        return True

    def _validar_campos_especificos(self, **kwargs) -> None:
        """
        Valida que se proporcione bodega para artículos.

        Raises:
            ValidationError: Si no se proporciona bodega
        """
        if 'bodega' not in kwargs or kwargs['bodega'] is None:
            raise ValidationError({'bodega': 'Debe especificar una bodega para recepción de artículos'})

    def _get_campos_especificos_recepcion(self, **kwargs) -> Dict[str, Any]:
        """
        Retorna campos específicos para recepción de artículos.

        Returns:
            Dict con campo 'bodega'
        """
        return {
            'bodega': kwargs.get('bodega')
        }

    def _crear_detalle_interno(
        self,
        recepcion: RecepcionArticulo,
        item: Articulo,
        cantidad: Decimal,
        **kwargs
    ) -> DetalleRecepcionArticulo:
        """
        Crea el detalle de recepción de artículo.

        Args:
            recepcion: Recepción
            item: Artículo
            cantidad: Cantidad
            **kwargs: lote, fecha_vencimiento, observaciones

        Returns:
            DetalleRecepcionArticulo creado
        """
        return DetalleRecepcionArticulo.objects.create(
            recepcion=recepcion,
            articulo=item,
            cantidad=cantidad,
            lote=kwargs.get('lote', ''),
            fecha_vencimiento=kwargs.get('fecha_vencimiento'),
            observaciones=kwargs.get('observaciones', '')
        )

    def _post_crear_detalle(
        self,
        recepcion: RecepcionArticulo,
        item: Articulo,
        cantidad: Decimal,
        **kwargs
    ) -> None:
        """
        Actualiza el stock del artículo después de crear el detalle.

        Args:
            recepcion: Recepción
            item: Artículo
            cantidad: Cantidad recibida
            **kwargs: actualizar_stock (default: True)

        Raises:
            ValidationError: Si excede stock máximo
        """
        actualizar_stock = kwargs.get('actualizar_stock', True)

        if actualizar_stock:
            stock_nuevo = item.stock_actual + cantidad

            # Validar stock máximo
            if item.stock_maximo and stock_nuevo > item.stock_maximo:
                raise ValidationError(
                    f'La cantidad recibida excede el stock máximo del artículo '
                    f'({item.stock_maximo})'
                )

            item.stock_actual = stock_nuevo
            item.save()

    # Método compatible con código existente que espera parámetro 'bodega'
    @transaction.atomic
    def crear_recepcion(
        self,
        recibido_por: User,
        bodega: Optional[Bodega] = None,
        orden_compra: Optional[OrdenCompra] = None,
        numero: Optional[str] = None,
        **kwargs: Any
    ) -> RecepcionArticulo:
        """
        Crea una nueva recepción de artículos.

        Args:
            recibido_por: Usuario que recibe
            bodega: Bodega de recepción (requerido)
            orden_compra: Orden de compra asociada (opcional)
            numero: Número de recepción (opcional, se genera automático)
            **kwargs: Campos opcionales

        Returns:
            RecepcionArticulo: Recepción creada

        Raises:
            ValidationError: Si hay errores de validación
        """
        # Agregar bodega a kwargs para que la clase base la procese
        kwargs['bodega'] = bodega
        return super().crear_recepcion(
            recibido_por=recibido_por,
            orden_compra=orden_compra,
            numero=numero,
            **kwargs
        )

    # Método compatible con código existente
    @transaction.atomic
    def agregar_detalle(
        self,
        recepcion: RecepcionArticulo,
        articulo: Articulo,
        cantidad: Decimal,
        actualizar_stock: bool = True,
        **kwargs: Any
    ) -> DetalleRecepcionArticulo:
        """
        Agrega un detalle a la recepción y actualiza el stock.

        Args:
            recepcion: Recepción
            articulo: Artículo recibido
            cantidad: Cantidad recibida
            actualizar_stock: Si debe actualizar el stock (default: True)
            **kwargs: Campos opcionales (lote, fecha_vencimiento, observaciones)

        Returns:
            DetalleRecepcionArticulo: Detalle creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        kwargs['actualizar_stock'] = actualizar_stock
        return super().agregar_detalle(recepcion, articulo, cantidad, **kwargs)


# ==================== RECEPCIÓN ACTIVO SERVICE ====================

class RecepcionActivoService(RecepcionServiceBase):
    """Service para lógica de negocio de Recepciones de Activos."""

    # Configuración de modelos y repositorios
    model_class = RecepcionActivo
    detalle_model_class = DetalleRecepcionActivo
    repository_class = RecepcionActivoRepository
    detalle_repository_class = DetalleRecepcionActivoRepository
    item_repository_class = ActivoRepository

    def _get_prefijo_numero(self) -> str:
        """Retorna el prefijo para el número de recepción de activos."""
        return 'RACT'

    def _requiere_bodega(self) -> bool:
        """Los activos NO requieren bodega."""
        return False

    def _validar_antes_crear_detalle(
        self,
        recepcion: RecepcionActivo,
        item: Activo,
        cantidad: Decimal,
        **kwargs
    ) -> None:
        """
        Valida que el activo tenga número de serie si lo requiere.

        Args:
            recepcion: Recepción
            item: Activo
            cantidad: Cantidad
            **kwargs: numero_serie

        Raises:
            ValidationError: Si el activo requiere serie y no se proporciona
        """
        numero_serie = kwargs.get('numero_serie')
        if item.requiere_serie and not numero_serie:
            raise ValidationError(
                {'numero_serie': 'Este activo requiere número de serie'}
            )

    def _crear_detalle_interno(
        self,
        recepcion: RecepcionActivo,
        item: Activo,
        cantidad: Decimal,
        **kwargs
    ) -> DetalleRecepcionActivo:
        """
        Crea el detalle de recepción de activo.

        Args:
            recepcion: Recepción
            item: Activo
            cantidad: Cantidad
            **kwargs: numero_serie, observaciones

        Returns:
            DetalleRecepcionActivo creado
        """
        numero_serie = kwargs.get('numero_serie', '')
        return DetalleRecepcionActivo.objects.create(
            recepcion=recepcion,
            activo=item,
            cantidad=cantidad,
            numero_serie=numero_serie,
            observaciones=kwargs.get('observaciones', '')
        )

    # Los activos NO actualizan stock, por lo que _post_crear_detalle
    # usa la implementación vacía de la clase base

    # Métodos compatibles con código existente
    @transaction.atomic
    def agregar_detalle(
        self,
        recepcion: RecepcionActivo,
        activo: Activo,
        cantidad: Decimal,
        **kwargs: Any
    ) -> DetalleRecepcionActivo:
        """
        Agrega un detalle a la recepción de activos.

        Args:
            recepcion: Recepción
            activo: Activo recibido
            cantidad: Cantidad recibida
            **kwargs: Campos opcionales (numero_serie, observaciones)

        Returns:
            DetalleRecepcionActivo: Detalle creado

        Raises:
            ValidationError: Si hay errores de validación
        """
        return super().agregar_detalle(recepcion, activo, cantidad, **kwargs)
