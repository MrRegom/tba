/**
 * Sistema de notificaciones global
 * Maneja SweetAlert2 y Modales de Bootstrap para mensajes del sistema
 */

document.addEventListener('DOMContentLoaded', function () {
    // Configuración base para SweetAlert2
    const swalConfig = {
        title: '¡Operación Exitosa!',
        icon: 'success',
        confirmButtonClass: 'btn btn-primary w-xs mt-2',
        buttonsStyling: false,
        timer: 3000,
        timerProgressBar: true
    };

    // Textos a filtrar (mensajes de login/logout que no queremos mostrar)
    const textosFiltrados = [
        'inició sesión',
        'cerró sesión',
        'Ha iniciado sesión',
        'Ha cerrado sesión',
        'inicio sesion',
        'cerro sesion'
    ];

    // 1. Procesar mensajes desde el contenedor central
    const systemMessagesContainer = document.getElementById('system-messages');
    if (!systemMessagesContainer) return;

    const messageDivs = systemMessagesContainer.querySelectorAll('div');
    if (messageDivs.length === 0) return;

    const modalElement = document.getElementById('mensajesModal');
    const modalBody = document.getElementById('mensajesModalBody');
    const modalHeader = document.getElementById('mensajesModalHeader');
    const modalTitle = document.getElementById('mensajesModalTitle');
    const modalIcon = document.getElementById('mensajesModalIcon');

    let tieneMensajesParaModal = false;
    let colorHeader = 'bg-primary';
    let textoTitulo = 'Mensaje';
    let htmlIcono = '<i class="ri-notification-line me-2"></i>';

    messageDivs.forEach(div => {
        const text = div.getAttribute('data-message');
        const tags = div.getAttribute('data-tags') || '';
        const textLower = text.toLowerCase();

        // Verificar si es mensaje ignorado
        const esMensajeIgnorado = textosFiltrados.some(filtro =>
            textLower.includes(filtro.toLowerCase())
        );
        if (esMensajeIgnorado) return;

        // RUTA A: SweetAlert (Solo para éxitos)
        if (tags.includes('success')) {
            Swal.fire({
                ...swalConfig,
                text: text
            });
            // No agregamos éxitos al modal para no saturar
            return;
        }

        // RUTA B: Modal de Bootstrap (Para errores, advertencias, info)
        tieneMensajesParaModal = true;

        // Configurar apariencia del modal según el primer mensaje no-éxito encontrado
        if (tags.includes('error') || tags.includes('danger')) {
            colorHeader = 'bg-danger';
            textoTitulo = 'Error';
            htmlIcono = '<i class="ri-error-warning-line me-2"></i>';
        } else if (tags.includes('warning')) {
            colorHeader = 'bg-warning';
            textoTitulo = 'Advertencia';
            htmlIcono = '<i class="ri-alert-line me-2"></i>';
        } else if (tags.includes('info')) {
            colorHeader = 'bg-info';
            textoTitulo = 'Información';
            htmlIcono = '<i class="ri-information-line me-2"></i>';
        }

        // Agregar mensaje al cuerpo del modal
        if (modalBody) {
            const p = document.createElement('p');
            p.className = 'mb-2 pb-2 border-bottom';
            p.textContent = text;
            modalBody.appendChild(p);
        }
    });

    // 2. Mostrar el modal si tiene contenido
    if (tieneMensajesParaModal && modalElement) {
        if (modalHeader) modalHeader.classList.add(colorHeader);
        if (modalTitle) modalTitle.textContent = textoTitulo;
        if (modalIcon) modalIcon.innerHTML = htmlIcono;

        const bootstrapModal = new bootstrap.Modal(modalElement);
        bootstrapModal.show();
    }
});
