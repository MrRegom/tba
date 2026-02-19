/**
 * Funcionalidad unificada para crear solicitudes (artículos y bienes)
 * @module solicitudes/crear-solicitud
 * @description Configurado via data-* attributes en #solicitud-crear-config
 */
(function () {
    'use strict';

    var itemsSeleccionados = [];
    var contadorFilas = 0;
    var config = {};
    var selectorModal = null;

    function leerConfig() {
        var el = document.getElementById('solicitud-crear-config');
        if (!el) return false;
        config = {
            itemType: el.dataset.itemType || 'articulo',
            itemIdField: el.dataset.itemIdField || 'articulo_id',
            tableId: el.dataset.tableId || 'tabla-articulos',
            tbodyId: el.dataset.tbodyId || 'tbody-articulos',
            emptyStateId: el.dataset.emptyStateId || 'sin-articulos',
            btnAgregarId: el.dataset.btnAgregarId || 'btn-agregar-articulo',
            hasUnidad: el.dataset.hasUnidad === 'true',
            minStep: el.dataset.minStep || '1',
            minValue: el.dataset.minValue || '1',
            useInlineSelector: el.dataset.useInlineSelector === 'true',
            modalSelectorId: el.dataset.modalSelectorId || '',
            collapseId: el.dataset.collapseId || '',
            emptyMessage: el.dataset.emptyMessage || 'No hay items agregados.',
            duplicateMessage: el.dataset.duplicateMessage || 'Este item ya ha sido agregado',
            validationMessage: el.dataset.validationMessage || 'Debe agregar al menos un item',
            qtyValidationMessage: el.dataset.qtyValidationMessage || 'Todas las cantidades deben ser mayores a cero'
        };
        return true;
    }

    function inicializar() {
        if (!leerConfig()) return;

        itemsSeleccionados = [];
        contadorFilas = 0;

        // Selector: modal o inline collapse
        if (!config.useInlineSelector && config.modalSelectorId) {
            var modalEl = document.getElementById(config.modalSelectorId);
            if (modalEl) {
                selectorModal = new bootstrap.Modal(modalEl);
            }
        }

        setupEventListeners();
        actualizarVisualizacion();
    }

    function setupEventListeners() {
        // Boton agregar
        var btnAgregar = document.getElementById(config.btnAgregarId);
        if (btnAgregar) {
            btnAgregar.addEventListener('click', function () {
                if (config.useInlineSelector && config.collapseId) {
                    var collapseEl = document.getElementById(config.collapseId);
                    if (collapseEl) {
                        var bsCollapse = bootstrap.Collapse.getOrCreateInstance(collapseEl);
                        bsCollapse.toggle();
                    }
                } else if (selectorModal) {
                    selectorModal.show();
                }
            });
        }

        // Buscador
        var inputBuscar = document.getElementById('buscar-item');
        if (inputBuscar) {
            inputBuscar.addEventListener('input', filtrarItems);
        }

        // Botones seleccionar (delegacion en contenedor)
        var listaTbody = document.getElementById('tbody-lista-items');
        if (listaTbody) {
            listaTbody.addEventListener('click', function (e) {
                var btn = e.target.closest('.btn-seleccionar-item');
                if (btn) seleccionarItem(btn);
            });
        }

        // Submit formulario
        var form = document.getElementById('formSolicitud');
        if (form) {
            form.addEventListener('submit', validarYEnviarFormulario);
        }
    }

    function filtrarItems(e) {
        var termino = e.target.value.toLowerCase();
        var filas = document.querySelectorAll('#tbody-lista-items tr');
        filas.forEach(function (fila) {
            var codigo = (fila.dataset.itemCodigo || '').toLowerCase();
            var nombre = (fila.dataset.itemNombre || '').toLowerCase();
            fila.style.display = (codigo.includes(termino) || nombre.includes(termino)) ? '' : 'none';
        });
    }

    function seleccionarItem(btn) {
        var fila = btn.closest('tr');
        var itemId = parseInt(fila.dataset.itemId);

        if (itemsSeleccionados.some(function (i) { return i.id === itemId; })) {
            mostrarAlerta(config.duplicateMessage, 'warning');
            return;
        }

        var item = {
            id: itemId,
            codigo: fila.dataset.itemCodigo || '',
            nombre: fila.dataset.itemNombre || '',
            unidad: fila.dataset.itemUnidad || ''
        };

        itemsSeleccionados.push(item);
        agregarFila(item);

        // Cerrar selector
        if (config.useInlineSelector && config.collapseId) {
            var collapseEl = document.getElementById(config.collapseId);
            if (collapseEl) {
                var bsCollapse = bootstrap.Collapse.getOrCreateInstance(collapseEl);
                bsCollapse.hide();
            }
        } else if (selectorModal) {
            selectorModal.hide();
        }

        // Limpiar busqueda
        var inputBuscar = document.getElementById('buscar-item');
        if (inputBuscar) {
            inputBuscar.value = '';
            document.querySelectorAll('#tbody-lista-items tr').forEach(function (tr) {
                tr.style.display = '';
            });
        }
    }

    function agregarFila(item) {
        var tbody = document.getElementById(config.tbodyId);
        if (!tbody) return;

        var fila = document.createElement('tr');
        fila.dataset.itemId = item.id;
        fila.dataset.filaId = contadorFilas;

        var unidadHtml = config.hasUnidad && item.unidad
            ? '<small class="text-muted">' + item.unidad + '</small>'
            : '';

        fila.innerHTML =
            '<td>' +
            '<strong>' + item.nombre + '</strong><br>' +
            '<small class="text-muted">C\u00F3digo: ' + item.codigo + '</small>' +
            '<input type="hidden" name="detalles[' + contadorFilas + '][' + config.itemIdField + ']" value="' + item.id + '">' +
            '</td>' +
            '<td>' +
            '<input type="number" name="detalles[' + contadorFilas + '][cantidad_solicitada]"' +
            ' class="form-control form-control-sm"' +
            ' min="' + config.minValue + '"' +
            ' step="' + config.minStep + '"' +
            ' required placeholder="0">' +
            unidadHtml +
            '</td>' +
            '<td>' +
            '<input type="text" name="detalles[' + contadorFilas + '][observaciones]"' +
            ' class="form-control form-control-sm" placeholder="Opcional">' +
            '</td>' +
            '<td class="text-center">' +
            '<button type="button" class="btn btn-sm btn-danger btn-eliminar-fila" data-fila-id="' + contadorFilas + '">' +
            '<i class="ri-delete-bin-line"></i>' +
            '</button>' +
            '</td>';

        tbody.appendChild(fila);
        fila.querySelector('.btn-eliminar-fila').addEventListener('click', eliminarFila);
        contadorFilas++;
        actualizarVisualizacion();
    }

    function eliminarFila(e) {
        var filaId = e.target.closest('button').dataset.filaId;
        var fila = document.querySelector('tr[data-fila-id="' + filaId + '"]');
        if (!fila) return;
        var itemId = parseInt(fila.dataset.itemId);
        itemsSeleccionados = itemsSeleccionados.filter(function (i) { return i.id !== itemId; });
        fila.remove();
        actualizarVisualizacion();
    }

    function actualizarVisualizacion() {
        var tabla = document.getElementById(config.tableId);
        var emptyState = document.getElementById(config.emptyStateId);

        // Búsqueda de respaldo si el ID no se encuentra: buscar el div de mensaje dentro del mismo contenedor que la tabla
        if (!emptyState && tabla) {
            var cardBody = tabla.closest('.card-body');
            if (cardBody) {
                emptyState = cardBody.querySelector('.text-center.text-muted.py-4');
            }
        }

        var tablaContainer = tabla ? tabla.closest('.table-responsive') : null;

        if (itemsSeleccionados.length === 0) {
            if (tabla) tabla.classList.add('d-none');
            if (tablaContainer) tablaContainer.classList.add('d-none');
            if (emptyState) {
                emptyState.classList.remove('d-none');
                emptyState.style.setProperty('display', 'block', 'important');
            }

            // Recrear si es necesario
            if (!emptyState && tabla) {
                var cardBody = tabla.closest('.card-body');
                if (cardBody) {
                    var div = document.createElement('div');
                    div.id = config.emptyStateId;
                    div.className = 'text-center text-muted py-4';
                    div.innerHTML = '<i class="ri-inbox-line" style="font-size: 3rem;"></i>' +
                        '<p class="mb-0">' + config.emptyMessage + '</p>';
                    cardBody.appendChild(div);
                }
            }
        } else {
            // Ocultar mensaje de "no hay items" - FORZAR con d-none y style !important
            if (emptyState) {
                emptyState.classList.add('d-none');
                emptyState.style.setProperty('display', 'none', 'important');
            }

            // Mostrar tabla y su contenedor
            if (tablaContainer) {
                tablaContainer.classList.remove('d-none');
                tablaContainer.style.setProperty('display', 'block', 'important');
            }
            if (tabla) {
                tabla.classList.remove('d-none');
                tabla.style.setProperty('display', 'table', 'important');
            }
        }
    }

    function validarYEnviarFormulario(e) {
        if (itemsSeleccionados.length === 0) {
            e.preventDefault();
            mostrarAlerta(config.validationMessage, 'warning');
            return false;
        }

        var inputs = document.querySelectorAll('input[name^="detalles"][name$="[cantidad_solicitada]"]');
        var todasValidas = true;
        inputs.forEach(function (input) {
            var valor = parseFloat(input.value);
            if (!valor || valor <= 0) {
                todasValidas = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        if (!todasValidas) {
            e.preventDefault();
            mostrarAlerta(config.qtyValidationMessage, 'warning');
            return false;
        }
        return true;
    }

    function mostrarAlerta(mensaje, tipo) {
        var alerta = document.createElement('div');
        alerta.className = 'alert alert-' + (tipo || 'info') + ' alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alerta.style.zIndex = '9999';
        alerta.innerHTML = mensaje +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
        document.body.appendChild(alerta);
        setTimeout(function () { alerta.remove(); }, 5000);
    }

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

    // Exponer para re-inicialización desde solicitudes_modal.js
    window.SolicitudCrear = { init: inicializar };

})();
