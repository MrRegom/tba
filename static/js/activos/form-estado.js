/**
 * Validación y envío del formulario de estados de activos.
 * 
 * Valida campos requeridos antes de enviar el formulario.
 * 
 * @file static/js/activos/form-estado.js
 */

(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('form-estado');
        const btnGuardar = document.getElementById('btn-guardar');
        
        if (!form || !btnGuardar) {
            return;
        }
        
        /**
         * Valida los campos requeridos del formulario.
         * 
         * @returns {boolean} True si todos los campos son válidos, False en caso contrario
         */
        function validarFormulario() {
            const codigo = form.querySelector('#id_codigo');
            const nombre = form.querySelector('#id_nombre');
            
            if (codigo && !codigo.value.trim()) {
                alert('El código es obligatorio');
                codigo.focus();
                return false;
            }
            
            if (nombre && !nombre.value.trim()) {
                alert('El nombre es obligatorio');
                nombre.focus();
                return false;
            }
            
            return true;
        }
        
        /**
         * Maneja el evento click del botón Guardar.
         * Valida el formulario y lo envía si es válido.
         */
        btnGuardar.addEventListener('click', function(e) {
            if (!validarFormulario()) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
            
            // Si la validación es exitosa, enviar el formulario
            form.submit();
        });
    });
})();

