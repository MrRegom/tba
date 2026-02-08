/**
 * Manejo de modales para órdenes de compra
 * Permite cargar el detalle de una orden en un modal vía AJAX
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const modal = document.getElementById('ordenesModal');
    const modalBody = document.getElementById('ordenesModalBody');
    const modalTitle = document.getElementById('ordenesModalLabel');

    if (!modal || !modalBody || !modalTitle) {
        console.error('Modal de órdenes no encontrado en el DOM');
        return;
    }

    // Bootstrap modal instance
    const bsModal = new bootstrap.Modal(modal);

    // Agregar event listeners a todos los enlaces con la clase 'ordenes-modal-link'
    const ordenesLinks = document.querySelectorAll('.ordenes-modal-link');

    ordenesLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const url = this.getAttribute('href');
            const title = this.getAttribute('data-modal-title') || 'Detalle de Orden';

            // Actualizar título del modal
            modalTitle.textContent = title;

            // Mostrar spinner de carga
            modalBody.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-2">Cargando información...</p>
                </div>
            `;

            // Mostrar el modal
            bsModal.show();

            // Cargar el contenido vía AJAX
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al cargar la orden');
                }
                return response.text();
            })
            .then(html => {
                modalBody.innerHTML = html;
            })
            .catch(error => {
                console.error('Error:', error);
                modalBody.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <h4 class="alert-heading">Error al cargar</h4>
                        <p>No se pudo cargar la información de la orden. Por favor, intente nuevamente.</p>
                        <hr>
                        <p class="mb-0">Si el problema persiste, contacte al administrador.</p>
                    </div>
                `;
            });
        });
    });

    // Limpiar el contenido del modal al cerrarlo
    modal.addEventListener('hidden.bs.modal', function() {
        modalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">Cargando información...</p>
            </div>
        `;
    });
});
