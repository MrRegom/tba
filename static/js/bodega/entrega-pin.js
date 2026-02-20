/**
 * Módulo para manejo de validación de PIN en entregas de bodega
 */
var EntregaPin = {
    modal: null,
    pinInput: null,
    pinError: null,
    confirmBtn: null,
    onSuccessCallback: null,
    usuarioId: null,
    intentos: 3,

    init() {
        const modalEl = document.getElementById('pinConfirmationModal');
        if (!modalEl) return;

        this.modal = new bootstrap.Modal(modalEl);
        this.pinInput = document.getElementById('pinInput');
        this.pinError = document.getElementById('pinError');
        this.confirmBtn = document.getElementById('confirmPinBtn');

        // Event listener para el botón de confirmar
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.validarPIN());
        }

        // Event listener para la tecla Enter en el input
        if (this.pinInput) {
            this.pinInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.validarPIN();
                }
            });

            // Limpiar error al escribir
            this.pinInput.addEventListener('input', () => {
                this.pinError.textContent = '';
                this.pinInput.classList.remove('is-invalid');
            });
        }

        // Limpiar al cerrar modal
        modalEl.addEventListener('hidden.bs.modal', () => {
            if (this.pinInput) this.pinInput.value = '';
            if (this.pinError) this.pinError.textContent = '';
            if (this.pinInput) this.pinInput.classList.remove('is-invalid');
            document.getElementById('pinIntentos').classList.add('d-none');
        });
    },

    /**
     * Muestra el modal de PIN
     * @param {number} usuarioId ID del usuario receptor
     * @param {string} usuarioNombre Nombre visible del receptor
     * @param {function} onSuccess Función a ejecutar si el PIN es válido
     */
    mostrarModal(usuarioId, usuarioNombre, onSuccess) {
        if (!this.modal) {
            this.init();
        }

        this.usuarioId = usuarioId;
        this.onSuccessCallback = onSuccess;
        this.intentos = 3;

        document.getElementById('modal-receptor-nombre').textContent = usuarioNombre || '---';
        document.getElementById('intentos-count').textContent = '3';
        document.getElementById('pinIntentos').classList.add('d-none');

        this.modal.show();

        // Enfocar input después de mostrar modal
        setTimeout(() => {
            if (this.pinInput) this.pinInput.focus();
        }, 500);
    },

    /**
     * Valida el PIN mediante AJAX
     */
    async validarPIN() {
        const pin = this.pinInput.value.trim();

        if (!pin || pin.length !== 4 || !/^\d+$/.test(pin)) {
            this.mostrarError('El PIN debe ser de 4 dígitos numéricos.');
            return;
        }

        this.setLoading(true);

        try {
            const formData = new FormData();
            formData.append('usuario_id', this.usuarioId);
            formData.append('pin', pin);

            const response = await fetch('/bodega/ajax/validar-pin-receptor/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.modal.hide();
                if (typeof this.onSuccessCallback === 'function') {
                    this.onSuccessCallback();
                }
            } else {
                this.mostrarError(data.message || 'PIN incorrecto.');

                if (data.intentos_restantes !== undefined) {
                    const intentosEl = document.getElementById('pinIntentos');
                    intentosEl.classList.remove('d-none');
                    document.getElementById('intentos-count').textContent = data.intentos_restantes;
                }

                if (data.bloqueado) {
                    this.confirmBtn.disabled = true;
                    this.pinInput.disabled = true;
                }
            }
        } catch (error) {
            console.error('Error al validar PIN:', error);
            this.mostrarError('Error de conexión. Intente nuevamente.');
        } finally {
            this.setLoading(false);
        }
    },

    mostrarError(mensaje) {
        if (this.pinError) {
            this.pinError.textContent = mensaje;
            this.pinInput.classList.add('is-invalid');
            this.pinInput.focus();
        }
    },

    setLoading(loading) {
        if (this.confirmBtn) {
            this.confirmBtn.disabled = loading;
            this.confirmBtn.innerHTML = loading ?
                '<span class="spinner-border spinner-border-sm me-1"></span> Validando...' :
                '<i class="ri-check-line me-1"></i> Confirmar Entrega';
        }
    },

    getCookie(name) {
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
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    EntregaPin.init();
});

window.EntregaPin = EntregaPin;
