/**
 * Script para gestionar movimientos múltiples de activos con selección dinámica y confirmación PIN
 * 
 * Funcionalidades:
 * - Búsqueda AJAX de activos disponibles
 * - Selección múltiple con checkboxes
 * - Paginación de resultados
 * - Confirmación con PIN del responsable
 * - Creación de múltiples movimientos
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== ELEMENTOS DEL DOM ====================
    const busquedaInput = document.getElementById('busqueda-activos');
    const filtroCategoriaSelect = document.getElementById('filtro-categoria');
    const filtroEstadoSelect = document.getElementById('filtro-estado');
    const tablaActivosContainer = document.getElementById('tabla-activos-container');
    const tablaActivosBody = document.getElementById('tabla-activos-body');
    const mensajeInicial = document.getElementById('mensaje-inicial');
    const mensajeSinResultados = document.getElementById('mensaje-sin-resultados');
    const seleccionarTodosCheckbox = document.getElementById('seleccionar-todos');
    const cardActivosSeleccionados = document.getElementById('card-activos-seleccionados');
    const listaActivosSeleccionados = document.getElementById('lista-activos-seleccionados');
    const contadorSeleccionados = document.getElementById('contador-seleccionados');
    const seccionDetallesMovimiento = document.getElementById('seccion-detalles-movimiento');
    const btnRegistrarMovimiento = document.getElementById('btn-registrar-movimiento');
    const activosSeleccionadosInput = document.getElementById('activos_seleccionados');
    const formMovimiento = document.getElementById('form-movimiento');
    const pinConfirmadoInput = document.getElementById('pin_confirmado');
    const responsableSelect = document.getElementById('id_responsable_movimiento');
    const incluirResponsableCheckbox = document.getElementById('incluir_responsable');
    const campoResponsableContainer = document.getElementById('campo-responsable-container');
    
    // Modal PIN
    const pinConfirmationModal = new bootstrap.Modal(document.getElementById('pinConfirmationModal'));
    const pinInput = document.getElementById('pinInput');
    const pinError = document.getElementById('pinError');
    const confirmPinBtn = document.getElementById('confirmPinBtn');
    
    // ==================== ESTADO DE LA APLICACIÓN ====================
    let activosSeleccionados = new Map(); // Map<id, {codigo, nombre, categoria, estado, marca, numero_serie}>
    let paginaActual = 1;
    let totalPaginas = 1;
    let timeoutBusqueda = null;
    
    // ==================== FUNCIONES DE BÚSQUEDA ====================
    
    /**
     * Realiza la búsqueda de activos mediante AJAX
     */
    function buscarActivos(pagina = 1) {
        const termino = busquedaInput.value.trim();
        const categoria = filtroCategoriaSelect.value;
        const estado = filtroEstadoSelect.value;
        
        // Si no hay término de búsqueda, mostrar mensaje inicial
        if (!termino && !categoria && !estado) {
            tablaActivosContainer.style.display = 'none';
            mensajeSinResultados.style.display = 'none';
            mensajeInicial.style.display = 'block';
            return;
        }
        
        // Construir URL con parámetros
        const params = new URLSearchParams({
            q: termino,
            page: pagina,
            per_page: 10
        });
        
        if (categoria) params.append('categoria', categoria);
        if (estado) params.append('estado', estado);
        
        // Realizar petición AJAX
        fetch(`/activos/ajax/buscar-activos/?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarResultados(data);
                } else {
                    console.error('Error en la búsqueda:', data);
                }
            })
            .catch(error => {
                console.error('Error en la petición AJAX:', error);
                alert('Ocurrió un error al buscar activos. Intente nuevamente.');
            });
    }
    
    /**
     * Muestra los resultados de la búsqueda en la tabla
     */
    function mostrarResultados(data) {
        mensajeInicial.style.display = 'none';
        
        if (data.activos.length === 0) {
            tablaActivosContainer.style.display = 'none';
            mensajeSinResultados.style.display = 'block';
            return;
        }
        
        mensajeSinResultados.style.display = 'none';
        tablaActivosContainer.style.display = 'block';
        
        // Limpiar tabla
        tablaActivosBody.innerHTML = '';
        
        // Llenar tabla con resultados
        data.activos.forEach(activo => {
            const isSelected = activosSeleccionados.has(activo.id);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="text-center">
                    <input type="checkbox" class="form-check-input checkbox-activo" 
                           data-activo-id="${activo.id}"
                           data-activo-codigo="${activo.codigo}"
                           data-activo-nombre="${activo.nombre}"
                           data-activo-categoria="${activo.categoria}"
                           data-activo-estado="${activo.estado}"
                           data-activo-estado-id="${activo.estado_id || ''}"
                           data-activo-marca="${activo.marca}"
                           data-activo-serie="${activo.numero_serie}"
                           ${isSelected ? 'checked' : ''}>
                </td>
                <td><strong>${activo.codigo}</strong></td>
                <td>${activo.nombre}</td>
                <td><span class="badge bg-secondary">${activo.categoria}</span></td>
                <td><span class="badge bg-info">${activo.estado}</span></td>
                <td>${activo.marca || '-'}</td>
                <td><small class="text-muted">${activo.numero_serie}</small></td>
            `;
            tablaActivosBody.appendChild(row);
        });
        
        // Actualizar paginación
        paginaActual = data.pagina_actual;
        totalPaginas = data.total_paginas;
        actualizarPaginacion(data);
        
        // Agregar event listeners a los checkboxes
        document.querySelectorAll('.checkbox-activo').forEach(checkbox => {
            checkbox.addEventListener('change', manejarSeleccionActivo);
        });
        
        // Actualizar estado del checkbox "Seleccionar todos"
        actualizarCheckboxSeleccionarTodos();
    }
    
    /**
     * Actualiza la paginación
     */
    function actualizarPaginacion(data) {
        const infoPaginacion = document.getElementById('info-paginacion');
        const paginacionActivos = document.getElementById('paginacion-activos');
        
        // Información de paginación
        const inicio = (data.pagina_actual - 1) * 10 + 1;
        const fin = Math.min(data.pagina_actual * 10, data.total);
        infoPaginacion.textContent = `Mostrando ${inicio}-${fin} de ${data.total} activos`;
        
        // Botones de paginación
        paginacionActivos.innerHTML = '';
        
        // Botón anterior
        const liAnterior = document.createElement('li');
        liAnterior.className = `page-item ${!data.tiene_anterior ? 'disabled' : ''}`;
        liAnterior.innerHTML = `<a class="page-link" href="#" data-pagina="${data.pagina_actual - 1}">Anterior</a>`;
        paginacionActivos.appendChild(liAnterior);
        
        // Números de página
        for (let i = 1; i <= data.total_paginas; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === data.pagina_actual ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#" data-pagina="${i}">${i}</a>`;
            paginacionActivos.appendChild(li);
        }
        
        // Botón siguiente
        const liSiguiente = document.createElement('li');
        liSiguiente.className = `page-item ${!data.tiene_siguiente ? 'disabled' : ''}`;
        liSiguiente.innerHTML = `<a class="page-link" href="#" data-pagina="${data.pagina_actual + 1}">Siguiente</a>`;
        paginacionActivos.appendChild(liSiguiente);
        
        // Event listeners para paginación
        paginacionActivos.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                if (!this.parentElement.classList.contains('disabled') && 
                    !this.parentElement.classList.contains('active')) {
                    const pagina = parseInt(this.dataset.pagina);
                    buscarActivos(pagina);
                }
            });
        });
    }
    
    // ==================== FUNCIONES DE SELECCIÓN ====================
    
    /**
     * Maneja la selección/deselección de un activo
     */
    function manejarSeleccionActivo(event) {
        const checkbox = event.target;
        const activoId = parseInt(checkbox.dataset.activoId);
        
        if (checkbox.checked) {
            // Agregar a seleccionados
            activosSeleccionados.set(activoId, {
                codigo: checkbox.dataset.activoCodigo,
                nombre: checkbox.dataset.activoNombre,
                categoria: checkbox.dataset.activoCategoria,
                estado: checkbox.dataset.activoEstado,
                estado_id: checkbox.dataset.activoEstadoId || null,
                marca: checkbox.dataset.activoMarca,
                numero_serie: checkbox.dataset.activoSerie
            });
        } else {
            // Remover de seleccionados
            activosSeleccionados.delete(activoId);
        }
        
        actualizarListaSeleccionados();
        actualizarCheckboxSeleccionarTodos();
    }
    
    /**
     * Actualiza la lista visual de activos seleccionados
     */
    function actualizarListaSeleccionados() {
        const cantidad = activosSeleccionados.size;
        contadorSeleccionados.textContent = cantidad;
        
        if (cantidad === 0) {
            cardActivosSeleccionados.style.display = 'none';
            seccionDetallesMovimiento.style.display = 'none';
            btnRegistrarMovimiento.disabled = true;
            return;
        }
        
        cardActivosSeleccionados.style.display = 'block';
        seccionDetallesMovimiento.style.display = 'block';
        btnRegistrarMovimiento.disabled = false;
        
        // Llenar lista
        listaActivosSeleccionados.innerHTML = '';
        activosSeleccionados.forEach((activo, id) => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <strong>${activo.codigo}</strong> - ${activo.nombre}
                    <br>
                    <small class="text-muted">
                        ${activo.categoria} | 
                        <span class="badge bg-info">Estado Actual: ${activo.estado}</span> | 
                        S/N: ${activo.numero_serie}
                    </small>
                </div>
                <button type="button" class="btn btn-sm btn-danger btn-quitar-activo" data-activo-id="${id}">
                    <i class="ri-close-line"></i>
                </button>
            `;
            listaActivosSeleccionados.appendChild(item);
        });
        
        // Event listeners para botones de quitar
        document.querySelectorAll('.btn-quitar-activo').forEach(btn => {
            btn.addEventListener('click', function() {
                const activoId = parseInt(this.dataset.activoId);
                activosSeleccionados.delete(activoId);
                
                // Desmarcar checkbox si está visible
                const checkbox = document.querySelector(`.checkbox-activo[data-activo-id="${activoId}"]`);
                if (checkbox) checkbox.checked = false;
                
                actualizarListaSeleccionados();
                actualizarCheckboxSeleccionarTodos();
            });
        });
        
        // Actualizar input hidden con IDs seleccionados
        activosSeleccionadosInput.value = Array.from(activosSeleccionados.keys()).join(',');
        
        // Auto-rellenar estado nuevo si todos tienen el mismo estado
        autoRellenarEstadoNuevo();
    }
    
    /**
     * Auto-rellena el campo "Nuevo Estado" con el estado actual si todos los activos
     * seleccionados tienen el mismo estado.
     */
    function autoRellenarEstadoNuevo() {
        const estadoNuevoSelect = document.getElementById('id_estado_nuevo');
        if (!estadoNuevoSelect || activosSeleccionados.size === 0) {
            return;
        }
        
        // Obtener todos los estados de los activos seleccionados
        const estadosIds = Array.from(activosSeleccionados.values())
            .map(activo => activo.estado_id)
            .filter(id => id !== null && id !== undefined && id !== '');
        
        if (estadosIds.length === 0) {
            // Si no hay estados, no hacer nada
            return;
        }
        
        // Verificar si todos tienen el mismo estado
        const primerEstadoId = estadosIds[0];
        const todosMismoEstado = estadosIds.every(id => id == primerEstadoId);
        
        if (todosMismoEstado && primerEstadoId) {
            // Si todos tienen el mismo estado, auto-rellenar
            const estadoAnterior = estadoNuevoSelect.value;
            estadoNuevoSelect.value = primerEstadoId;
            
            // Mostrar mensaje informativo si cambió el valor
            const mensajeEstadoActual = document.getElementById('mensaje-estado-actual');
            if (mensajeEstadoActual) {
                if (estadoAnterior !== primerEstadoId) {
                    mensajeEstadoActual.classList.remove('d-none');
                    // Ocultar el mensaje después de 5 segundos
                    setTimeout(() => {
                        mensajeEstadoActual.classList.add('d-none');
                    }, 5000);
                } else {
                    mensajeEstadoActual.classList.add('d-none');
                }
            }
            
            // Disparar evento change para que otros scripts puedan reaccionar
            estadoNuevoSelect.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            // Si tienen estados diferentes, limpiar el campo solo si estaba vacío
            // (no sobrescribir si el usuario ya seleccionó algo)
            if (!estadoNuevoSelect.value) {
                estadoNuevoSelect.value = '';
            }
            
            // Ocultar mensaje informativo
            const mensajeEstadoActual = document.getElementById('mensaje-estado-actual');
            if (mensajeEstadoActual) {
                mensajeEstadoActual.classList.add('d-none');
            }
        }
    }
    
    /**
     * Actualiza el estado del checkbox "Seleccionar todos"
     */
    function actualizarCheckboxSeleccionarTodos() {
        const checkboxes = document.querySelectorAll('.checkbox-activo');
        const checkboxesMarcados = document.querySelectorAll('.checkbox-activo:checked');
        
        if (checkboxes.length === 0) {
            seleccionarTodosCheckbox.checked = false;
            seleccionarTodosCheckbox.indeterminate = false;
            return;
        }
        
        if (checkboxesMarcados.length === 0) {
            seleccionarTodosCheckbox.checked = false;
            seleccionarTodosCheckbox.indeterminate = false;
        } else if (checkboxesMarcados.length === checkboxes.length) {
            seleccionarTodosCheckbox.checked = true;
            seleccionarTodosCheckbox.indeterminate = false;
        } else {
            seleccionarTodosCheckbox.checked = false;
            seleccionarTodosCheckbox.indeterminate = true;
        }
    }
    
    // ==================== FUNCIONES DE CONFIRMACIÓN PIN ====================
    
    /**
     * Muestra el modal de confirmación con PIN
     */
    function mostrarModalConfirmacionPIN() {
        // Verificar si se incluye responsable
        const incluyeResponsable = incluirResponsableCheckbox ? incluirResponsableCheckbox.checked : false;
        
        if (!incluyeResponsable) {
            // Si no se incluye responsable, enviar formulario directamente
            formMovimiento.submit();
            return;
        }
        
        // Verificar que el elemento responsable existe
        if (!responsableSelect) {
            // Si no existe el campo responsable, enviar formulario directamente
            formMovimiento.submit();
            return;
        }
        
        const responsableId = responsableSelect.value;
        
        if (!responsableId) {
            // Si no hay responsable seleccionado, enviar formulario directamente
            formMovimiento.submit();
            return;
        }
        
        // Llenar información del modal
        const responsableNombre = responsableSelect.options[responsableSelect.selectedIndex]?.text || 'No especificado';
        document.getElementById('modal-cantidad-activos').textContent = activosSeleccionados.size;
        document.getElementById('modal-responsable-info').textContent = responsableNombre;
        document.getElementById('modal-responsable-nombre').textContent = responsableNombre;
        
        // Llenar lista de activos en el modal
        const modalListaActivos = document.getElementById('modal-lista-activos');
        modalListaActivos.innerHTML = '<ul class="list-unstyled mb-0">';
        activosSeleccionados.forEach(activo => {
            modalListaActivos.innerHTML += `<li><i class="ri-checkbox-circle-line text-success me-2"></i>${activo.codigo} - ${activo.nombre}</li>`;
        });
        modalListaActivos.innerHTML += '</ul>';
        
        // Limpiar y mostrar modal
        pinInput.value = '';
        pinError.textContent = '';
        confirmPinBtn.disabled = false;
        pinConfirmationModal.show();
    }
    
    /**
     * Valida el PIN mediante AJAX
     */
    function validarPIN() {
        const pin = pinInput.value;
        
        // Verificar que el elemento responsable existe
        if (!responsableSelect) {
            // Si no existe, enviar formulario directamente
            formMovimiento.submit();
            return;
        }
        
        const responsableId = responsableSelect.value;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        if (pin.length !== 4 || !/^\d{4}$/.test(pin)) {
            pinError.textContent = 'El PIN debe ser de 4 dígitos numéricos.';
            return;
        }
        
        pinError.textContent = '';
        confirmPinBtn.disabled = true;
        confirmPinBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Validando...';
        
        // Realizar validación AJAX
        fetch('/activos/ajax/validar-pin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                'responsable_id': responsableId,
                'pin': pin
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // PIN válido - marcar como confirmado y enviar formulario
                pinConfirmadoInput.value = 'true';
                pinConfirmationModal.hide();
                formMovimiento.submit();
            } else {
                // PIN inválido - mostrar error
                pinError.textContent = data.message;
                confirmPinBtn.disabled = false;
                confirmPinBtn.innerHTML = '<i class="ri-check-line me-1"></i> Confirmar';
                
                if (data.bloqueado) {
                    confirmPinBtn.disabled = true;
                }
            }
        })
        .catch(error => {
            console.error('Error en la validación del PIN:', error);
            pinError.textContent = 'Ocurrió un error al validar el PIN. Intente de nuevo.';
            confirmPinBtn.disabled = false;
            confirmPinBtn.innerHTML = '<i class="ri-check-line me-1"></i> Confirmar';
        });
    }
    
    // ==================== EVENT LISTENERS ====================
    
    // Búsqueda con debounce
    busquedaInput.addEventListener('input', function() {
        clearTimeout(timeoutBusqueda);
        timeoutBusqueda = setTimeout(() => {
            buscarActivos(1);
        }, 500);
    });
    
    // Filtros
    filtroCategoriaSelect.addEventListener('change', () => buscarActivos(1));
    filtroEstadoSelect.addEventListener('change', () => buscarActivos(1));
    
    // Seleccionar/deseleccionar todos
    seleccionarTodosCheckbox.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.checkbox-activo');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
            const event = new Event('change');
            checkbox.dispatchEvent(event);
        });
    });
    
    // ==================== MANEJO DEL CHECKBOX RESPONSABLE ====================
    
    /**
     * Maneja el cambio del checkbox "Incluir responsable"
     */
    if (incluirResponsableCheckbox && campoResponsableContainer) {
        incluirResponsableCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // Mostrar campo responsable
                campoResponsableContainer.style.display = 'block';
                responsableSelect.disabled = false;
            } else {
                // Ocultar campo responsable y limpiar valor
                campoResponsableContainer.style.display = 'none';
                responsableSelect.disabled = true;
                responsableSelect.value = '';
            }
        });
        
        // Ejecutar al cargar para establecer estado inicial
        if (!incluirResponsableCheckbox.checked) {
            campoResponsableContainer.style.display = 'none';
            responsableSelect.disabled = true;
        }
    }
    
    // Submit del formulario
    formMovimiento.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Validar que haya activos seleccionados
        if (activosSeleccionados.size === 0) {
            alert('Debe seleccionar al menos un activo para registrar el movimiento.');
            return;
        }
        
        // Validar si se incluye responsable
        const incluyeResponsable = incluirResponsableCheckbox ? incluirResponsableCheckbox.checked : false;
        
        if (!incluyeResponsable) {
            // Si no incluye responsable, preguntar confirmación
            const confirmacion = confirm(
                '⚠️ ¿Está seguro de que este movimiento NO requiere un responsable?\n\n' +
                'Si el movimiento debería tener un responsable, marque la opción "Incluir responsable" antes de continuar.\n\n' +
                '¿Desea continuar sin responsable?'
            );
            
            if (!confirmacion) {
                // Si cancela, mostrar el checkbox y campo responsable
                if (incluirResponsableCheckbox) {
                    incluirResponsableCheckbox.checked = true;
                    if (campoResponsableContainer) {
                        campoResponsableContainer.style.display = 'block';
                        responsableSelect.disabled = false;
                    }
                    // Scroll al campo responsable
                    campoResponsableContainer?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }
            
            // Si confirma, limpiar el campo responsable y enviar formulario
            if (responsableSelect) {
                responsableSelect.value = '';
            }
            this.submit();
            return;
        }
        
        // Si incluye responsable, validar que esté seleccionado
        if (responsableSelect && !responsableSelect.value) {
            alert('Debe seleccionar un responsable para este movimiento.');
            responsableSelect.focus();
            return;
        }
        
        // Si el PIN ya fue confirmado, enviar formulario
        if (pinConfirmadoInput && pinConfirmadoInput.value === 'true') {
            this.submit();
            return;
        }
        
        // Mostrar modal de confirmación PIN
        mostrarModalConfirmacionPIN();
    });
    
    // Confirmar PIN
    confirmPinBtn.addEventListener('click', validarPIN);
    
    // Permitir Enter en el input del PIN
    pinInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            validarPIN();
        }
    });
    
    // Resetear modal cuando se cierra
    document.getElementById('pinConfirmationModal').addEventListener('hidden.bs.modal', function() {
        pinInput.value = '';
        pinError.textContent = '';
        confirmPinBtn.disabled = false;
        confirmPinBtn.innerHTML = '<i class="ri-check-line me-1"></i> Confirmar';
    });
});


