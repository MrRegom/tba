/**
 * Modal AJAX para módulo de bodega (entregas, recepciones, movimientos).
 * Soporta: detalle en modal, formularios de creación en modal,
 * modales anidados (selector de items), y envío AJAX de formularios.
 */
(function(){
    'use strict';

    /* ── helpers ─────────────────────────────────────────────── */

    function ensureModalContainer(){
        if(document.getElementById('bodegaModal')) return;
        var container = document.createElement('div');
        container.innerHTML =
            '<div class="modal fade" id="bodegaModal" tabindex="-1" aria-hidden="true">' +
            '  <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">' +
            '    <div class="modal-content">' +
            '      <div class="modal-header">' +
            '        <h5 class="modal-title" id="bodegaModalLabel">Detalle</h5>' +
            '        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
            '      </div>' +
            '      <div class="modal-body" id="bodegaModalBody"></div>' +
            '    </div>' +
            '  </div>' +
            '</div>';
        document.body.appendChild(container);
    }

    /** Limpia modales anidados que se movieron previamente al body. */
    function cleanupNestedModals(){
        document.querySelectorAll('.bodega-nested-modal-moved').forEach(function(el){
            var bsInstance = bootstrap.Modal.getInstance(el);
            if(bsInstance) bsInstance.dispose();
            el.remove();
        });
    }

    /**
     * Después de inyectar HTML en el modal body:
     * 1. Mueve modales anidados (.bodega-nested-modal) al body
     *    para evitar el problema de modal-dentro-de-modal.
     * 2. Ejecuta <script> tags (inline y src).
     */
    function processModalContent(modalBody){
        // 1. Mover modales anidados al body con z-index superior
        var nested = modalBody.querySelectorAll('.bodega-nested-modal');
        nested.forEach(function(nestedModal){
            nestedModal.classList.remove('bodega-nested-modal');
            nestedModal.classList.add('bodega-nested-modal-moved');
            nestedModal.style.zIndex = '1060';
            document.body.appendChild(nestedModal);
        });

        // 2. Ejecutar scripts
        var scripts = modalBody.querySelectorAll('script');
        scripts.forEach(function(oldScript){
            var newScript = document.createElement('script');
            if(oldScript.src){
                newScript.src = oldScript.src;
            } else {
                newScript.textContent = oldScript.textContent;
            }
            oldScript.parentNode.removeChild(oldScript);
            document.body.appendChild(newScript);
        });
    }

    /**
     * Intercepta el submit de formularios dentro del modal bodega
     * y los envía vía AJAX. En caso de éxito recarga la página.
     * En caso de error de validación, re-renderiza el formulario.
     */
    function bindFormSubmit(modalBody, modalEl){
        var form = modalBody.querySelector('form');
        if(!form) return;

        form.addEventListener('submit', function(ev){
            ev.preventDefault();
            var submitBtn = form.querySelector('button[type="submit"]');
            if(submitBtn){
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Procesando...';
            }

            var formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(function(resp){
                if(resp.redirected){
                    // Éxito: el servidor redirigió (form_valid normal).
                    // Cerrar modal y recargar la página.
                    var bsModal = bootstrap.Modal.getInstance(modalEl);
                    if(bsModal) bsModal.hide();
                    cleanupNestedModals();
                    window.location.reload();
                    return null;
                }
                return resp.text().then(function(html){
                    return { status: resp.status, html: html };
                });
            })
            .then(function(result){
                if(!result) return; // fue redirect
                if(result.status >= 200 && result.status < 300){
                    // Respuesta OK sin redirect - puede ser JSON success
                    try {
                        var data = JSON.parse(result.html);
                        if(data.success){
                            var bsModal = bootstrap.Modal.getInstance(modalEl);
                            if(bsModal) bsModal.hide();
                            cleanupNestedModals();
                            window.location.reload();
                            return;
                        }
                    } catch(e){ /* no es JSON, es HTML */ }
                }
                // Re-renderizar formulario con errores
                cleanupNestedModals();
                modalBody.innerHTML = result.html;
                processModalContent(modalBody);
                bindFormSubmit(modalBody, modalEl);
            })
            .catch(function(err){
                console.error('Error enviando formulario bodega:', err);
                if(submitBtn){
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="ri-save-line"></i> Guardar';
                }
            });
        });
    }

    /* ── evento click delegado ───────────────────────────────── */

    document.addEventListener('click', function(ev){
        var a = ev.target.closest('a.bodega-modal-link');
        if(!a) return;
        ev.preventDefault();

        try {
            var url = new URL(a.href, window.location.origin);
            url.searchParams.set('modal','1');

            ensureModalContainer();
            cleanupNestedModals();

            var modalEl = document.getElementById('bodegaModal');
            var modalBody = document.getElementById('bodegaModalBody');
            var modalTitle = document.getElementById('bodegaModalLabel');
            if(modalTitle && a.dataset.modalTitle) modalTitle.textContent = a.dataset.modalTitle;

            // Loading state
            modalBody.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Cargando...</p></div>';
            var bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
            bsModal.show();

            fetch(url.toString(), { headers: {'X-Requested-With': 'XMLHttpRequest'} })
                .then(function(resp){ return resp.text(); })
                .then(function(html){
                    modalBody.innerHTML = html;
                    processModalContent(modalBody);
                    bindFormSubmit(modalBody, modalEl);
                })
                .catch(function(err){
                    modalBody.innerHTML = '<div class="alert alert-danger">Error al cargar el contenido.</div>';
                    console.error('Error cargando modal bodega:', err);
                });
        } catch(e) {
            console.error('URL inválida', e);
        }
    });

    /* ── cleanup al cerrar modal ─────────────────────────────── */

    document.addEventListener('hidden.bs.modal', function(ev){
        if(ev.target.id === 'bodegaModal'){
            cleanupNestedModals();
            var modalBody = document.getElementById('bodegaModalBody');
            if(modalBody) modalBody.innerHTML = '';
        }
    });

})();
