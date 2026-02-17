/**
 * Marca el item activo del sidebar comparando location.pathname
 * con los href de los nav-links. Reemplaza la logica del tema Velzon
 * que solo funciona con archivos HTML estaticos.
 */
(function() {
    'use strict';

    function activateMenuItem() {
        var nav = document.getElementById('navbar-nav');
        if (!nav) return;

        var currentPath = location.pathname;

        // Limpiar estados activos previos puestos por app.js
        nav.querySelectorAll('.active').forEach(function(el) {
            el.classList.remove('active');
        });
        nav.querySelectorAll('.collapse.show').forEach(function(el) {
            el.classList.remove('show');
        });
        nav.querySelectorAll('[aria-expanded="true"]').forEach(function(el) {
            el.setAttribute('aria-expanded', 'false');
        });

        // Buscar mejor coincidencia: primero exacta, luego por prefijo
        var links = nav.querySelectorAll('a.nav-link, a.menu-link');
        var bestMatch = null;
        var bestLength = 0;

        links.forEach(function(link) {
            var href = link.getAttribute('href');
            if (!href || href === '#' || href.startsWith('#')) return;

            // Extraer pathname del href
            try {
                var url = new URL(href, location.origin);
                var linkPath = url.pathname;

                if (currentPath === linkPath) {
                    // Coincidencia exacta - maxima prioridad
                    if (linkPath.length > bestLength) {
                        bestMatch = link;
                        bestLength = linkPath.length + 1000; // Prioridad extra
                    }
                } else if (currentPath.startsWith(linkPath) && linkPath !== '/') {
                    // Coincidencia por prefijo (para sub-paginas)
                    if (linkPath.length > bestLength) {
                        bestMatch = link;
                        bestLength = linkPath.length;
                    }
                }
            } catch(e) {
                // Ignorar hrefs invalidos
            }
        });

        if (!bestMatch) return;

        // Marcar como activo
        bestMatch.classList.add('active');

        // Abrir collapse padre si es submenu
        var collapse = bestMatch.closest('.collapse.menu-dropdown');
        if (collapse) {
            collapse.classList.add('show');
            var parentToggle = collapse.parentElement.querySelector('[data-bs-toggle="collapse"]');
            if (parentToggle) {
                parentToggle.classList.add('active');
                parentToggle.setAttribute('aria-expanded', 'true');
            }

            // Soporte para submenus anidados
            var parentCollapse = collapse.parentElement.closest('.collapse.menu-dropdown');
            if (parentCollapse) {
                parentCollapse.classList.add('show');
                var grandParentToggle = parentCollapse.parentElement.querySelector('[data-bs-toggle="collapse"]');
                if (grandParentToggle) {
                    grandParentToggle.classList.add('active');
                    grandParentToggle.setAttribute('aria-expanded', 'true');
                }
            }
        }
    }

    // Ejecutar despues de que app.js haya corrido
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(activateMenuItem, 100);
        });
    } else {
        setTimeout(activateMenuItem, 100);
    }
})();
