/**
 * Módulo para creación de órdenes de compra
 * Refactorizado siguiendo principios SOLID y Clean Code
 *
 * Responsabilidades separadas:
 * - FormValidator: Validación de datos
 * - DataCollector: Recolección de datos de tablas
 * - RowBuilder: Construcción de filas HTML
 * - TotalesCalculator: Cálculos de totales
 * - APIClient: Comunicación con backend
 * - OrdenCompraController: Coordinador principal
 */

// =============================================================================
// UTILIDADES
// =============================================================================

class DOMUtils {
    /**
     * Escapa HTML para prevenir XSS
     */
    static escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * Formatea números con separadores de miles
     */
    static formatNumber(num) {
        return new Intl.NumberFormat('es-CL').format(num || 0);
    }
}

// =============================================================================
// VALIDACIÓN
// =============================================================================

class FormValidator {
    /**
     * Valida un artículo individual
     */
    static validateArticulo(index) {
        const articuloInput = document.getElementById(`select_articulo_${index}`);
        const inputCantidad = document.getElementById(`cantidad_articulo_${index}`);

        if (!articuloInput || !articuloInput.value) {
            alert('Seleccione un artículo en todas las filas.');
            return false;
        }

        if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
            alert('Ingrese una cantidad válida en todas las filas de artículos.');
            return false;
        }

        return true;
    }

    /**
     * Valida un bien individual
     */
    static validateBien(index) {
        const bienInput = document.getElementById(`select_bien_${index}`);
        const inputCantidad = document.getElementById(`cantidad_bien_${index}`);

        if (!bienInput || !bienInput.value) {
            alert('Seleccione un bien/activo en todas las filas.');
            return false;
        }

        if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
            alert('Ingrese una cantidad válida en todas las filas de bienes.');
            return false;
        }

        return true;
    }
}

// =============================================================================
// RECOLECCIÓN DE DATOS
// =============================================================================

class DataCollector {
    /**
     * Recolecta datos de un artículo
     */
    static collectArticuloData(index) {
        const articuloInput = document.getElementById(`select_articulo_${index}`);
        const inputCantidad = document.getElementById(`cantidad_articulo_${index}`);
        const inputPrecio = document.getElementById(`precio_articulo_${index}`);
        const inputDescuento = document.getElementById(`descuento_articulo_${index}`);

        return {
            articulo_id: parseInt(articuloInput.value),
            cantidad: parseInt(inputCantidad.value),
            precio_unitario: parseFloat(inputPrecio.value) || 0,
            descuento: parseFloat(inputDescuento.value) || 0
        };
    }

    /**
     * Recolecta datos de un bien
     */
    static collectBienData(index) {
        const bienInput = document.getElementById(`select_bien_${index}`);
        const inputCantidad = document.getElementById(`cantidad_bien_${index}`);
        const inputPrecio = document.getElementById(`precio_bien_${index}`);
        const inputDescuento = document.getElementById(`descuento_bien_${index}`);

        return {
            activo_id: parseInt(bienInput.value),
            cantidad: parseInt(inputCantidad.value),
            precio_unitario: parseFloat(inputPrecio.value) || 0,
            descuento: parseFloat(inputDescuento.value) || 0
        };
    }

    /**
     * Recolecta todos los artículos del formulario
     */
    static collectAllArticulos(contador) {
        const articulos = [];

        for (let i = 0; i < contador; i++) {
            const fila = document.getElementById(`fila_articulo_${i}`);
            if (!fila) continue;

            if (!FormValidator.validateArticulo(i)) {
                throw new Error('Validación de artículo fallida');
            }

            articulos.push(this.collectArticuloData(i));
        }

        return articulos;
    }

    /**
     * Recolecta todos los bienes del formulario
     */
    static collectAllBienes(contador) {
        const bienes = [];

        for (let i = 0; i < contador; i++) {
            const fila = document.getElementById(`fila_bien_${i}`);
            if (!fila) continue;

            if (!FormValidator.validateBien(i)) {
                throw new Error('Validación de bien fallida');
            }

            bienes.push(this.collectBienData(i));
        }

        return bienes;
    }
}

// =============================================================================
// CÁLCULO DE TOTALES
// =============================================================================

class TotalesCalculator {
    /**
     * Calcula el subtotal de un item
     */
    static calculateSubtotal(cantidad, precioUnitario, descuento = 0) {
        return (cantidad * precioUnitario) - descuento;
    }

    /**
     * Actualiza el subtotal de un artículo en el DOM
     */
    static updateArticuloSubtotal(index) {
        const cantidad = parseFloat(document.getElementById(`cantidad_articulo_${index}`)?.value) || 0;
        const precio = parseFloat(document.getElementById(`precio_articulo_${index}`)?.value) || 0;
        const descuento = parseFloat(document.getElementById(`descuento_articulo_${index}`)?.value) || 0;

        const subtotal = this.calculateSubtotal(cantidad, precio, descuento);
        const subtotalElement = document.getElementById(`subtotal_articulo_${index}`);

        if (subtotalElement) {
            subtotalElement.textContent = `$${DOMUtils.formatNumber(subtotal)}`;
        }

        return subtotal;
    }

    /**
     * Actualiza el subtotal de un bien en el DOM
     */
    static updateBienSubtotal(index) {
        const cantidad = parseFloat(document.getElementById(`cantidad_bien_${index}`)?.value) || 0;
        const precio = parseFloat(document.getElementById(`precio_bien_${index}`)?.value) || 0;
        const descuento = parseFloat(document.getElementById(`descuento_bien_${index}`)?.value) || 0;

        const subtotal = this.calculateSubtotal(cantidad, precio, descuento);
        const subtotalElement = document.getElementById(`subtotal_bien_${index}`);

        if (subtotalElement) {
            subtotalElement.textContent = `$${DOMUtils.formatNumber(subtotal)}`;
        }

        return subtotal;
    }

    /**
     * Calcula y actualiza todos los totales
     */
    static updateAllTotales(contadorArticulos, contadorBienes) {
        let totalArticulos = 0;
        let totalBienes = 0;

        // Sumar artículos
        for (let i = 0; i < contadorArticulos; i++) {
            if (document.getElementById(`fila_articulo_${i}`)) {
                totalArticulos += this.updateArticuloSubtotal(i);
            }
        }

        // Sumar bienes
        for (let i = 0; i < contadorBienes; i++) {
            if (document.getElementById(`fila_bien_${i}`)) {
                totalBienes += this.updateBienSubtotal(i);
            }
        }

        const totalGeneral = totalArticulos + totalBienes;

        // Actualizar DOM
        const totalArticulosElement = document.getElementById('total-articulos');
        const totalBienesElement = document.getElementById('total-bienes');
        const totalGeneralElement = document.getElementById('total-general');

        if (totalArticulosElement) {
            totalArticulosElement.textContent = `$${DOMUtils.formatNumber(totalArticulos)}`;
        }
        if (totalBienesElement) {
            totalBienesElement.textContent = `$${DOMUtils.formatNumber(totalBienes)}`;
        }
        if (totalGeneralElement) {
            totalGeneralElement.textContent = `$${DOMUtils.formatNumber(totalGeneral)}`;
        }

        return { totalArticulos, totalBienes, totalGeneral };
    }
}

// =============================================================================
// CONSTRUCCIÓN DE FILAS (UI)
// =============================================================================

class InputBuilder {
    /**
     * Crea input de cantidad (solo enteros)
     */
    static createCantidadInput(index, tipo, initialValue = '') {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `cantidad_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '1';
        input.step = '1';

        // Forzar valor inicial a entero
        const valorEntero = initialValue ? Math.floor(parseFloat(initialValue)) : '';
        input.value = valorEntero;
        input.required = true;

        // Prevenir entrada de decimales
        input.addEventListener('keydown', (e) => {
            if (e.key === '.' || e.key === ',') {
                e.preventDefault();
            }
        });

        // Forzar entero al cambiar valor
        input.addEventListener('input', (e) => {
            const value = e.target.value;
            if (value.includes('.') || value.includes(',')) {
                e.target.value = Math.floor(parseFloat(value)) || '';
            }
        });

        // Forzar entero al perder el foco (blur)
        input.addEventListener('blur', (e) => {
            const value = e.target.value;
            if (value) {
                e.target.value = Math.floor(parseFloat(value));
            }
        });

        return input;
    }

    /**
     * Crea input de precio (permite decimales)
     */
    static createPrecioInput(index, tipo, initialValue = '0') {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `precio_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '0';
        input.step = '0.01';

        // Asegurar que el valor inicial sea numérico
        const valorPrecio = initialValue ? parseFloat(initialValue) : 0;
        input.value = valorPrecio;

        // Formatear a 2 decimales al perder el foco
        input.addEventListener('blur', (e) => {
            const value = parseFloat(e.target.value);
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2);
            }
        });

        return input;
    }

    /**
     * Crea input de descuento (permite decimales)
     */
    static createDescuentoInput(index, tipo) {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `descuento_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '0';
        input.step = '0.01';
        input.value = '0';

        // Formatear a 2 decimales al perder el foco
        input.addEventListener('blur', (e) => {
            const value = parseFloat(e.target.value);
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2);
            }
        });

        return input;
    }

    /**
     * Crea botón eliminar
     */
    static createEliminarButton(index, tipo, onClickHandler) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-danger';
        btn.innerHTML = '<i class="ri-delete-bin-line"></i>';
        btn.onclick = () => onClickHandler(index, tipo);
        return btn;
    }
}

class ArticuloRowBuilder {
    /**
     * Construye una fila de artículo
     */
    static buildRow(detalle, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_articulo_${index}`;

        // Agregar atributo para identificar a qué solicitud pertenece
        if (detalle.solicitud_id) {
            fila.setAttribute('data-solicitud-id', detalle.solicitud_id);
        }

        // Columna: Artículo
        const celdaArticulo = document.createElement('td');
        celdaArticulo.innerHTML = `
            <strong>${DOMUtils.escapeHtml(detalle.codigo)} - ${DOMUtils.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${DOMUtils.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${DOMUtils.escapeHtml(detalle.solicitud_numero)}</small>
        `;

        // Hidden input para el ID
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_articulo_${index}`;
        hiddenInput.value = detalle.articulo_id;
        celdaArticulo.appendChild(hiddenInput);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'articulo', detalle.cantidad_aprobada);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'articulo', detalle.precio_unitario || '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'articulo');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        const subtotal = TotalesCalculator.calculateSubtotal(
            parseFloat(detalle.cantidad_aprobada),
            parseFloat(detalle.precio_unitario || 0)
        );
        celdaSubtotal.innerHTML = `<strong id="subtotal_articulo_${index}" class="text-end d-block">$${DOMUtils.formatNumber(subtotal)}</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'articulo', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaArticulo);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

class BienRowBuilder {
    /**
     * Construye una fila de bien/activo
     */
    static buildRow(detalle, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_bien_${index}`;

        // Agregar atributo para identificar a qué solicitud pertenece
        if (detalle.solicitud_id) {
            fila.setAttribute('data-solicitud-id', detalle.solicitud_id);
        }

        // Columna: Bien
        const celdaBien = document.createElement('td');
        celdaBien.innerHTML = `
            <strong>${DOMUtils.escapeHtml(detalle.codigo)} - ${DOMUtils.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${DOMUtils.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${DOMUtils.escapeHtml(detalle.solicitud_numero)}</small>
        `;

        // Hidden input para el ID
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_bien_${index}`;
        hiddenInput.value = detalle.activo_id;
        celdaBien.appendChild(hiddenInput);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'bien', detalle.cantidad_aprobada);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'bien', detalle.precio_unitario || '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'bien');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        const subtotal = TotalesCalculator.calculateSubtotal(
            parseFloat(detalle.cantidad_aprobada),
            parseFloat(detalle.precio_unitario || 0)
        );
        celdaSubtotal.innerHTML = `<strong id="subtotal_bien_${index}" class="text-end d-block">$${DOMUtils.formatNumber(subtotal)}</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'bien', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaBien);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

class ArticuloManualRowBuilder {
    /**
     * Construye una fila de artículo manual con selector
     */
    static buildRow(articulos, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_articulo_${index}`;

        // Columna: Artículo (selector)
        const celdaArticulo = document.createElement('td');
        const select = document.createElement('select');
        select.id = `select_articulo_${index}`;
        select.className = 'form-select form-select-sm';
        select.required = true;

        // Opción vacía
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = 'Seleccione un artículo...';
        select.appendChild(emptyOption);

        // Opciones de artículos
        articulos.forEach(art => {
            const option = document.createElement('option');
            option.value = art.id;
            option.textContent = `${art.codigo} - ${art.nombre} (${art.categoria})`;
            select.appendChild(option);
        });

        celdaArticulo.appendChild(select);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'articulo', 1);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'articulo', '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'articulo');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        celdaSubtotal.innerHTML = `<strong id="subtotal_articulo_${index}" class="text-end d-block">$0</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'articulo', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaArticulo);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

class BienManualRowBuilder {
    /**
     * Construye una fila de bien/activo manual con selector
     */
    static buildRow(activos, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_bien_${index}`;

        // Columna: Bien (selector)
        const celdaBien = document.createElement('td');
        const select = document.createElement('select');
        select.id = `select_bien_${index}`;
        select.className = 'form-select form-select-sm';
        select.required = true;

        // Opción vacía
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = 'Seleccione un bien/activo...';
        select.appendChild(emptyOption);

        // Opciones de bienes
        activos.forEach(activo => {
            const option = document.createElement('option');
            option.value = activo.id;
            option.textContent = `${activo.codigo} - ${activo.nombre} (${activo.categoria})`;
            select.appendChild(option);
        });

        celdaBien.appendChild(select);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'bien', 1);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'bien', '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'bien');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        celdaSubtotal.innerHTML = `<strong id="subtotal_bien_${index}" class="text-end d-block">$0</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'bien', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaBien);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

// =============================================================================
// CLIENTE API
// =============================================================================

class APIClient {
    /**
     * Obtiene detalles de solicitudes
     */
    static async fetchDetallesSolicitudes(solicitudIds) {
        console.log('=== APIClient.fetchDetallesSolicitudes ===');
        console.log('IDs recibidos:', solicitudIds);

        if (solicitudIds.length === 0) {
            console.log('No hay IDs para buscar, retornando array vacío');
            return [];
        }

        const params = new URLSearchParams();
        solicitudIds.forEach(id => params.append('solicitudes[]', id));
        const url = `/compras/api/obtener-detalles-solicitudes/?${params.toString()}`;

        console.log('URL del API:', url);

        try {
            console.log('Iniciando llamada fetch...');
            const response = await fetch(url);
            console.log('Respuesta recibida:', response);
            console.log('Status:', response.status);
            console.log('Status Text:', response.statusText);

            const data = await response.json();
            console.log('Datos JSON parseados:', data);

            return data.detalles || [];
        } catch (error) {
            console.error('Error al cargar detalles de solicitudes:', error);
            throw error;
        }
    }
}

// =============================================================================
// CONTROLADOR PRINCIPAL
// =============================================================================

class OrdenCompraController {
    constructor(articulos, activos) {
        this.articulosDisponibles = articulos;
        this.activosDisponibles = activos;
        this.solicitudesSeleccionadas = [];
        this.articulosManualesSeleccionados = [];
        this.bienesManualesSeleccionados = [];
        this.contadorArticulos = 0;
        this.contadorBienes = 0;
        this.modalArticulo = null;
        this.modalBien = null;

        this.init();
    }

    init() {
        this.initModals();
        this.setupEventListeners();
        this.initializeEmptyStates();
        console.log('OrdenCompraController inicializado correctamente');
    }

    initModals() {
        const modalArticuloEl = document.getElementById('modalArticulo');
        const modalBienEl = document.getElementById('modalBien');

        if (modalArticuloEl) {
            this.modalArticulo = new bootstrap.Modal(modalArticuloEl);
        }
        if (modalBienEl) {
            this.modalBien = new bootstrap.Modal(modalBienEl);
        }
    }

    initializeEmptyStates() {
        // Mostrar empty states inicialmente
        this.actualizarVisualizacionArticulos();
        this.actualizarVisualizacionBienes();
    }

    setupEventListeners() {
        console.log('=== setupEventListeners ===');

        // Formulario principal
        const form = document.getElementById('form-orden-compra');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
            console.log('Event listener agregado al formulario de orden');
        }

        // Tabla de solicitudes
        const tablaSolicitudes = document.getElementById('tabla-solicitudes-disponibles');
        if (tablaSolicitudes) {
            tablaSolicitudes.addEventListener('click', (e) => this.handleSolicitudClick(e));
            console.log('Event listener agregado a tabla de solicitudes');
        }

        // Botones para abrir modales
        const btnAgregarArticulo = document.getElementById('btn-agregar-articulo-manual');
        if (btnAgregarArticulo) {
            btnAgregarArticulo.addEventListener('click', () => this.abrirModalArticulo());
            console.log('Event listener agregado al botón agregar artículo');
        }

        const btnAgregarBien = document.getElementById('btn-agregar-bien-manual');
        if (btnAgregarBien) {
            btnAgregarBien.addEventListener('click', () => this.abrirModalBien());
            console.log('Event listener agregado al botón agregar bien');
        }

        // Buscadores de modales
        const inputBuscarArticulo = document.getElementById('buscar-articulo');
        if (inputBuscarArticulo) {
            inputBuscarArticulo.addEventListener('input', (e) => this.filtrarArticulos(e));
        }

        const inputBuscarBien = document.getElementById('buscar-bien');
        if (inputBuscarBien) {
            inputBuscarBien.addEventListener('input', (e) => this.filtrarBienes(e));
        }

        // Botones de selección en modales
        document.querySelectorAll('.btn-seleccionar-articulo').forEach(btn => {
            btn.addEventListener('click', (e) => this.seleccionarArticuloDesdeModal(e));
        });

        document.querySelectorAll('.btn-seleccionar-bien').forEach(btn => {
            btn.addEventListener('click', (e) => this.seleccionarBienDesdeModal(e));
        });

        // Toggle de "Requiere asociar solicitud"
        const radioSi = document.getElementById('requiere_solicitud_si');
        const radioNo = document.getElementById('requiere_solicitud_no');

        if (radioSi) {
            radioSi.addEventListener('change', () => this.toggleSeccionSolicitudes(true));
        }
        if (radioNo) {
            radioNo.addEventListener('change', () => this.toggleSeccionSolicitudes(false));
        }
    }

    toggleSeccionSolicitudes(mostrar) {
        const seccionSolicitudes = document.getElementById('seccion-solicitudes');
        if (seccionSolicitudes) {
            seccionSolicitudes.style.display = mostrar ? 'block' : 'none';
            console.log(`Sección de solicitudes ${mostrar ? 'mostrada' : 'ocultada'}`);
        }
    }

    handleSolicitudClick(event) {
        console.log('=== Click detectado en tabla de solicitudes ===');
        console.log('Event target:', event.target);

        const btnToggle = event.target.closest('.btn-toggle-solicitud');
        console.log('Botón encontrado:', btnToggle);

        if (!btnToggle) {
            console.log('No se encontró botón .btn-toggle-solicitud');
            return;
        }

        const solicitudId = btnToggle.getAttribute('data-solicitud-id');
        const action = btnToggle.getAttribute('data-action');

        console.log('Solicitud ID:', solicitudId);
        console.log('Acción:', action);

        if (action === 'agregar') {
            console.log('Llamando a agregarSolicitud...');
            this.agregarSolicitud(solicitudId);
        } else {
            console.log('Llamando a quitarSolicitud...');
            this.quitarSolicitud(solicitudId);
        }
    }

    async agregarSolicitud(solicitudId) {
        console.log('=== agregarSolicitud llamada ===');
        console.log('Solicitud ID recibida:', solicitudId);
        console.log('Solicitudes ya seleccionadas:', this.solicitudesSeleccionadas);

        if (this.solicitudesSeleccionadas.includes(solicitudId)) {
            console.log('Solicitud ya está en la lista, ignorando...');
            return;
        }

        this.solicitudesSeleccionadas.push(solicitudId);
        console.log('Solicitud agregada. Lista actualizada:', this.solicitudesSeleccionadas);
        console.log('Llamando a cargarArticulosDeSolicitudes...');
        await this.cargarArticulosDeSolicitudes();

        // Actualizar campo oculto de solicitudes
        this.actualizarCampoSolicitudes();

        // Actualizar UI del botón
        console.log('Actualizando UI del botón...');
        this.toggleBotonSolicitud(solicitudId, 'agregar');
    }

    quitarSolicitud(solicitudId) {
        console.log('=== quitarSolicitud ===');
        console.log('Solicitud ID a quitar:', solicitudId);

        const index = this.solicitudesSeleccionadas.indexOf(solicitudId);
        if (index > -1) {
            this.solicitudesSeleccionadas.splice(index, 1);
            console.log('Solicitud removida de la lista. Lista actualizada:', this.solicitudesSeleccionadas);
        }

        // Quitar todos los artículos de esta solicitud
        this.quitarArticulosDeSolicitud(solicitudId);

        // Quitar todos los bienes de esta solicitud
        this.quitarBienesDeSolicitud(solicitudId);

        // Actualizar totales
        this.actualizarTotales();

        // Actualizar campo oculto de solicitudes
        this.actualizarCampoSolicitudes();

        // Actualizar UI del botón
        this.toggleBotonSolicitud(solicitudId, 'quitar');
    }

    quitarArticulosDeSolicitud(solicitudId) {
        console.log('=== quitarArticulosDeSolicitud ===');
        console.log('Buscando artículos de solicitud ID:', solicitudId);

        const tbody = document.getElementById('tbody-articulos-orden');
        if (!tbody) {
            console.warn('No se encontró tbody-articulos-orden');
            return;
        }

        // Buscar todas las filas que pertenecen a esta solicitud
        const filas = tbody.querySelectorAll(`tr[data-solicitud-id="${solicitudId}"]`);
        console.log('Filas de artículos encontradas:', filas.length);

        filas.forEach(fila => {
            console.log('Eliminando fila:', fila.id);
            fila.remove();
        });

        // Actualizar visualización
        this.actualizarVisualizacionArticulos();
    }

    quitarBienesDeSolicitud(solicitudId) {
        console.log('=== quitarBienesDeSolicitud ===');
        console.log('Buscando bienes de solicitud ID:', solicitudId);

        const tbody = document.getElementById('tbody-bienes-orden');
        if (!tbody) {
            console.warn('No se encontró tbody-bienes-orden');
            return;
        }

        // Buscar todas las filas que pertenecen a esta solicitud
        const filas = tbody.querySelectorAll(`tr[data-solicitud-id="${solicitudId}"]`);
        console.log('Filas de bienes encontradas:', filas.length);

        filas.forEach(fila => {
            console.log('Eliminando fila:', fila.id);
            fila.remove();
        });

        // Actualizar visualización
        this.actualizarVisualizacionBienes();
    }

    actualizarCampoSolicitudes() {
        console.log('=== actualizarCampoSolicitudes ===');
        console.log('Solicitudes seleccionadas:', this.solicitudesSeleccionadas);

        const container = document.getElementById('solicitudes-hidden-inputs');
        if (!container) {
            console.error('No se encontró el contenedor #solicitudes-hidden-inputs');
            return;
        }

        // Limpiar todos los inputs existentes
        container.innerHTML = '';

        // Crear un input hidden por cada solicitud seleccionada
        this.solicitudesSeleccionadas.forEach(solicitudId => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'solicitudes';
            input.value = solicitudId;
            container.appendChild(input);
            console.log(`Input hidden creado para solicitud ID: ${solicitudId}`);
        });

        console.log(`Total de inputs creados: ${this.solicitudesSeleccionadas.length}`);
    }

    toggleBotonSolicitud(solicitudId, accion) {
        console.log('=== toggleBotonSolicitud ===');
        console.log('Solicitud ID:', solicitudId);
        console.log('Acción:', accion);

        // Buscar la fila de la solicitud en la tabla
        const fila = document.querySelector(`tr[data-solicitud-id="${solicitudId}"]`);
        console.log('Fila encontrada:', fila);

        if (!fila) {
            console.warn('No se encontró la fila de la solicitud');
            return;
        }

        // Buscar el botón dentro de la fila
        const boton = fila.querySelector('.btn-toggle-solicitud');
        console.log('Botón encontrado:', boton);

        if (!boton) {
            console.warn('No se encontró el botón en la fila');
            return;
        }

        if (accion === 'agregar') {
            // Cambiar a botón "Quitar"
            boton.className = 'btn btn-sm btn-danger btn-toggle-solicitud';
            boton.setAttribute('data-action', 'quitar');
            boton.innerHTML = '<i class="ri-close-line"></i> Quitar';

            // Resaltar la fila
            fila.classList.add('table-success');

            console.log('Botón cambiado a "Quitar" y fila resaltada');
        } else {
            // Cambiar a botón "Agregar"
            boton.className = 'btn btn-sm btn-success btn-toggle-solicitud';
            boton.setAttribute('data-action', 'agregar');
            boton.innerHTML = '<i class="ri-add-line"></i> Agregar';

            // Quitar resaltado de la fila
            fila.classList.remove('table-success');

            console.log('Botón cambiado a "Agregar" y fila sin resaltar');
        }
    }

    async cargarArticulosDeSolicitudes() {
        console.log('=== cargarArticulosDeSolicitudes llamada ===');
        console.log('Solicitudes a cargar:', this.solicitudesSeleccionadas);

        try {
            const detalles = await APIClient.fetchDetallesSolicitudes(this.solicitudesSeleccionadas);
            console.log('Detalles recibidos del API:', detalles);
            console.log('Cantidad de detalles:', detalles.length);
            this.procesarDetalles(detalles);
            console.log('Detalles procesados exitosamente');
        } catch (error) {
            console.error('Error al procesar solicitudes:', error);
            alert('Error al cargar los detalles de las solicitudes');
        }
    }

    procesarDetalles(detalles) {
        console.log('=== procesarDetalles ===');
        console.log('Detalles a procesar:', detalles);

        detalles.forEach((detalle, index) => {
            console.log(`Procesando detalle ${index + 1}:`, detalle);
            console.log('Tipo de detalle:', detalle.tipo);

            if (detalle.tipo === 'articulo') {
                console.log('Es un artículo, llamando a agregarArticuloSolicitud...');
                this.agregarArticuloSolicitud(detalle);
            } else {
                console.log('Es un bien/activo, llamando a agregarBienSolicitud...');
                this.agregarBienSolicitud(detalle);
            }
        });

        console.log('Todos los detalles procesados');
    }

    agregarArticuloSolicitud(detalle) {
        console.log('=== agregarArticuloSolicitud ===');
        console.log('Detalle recibido:', detalle);

        const tbody = document.getElementById('tbody-articulos-orden');
        console.log('tbody encontrado:', tbody);

        if (!tbody) {
            console.error('No se encontró tbody-articulos-orden');
            return;
        }

        console.log('Hijos actuales de tbody:', tbody.children.length);

        // Limpiar mensaje "vacío" si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            console.log('Limpiando mensaje vacío...');
            tbody.innerHTML = '';
        }

        console.log('Construyendo fila con contador:', this.contadorArticulos);

        const fila = ArticuloRowBuilder.buildRow(
            detalle,
            this.contadorArticulos,
            (index) => this.eliminarFila(index, 'articulo'),
            () => this.actualizarTotales()
        );

        console.log('Fila construida:', fila);

        tbody.appendChild(fila);
        console.log('Fila agregada al tbody');

        this.contadorArticulos++;
        console.log('Contador incrementado a:', this.contadorArticulos);

        this.actualizarVisualizacionArticulos();
        this.actualizarTotales();
        console.log('Totales actualizados');
    }

    agregarBienSolicitud(detalle) {
        console.log('=== agregarBienSolicitud ===');
        console.log('Detalle recibido:', detalle);

        const tbody = document.getElementById('tbody-bienes-orden');
        console.log('tbody encontrado:', tbody);

        if (!tbody) {
            console.error('No se encontró tbody-bienes-orden');
            return;
        }

        console.log('Hijos actuales de tbody:', tbody.children.length);

        // Limpiar mensaje "vacío" si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            console.log('Limpiando mensaje vacío...');
            tbody.innerHTML = '';
        }

        console.log('Construyendo fila con contador:', this.contadorBienes);

        const fila = BienRowBuilder.buildRow(
            detalle,
            this.contadorBienes,
            (index) => this.eliminarFila(index, 'bien'),
            () => this.actualizarTotales()
        );

        console.log('Fila construida:', fila);

        tbody.appendChild(fila);
        console.log('Fila agregada al tbody');

        this.contadorBienes++;
        console.log('Contador incrementado a:', this.contadorBienes);

        this.actualizarVisualizacionBienes();
        this.actualizarTotales();
        console.log('Totales actualizados');
    }

    abrirModalArticulo() {
        if (this.modalArticulo) {
            this.modalArticulo.show();
        }
    }

    abrirModalBien() {
        if (this.modalBien) {
            this.modalBien.show();
        }
    }

    filtrarArticulos(e) {
        const termino = e.target.value.toLowerCase();
        const filas = document.querySelectorAll('#tbody-lista-articulos tr');

        filas.forEach(fila => {
            const codigo = fila.dataset.articuloCodigo.toLowerCase();
            const nombre = fila.dataset.articuloNombre.toLowerCase();

            if (codigo.includes(termino) || nombre.includes(termino)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    filtrarBienes(e) {
        const termino = e.target.value.toLowerCase();
        const filas = document.querySelectorAll('#tbody-lista-bienes tr');

        filas.forEach(fila => {
            const codigo = fila.dataset.bienCodigo.toLowerCase();
            const nombre = fila.dataset.bienNombre.toLowerCase();

            if (codigo.includes(termino) || nombre.includes(termino)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    seleccionarArticuloDesdeModal(e) {
        const fila = e.target.closest('tr');
        const articuloId = parseInt(fila.dataset.articuloId);

        // Verificar si ya está seleccionado
        const yaExiste = this.articulosManualesSeleccionados.some(a => a.id === articuloId) ||
                        document.querySelector(`#tbody-articulos-orden tr[data-articulo-id="${articuloId}"]`);

        if (yaExiste) {
            alert('Este artículo ya ha sido agregado');
            return;
        }

        // Crear objeto artículo
        const articulo = {
            id: articuloId,
            codigo: fila.dataset.articuloCodigo,
            nombre: fila.dataset.articuloNombre,
            categoria: fila.dataset.articuloCategoria,
            unidad: fila.dataset.articuloUnidad
        };

        this.articulosManualesSeleccionados.push(articulo);
        this.agregarFilaArticuloManual(articulo);

        // Cerrar modal
        this.modalArticulo.hide();

        // Limpiar búsqueda
        document.getElementById('buscar-articulo').value = '';
        document.querySelectorAll('#tbody-lista-articulos tr').forEach(tr => tr.style.display = '');
    }

    seleccionarBienDesdeModal(e) {
        const fila = e.target.closest('tr');
        const bienId = parseInt(fila.dataset.bienId);

        // Verificar si ya está seleccionado
        const yaExiste = this.bienesManualesSeleccionados.some(b => b.id === bienId) ||
                        document.querySelector(`#tbody-bienes-orden tr[data-bien-id="${bienId}"]`);

        if (yaExiste) {
            alert('Este bien/activo ya ha sido agregado');
            return;
        }

        // Crear objeto bien
        const bien = {
            id: bienId,
            codigo: fila.dataset.bienCodigo,
            nombre: fila.dataset.bienNombre,
            categoria: fila.dataset.bienCategoria
        };

        this.bienesManualesSeleccionados.push(bien);
        this.agregarFilaBienManual(bien);

        // Cerrar modal
        this.modalBien.hide();

        // Limpiar búsqueda
        document.getElementById('buscar-bien').value = '';
        document.querySelectorAll('#tbody-lista-bienes tr').forEach(tr => tr.style.display = '');
    }

    agregarFilaArticuloManual(articulo) {
        const tbody = document.getElementById('tbody-articulos-orden');
        if (!tbody) return;

        const fila = document.createElement('tr');
        fila.dataset.articuloId = articulo.id;
        fila.dataset.filaId = this.contadorArticulos;
        fila.id = `fila_articulo_${this.contadorArticulos}`;

        fila.innerHTML = `
            <td>
                <strong>${DOMUtils.escapeHtml(articulo.nombre)}</strong><br>
                <small class="text-muted">Código: ${DOMUtils.escapeHtml(articulo.codigo)}</small>
                <input type="hidden" id="select_articulo_${this.contadorArticulos}" value="${articulo.id}">
            </td>
            <td>
                <input type="number" id="cantidad_articulo_${this.contadorArticulos}" class="form-control form-control-sm" min="1" step="1" value="1" required>
                <small class="text-muted">${DOMUtils.escapeHtml(articulo.unidad)}</small>
            </td>
            <td>
                <input type="number" id="precio_articulo_${this.contadorArticulos}" class="form-control form-control-sm" min="0" step="0.01" value="0" required>
            </td>
            <td>
                <input type="number" id="descuento_articulo_${this.contadorArticulos}" class="form-control form-control-sm" min="0" step="0.01" value="0">
            </td>
            <td>
                <strong id="subtotal_articulo_${this.contadorArticulos}" class="text-end d-block">$0</strong>
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-eliminar-articulo" data-fila-id="${this.contadorArticulos}">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </td>
        `;

        tbody.appendChild(fila);

        // Event listeners para actualizar subtotal
        fila.querySelector(`#cantidad_articulo_${this.contadorArticulos}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector(`#precio_articulo_${this.contadorArticulos}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector(`#descuento_articulo_${this.contadorArticulos}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector('.btn-eliminar-articulo').addEventListener('click', (e) => this.eliminarFilaArticuloManual(e));

        this.contadorArticulos++;
        this.actualizarVisualizacionArticulos();
        this.actualizarTotales();
    }

    agregarFilaBienManual(bien) {
        const tbody = document.getElementById('tbody-bienes-orden');
        if (!tbody) return;

        const fila = document.createElement('tr');
        fila.dataset.bienId = bien.id;
        fila.dataset.filaId = this.contadorBienes;
        fila.id = `fila_bien_${this.contadorBienes}`;

        fila.innerHTML = `
            <td>
                <strong>${DOMUtils.escapeHtml(bien.nombre)}</strong><br>
                <small class="text-muted">Código: ${DOMUtils.escapeHtml(bien.codigo)}</small>
                <input type="hidden" id="select_bien_${this.contadorBienes}" value="${bien.id}">
            </td>
            <td>
                <input type="number" id="cantidad_bien_${this.contadorBienes}" class="form-control form-control-sm" min="1" step="1" value="1" required>
                <small class="text-muted">unidad</small>
            </td>
            <td>
                <input type="number" id="precio_bien_${this.contadorBienes}" class="form-control form-control-sm" min="0" step="0.01" value="0" required>
            </td>
            <td>
                <input type="number" id="descuento_bien_${this.contadorBienes}" class="form-control form-control-sm" min="0" step="0.01" value="0">
            </td>
            <td>
                <strong id="subtotal_bien_${this.contadorBienes}" class="text-end d-block">$0</strong>
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-eliminar-bien" data-fila-id="${this.contadorBienes}">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </td>
        `;

        tbody.appendChild(fila);

        // Event listeners para actualizar subtotal
        fila.querySelector(`#cantidad_bien_${this.contadorBienes}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector(`#precio_bien_${this.contadorBienes}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector(`#descuento_bien_${this.contadorBienes}`).addEventListener('input', () => this.actualizarTotales());
        fila.querySelector('.btn-eliminar-bien').addEventListener('click', (e) => this.eliminarFilaBienManual(e));

        this.contadorBienes++;
        this.actualizarVisualizacionBienes();
        this.actualizarTotales();
    }

    eliminarFilaArticuloManual(e) {
        const filaId = e.target.closest('button').dataset.filaId;
        const fila = document.querySelector(`#tbody-articulos-orden tr[data-fila-id="${filaId}"]`);
        if (fila) {
            const articuloId = parseInt(fila.dataset.articuloId);
            this.articulosManualesSeleccionados = this.articulosManualesSeleccionados.filter(a => a.id !== articuloId);
            fila.remove();
            this.actualizarVisualizacionArticulos();
            this.actualizarTotales();
        }
    }

    eliminarFilaBienManual(e) {
        const filaId = e.target.closest('button').dataset.filaId;
        const fila = document.querySelector(`#tbody-bienes-orden tr[data-fila-id="${filaId}"]`);
        if (fila) {
            const bienId = parseInt(fila.dataset.bienId);
            this.bienesManualesSeleccionados = this.bienesManualesSeleccionados.filter(b => b.id !== bienId);
            fila.remove();
            this.actualizarVisualizacionBienes();
            this.actualizarTotales();
        }
    }

    actualizarVisualizacionArticulos() {
        const tbody = document.getElementById('tbody-articulos-orden');
        const tabla = document.getElementById('tabla-articulos-orden');
        const sinArticulos = document.getElementById('sin-articulos');
        const tablaContainer = tabla ? tabla.closest('.table-responsive') : null;

        if (!tbody || !tabla) return;

        const filasReales = tbody.querySelectorAll('tr').length;

        if (filasReales === 0) {
            // Mostrar empty state
            if (sinArticulos) {
                sinArticulos.style.display = 'block';
            }
            if (tablaContainer) tablaContainer.style.display = 'none';
        } else {
            // Mostrar tabla
            if (sinArticulos) {
                sinArticulos.style.display = 'none';
            }
            if (tablaContainer) tablaContainer.style.display = 'block';
        }
    }

    actualizarVisualizacionBienes() {
        const tbody = document.getElementById('tbody-bienes-orden');
        const tabla = document.getElementById('tabla-bienes-orden');
        const sinBienes = document.getElementById('sin-bienes');
        const tablaContainer = tabla ? tabla.closest('.table-responsive') : null;

        if (!tbody || !tabla) return;

        const filasReales = tbody.querySelectorAll('tr').length;

        if (filasReales === 0) {
            // Mostrar empty state
            if (sinBienes) {
                sinBienes.style.display = 'block';
            }
            if (tablaContainer) tablaContainer.style.display = 'none';
        } else {
            // Mostrar tabla
            if (sinBienes) {
                sinBienes.style.display = 'none';
            }
            if (tablaContainer) tablaContainer.style.display = 'block';
        }
    }

    eliminarFila(index, tipo) {
        const fila = document.getElementById(`fila_${tipo}_${index}`);
        if (fila) {
            fila.remove();
            this.actualizarTotales();

            // Si no quedan filas, mostrar mensaje vacío
            const tbody = document.getElementById(`tbody-${tipo}s-orden`);
            if (tbody && tbody.children.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            ${tipo === 'articulo' ? 'No hay artículos agregados. Haga clic en "Añadir Artículo" para comenzar.' : 'No hay bienes agregados'}
                        </td>
                    </tr>
                `;
            }
        }
    }

    actualizarTotales() {
        TotalesCalculator.updateAllTotales(this.contadorArticulos, this.contadorBienes);
    }

    handleFormSubmit(event) {
        console.log('=== INICIANDO validación y envío del formulario ===');

        try {
            // Recolectar datos
            const articulos = DataCollector.collectAllArticulos(this.contadorArticulos);
            const bienes = DataCollector.collectAllBienes(this.contadorBienes);

            // Guardar en campos ocultos
            this.saveToHiddenFields(articulos, bienes);

            console.log('Artículos:', articulos);
            console.log('Bienes:', bienes);
            console.log('=== Formulario listo para enviar ===');

            // Permitir que el formulario se envíe normalmente
            return true;

        } catch (error) {
            // Si hay error de validación, prevenir el envío
            event.preventDefault();
            console.error('Error en validación:', error);
            return false;
        }
    }

    saveToHiddenFields(articulos, bienes) {
        const articulosInput = document.getElementById('articulosJson');
        const bienesInput = document.getElementById('bienesJson');

        if (articulosInput) {
            articulosInput.value = JSON.stringify(articulos);
            console.log('Artículos JSON guardado:', articulosInput.value);
        }

        if (bienesInput) {
            bienesInput.value = JSON.stringify(bienes);
            console.log('Bienes JSON guardado:', bienesInput.value);
        }
    }
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM Content Loaded ===');
    console.log('ARTICULOS_DISPONIBLES definido?', typeof ARTICULOS_DISPONIBLES !== 'undefined');
    console.log('ACTIVOS_DISPONIBLES definido?', typeof ACTIVOS_DISPONIBLES !== 'undefined');

    if (typeof ARTICULOS_DISPONIBLES !== 'undefined') {
        console.log('Artículos disponibles:', ARTICULOS_DISPONIBLES.length);
    }
    if (typeof ACTIVOS_DISPONIBLES !== 'undefined') {
        console.log('Activos disponibles:', ACTIVOS_DISPONIBLES.length);
    }

    if (typeof ARTICULOS_DISPONIBLES !== 'undefined' && typeof ACTIVOS_DISPONIBLES !== 'undefined') {
        console.log('Creando OrdenCompraController...');
        window.ordenCompraController = new OrdenCompraController(
            ARTICULOS_DISPONIBLES,
            ACTIVOS_DISPONIBLES
        );
        console.log('Controlador creado y asignado a window.ordenCompraController');
    } else {
        console.error('Datos de artículos/activos no disponibles');
        console.error('ARTICULOS_DISPONIBLES:', typeof ARTICULOS_DISPONIBLES);
        console.error('ACTIVOS_DISPONIBLES:', typeof ACTIVOS_DISPONIBLES);
    }
});
