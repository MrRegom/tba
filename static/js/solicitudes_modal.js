(function () {
    'use strict';

    /**
     * Obtiene el valor de una cookie por su nombre
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function ensureModalContainer() {
        if (document.getElementById('solicitudModal')) return;

        // Fix focus trap for SweetAlert2 when opened from Bootstrap modal
        document.addEventListener('focusin', (e) => {
            if (e.target.closest(".swal2-container")) {
                e.stopImmediatePropagation();
            }
        });
        const container = document.createElement('div');
        container.innerHTML = `
                <div class="modal fade" id="solicitudModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="solicitudModalLabel">Detalle</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body" id="solicitudModalBody">
                                <!-- Contenido cargado por AJAX -->
                            </div>
                        </div>
                    </div>
                </div>`;
        document.body.appendChild(container);
    }

    // Delegar clicks en enlaces con clase .solicitudes-modal-link
    document.addEventListener('click', function (ev) {
        const a = ev.target.closest('a.solicitudes-modal-link');
        if (!a) return;
        ev.preventDefault();

        // Construir URL y forzar modal=1 para que la vista devuelva parcial
        try {
            const url = new URL(a.href, window.location.origin);
            url.searchParams.set('modal', '1');

            // Asegurar que exista el contenedor del modal; si no, crearlo dinámicamente
            ensureModalContainer();

            const modalEl = document.getElementById('solicitudModal');
            const modalBody = document.getElementById('solicitudModalBody');
            const modalTitle = document.getElementById('solicitudModalLabel');
            if (modalTitle && a.dataset.modalTitle) modalTitle.textContent = a.dataset.modalTitle;

            fetch(url.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(resp => resp.text())
                .then(html => {
                    modalBody.innerHTML = html;
                    // Inicializar comportamientos dentro del modal
                    initModalBindings(modalBody);
                    // Mostrar modal usando Bootstrap 5 si no está ya visible
                    let bsModal = bootstrap.Modal.getInstance(modalEl);
                    if (!bsModal) {
                        bsModal = new bootstrap.Modal(modalEl);
                    }

                    // Solo llamar a show() si el modal no se está mostrando
                    // (Si ya está abierto y navegamos internamente, no hace falta show())
                    if (!modalEl.classList.contains('show')) {
                        bsModal.show();
                    }
                })
                .catch(err => {
                    console.error('Error cargando modal:', err);
                });
        } catch (e) {
            console.error('URL inválida', e);
        }
    });

    // Inicializa bindings para formularios y botones dentro del modal
    function initModalBindings(root) {
        if (!root) return;

        // Si el contenido cargado tiene config de crear-solicitud, inicializar JS unificado
        if (root.querySelector('#solicitud-crear-config') && window.SolicitudCrear) {
            window.SolicitudCrear.init();
        }

        // Manejar submits de TODOS los formularios en el modal
        root.querySelectorAll('form').forEach(function (form) {
            form.addEventListener('submit', function (ev) {
                ev.preventDefault();
                submitFormViaAjax(form, root);
            });
        });

        // Botón para agregar filas al formset
        // Definir addFormRow y toggleSeccionActividad localmente para evitar mezclar JS en plantillas
        window.addFormRow = function () {
            const tbody = root.querySelector('#detalles-tbody');
            const totalForms = root.querySelector('#id_detalles-TOTAL_FORMS') || document.querySelector('#id_detalles-TOTAL_FORMS');
            if (!tbody || !totalForms) return;
            const formIdx = parseInt(totalForms.value);
            const lastRow = tbody.querySelector('.detalle-row:last-child');
            if (!lastRow) return;
            const newRow = lastRow.cloneNode(true);
            const html = newRow.innerHTML.replace(/detalles-(\d+)-/g, `detalles-${formIdx}-`);
            newRow.innerHTML = html;
            // Limpiar valores
            newRow.querySelectorAll('input, select, textarea').forEach(field => {
                if (field.type === 'checkbox' || field.type === 'radio') field.checked = false;
                else if (field.tagName === 'SELECT') field.selectedIndex = 0;
                else if (field.name && !field.name.includes('id')) field.value = '';
            });
            tbody.appendChild(newRow);
            totalForms.value = formIdx + 1;
        };

        window.toggleSeccionActividad = function () {
            const tipoSolicitudSelect = root.querySelector('select[name="tipo_solicitud"]') || document.querySelector('select[name="tipo_solicitud"]');
            const seccionActividad = root.querySelector('#seccion-actividad');
            if (!tipoSolicitudSelect || !seccionActividad) return;
            const selectedOption = tipoSolicitudSelect.options[tipoSolicitudSelect.selectedIndex];
            const selectedText = selectedOption ? selectedOption.text.toLowerCase() : '';
            if (selectedText.includes('materiales')) seccionActividad.style.display = '';
            else seccionActividad.style.display = 'none';
        };

        // Vincular cambio de tipo de solicitud
        const tipoSelect = root.querySelector('select[name="tipo_solicitud"]');
        if (tipoSelect) {
            tipoSelect.addEventListener('change', function () { window.toggleSeccionActividad(); });
            // Ejecutar inicial
            window.toggleSeccionActividad();
        }

        // Botón Comprar: Mueve la solicitud al estado COMPRAR
        root.querySelectorAll('.solicitud-comprar-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                const pk = this.dataset.pk;
                handleComprarSolicitud(pk, root);
            });
        });
    }

    /**
     * Gestiona el flujo de confirmación para enviar a compras
     * @param {number} pk - ID de la solicitud
     * @param {HTMLElement} root - Elemento raíz (modal)
     */
    function handleComprarSolicitud(pk, root) {
        if (!window.Swal) {
            if (confirm('¿Desea enviar esta solicitud al departamento de compras?')) {
                const notes = prompt('Notas adicionales para compras (opcional):');
                ejecutarAccionComprar(pk, notes, root);
            }
            return;
        }

        Swal.fire({
            title: '¿Enviar a Compras?',
            text: 'Se notificará al departamento de adquisiciones.',
            icon: 'question',
            input: 'textarea',
            inputLabel: 'Notas / Observaciones (opcional)',
            inputPlaceholder: 'Escriba aquí si hay algún detalle para compras...',
            showCancelButton: true,
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#0ab39c',
            cancelButtonColor: '#f06548',
            didOpen: () => {
                // Forzar foco al textarea para evitar que el modal de atrás lo robe
                const input = Swal.getInput();
                if (input) setTimeout(() => input.focus(), 100);
            },
            preConfirm: (notes) => {
                return notes || '';
            }
        }).then((result) => {
            if (result.isConfirmed) {
                ejecutarAccionComprar(pk, result.value, root);
            }
        });
    }

    /**
     * Ejecuta el POST definitivo hacia el backend para la acción comprar
     */
    function ejecutarAccionComprar(pk, notes, root) {
        const url = `/solicitudes/${pk}/comprar/?modal=1`;
        const formData = new FormData();
        formData.append('notas_compra', notes || '');

        // Obtener CSRF de la cookie (infalible para Django AJAX)
        const csrftoken = getCookie('csrftoken');

        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
            .then(resp => {
                if (!resp.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return resp.text();
            })
            .then(html => {
                // Si la respuesta es el detalle actualizado
                const modalBody = document.getElementById('solicitudModalBody');
                if (modalBody) {
                    modalBody.innerHTML = html;
                    initModalBindings(modalBody);
                }

                if (window.Swal) {
                    Swal.fire({
                        title: '¡Operación Exitosa!',
                        text: 'La solicitud ha sido enviada a compras correctamente.',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => {
                        // Refrescar la página para que el estado cambie en la lista principal
                        window.location.reload();
                    });
                } else {
                    window.location.reload();
                }
            })
            .catch(err => {
                console.error('Error al enviar a compras:', err);
                if (window.Swal) {
                    Swal.fire({
                        title: 'Error de Seguridad',
                        text: 'No se pudo validar la sesión (CSRF). Por favor, refresque la página e intente de nuevo.',
                        icon: 'error'
                    });
                } else {
                    alert('Error al enviar a compras. Por favor refresque la página.');
                }
            });
    }

    function submitFormViaAjax(form, root) {
        const action = form.getAttribute('action') || window.location.href;
        const method = (form.getAttribute('method') || 'POST').toUpperCase();
        const formData = new FormData(form);

        fetch(action + (action.includes('?') ? '&' : '?') + 'modal=1', {
            method: method,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
            .then(resp => resp.text())
            .then(html => {
                // Reemplazar el contenido del modal con la respuesta (que puede ser formulario con errores o detalle actualizado)
                const modalBody = document.getElementById('solicitudModalBody');
                if (modalBody) {
                    modalBody.innerHTML = html;
                    initModalBindings(modalBody);
                }
                // Si la respuesta contiene elementos que indiquen éxito, podríamos cerrar el modal y refrescar la lista.
                // Para mantener simpleza: si el HTML no contiene "form" asumimos que es vista de detalle -> refrescar lista
                if (!html.includes('<form')) {
                    // Cerrar modal y refrescar la página para ver cambios
                    const modalEl = document.getElementById('solicitudModal');
                    const bsModal = bootstrap.Modal.getInstance(modalEl);
                    if (bsModal) bsModal.hide();

                    // Refrescar la lista (o recargar la página) tras la animación
                    setTimeout(() => {
                        window.location.reload();
                    }, 300);
                }
            })
            .catch(err => {
                console.error('Error enviando formulario:', err);
            });
    }

    // Cleanup persistente para evitar fondos grises bloqueados
    document.addEventListener('hidden.bs.modal', function (event) {
        if (event.target.id === 'solicitudModal') {
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.paddingRight = '';
            document.body.style.overflow = '';
        }
    });

})();
