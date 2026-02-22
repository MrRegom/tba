/**
 * sidebar-active.js
 *
 * El estado activo se marca server-side en sidebar.html (Django request.path).
 * Este script previene que app.js (función w()) sobreescriba esos estados.
 *
 * app.js corre como IIFE al final del body. Nosotros corremos DESPUÉS de app.js
 * (ver base.html), pero podemos restaurar el estado server-side sin delay visible
 * porque solo usamos requestAnimationFrame (2 frames, ~32ms, imperceptible).
 */
(function () {
  "use strict";

  // Capturar IDs de collapses que YA tienen .show desde el servidor
  // (antes de que app.js los toque)
  var openCollapseIds = [];
  var activeLinks = [];

  document
    .querySelectorAll("#navbar-nav .collapse.menu-dropdown.show")
    .forEach(function (el) {
      openCollapseIds.push(el.id);
    });
  document
    .querySelectorAll(
      "#navbar-nav .nav-link.active, #navbar-nav .menu-link.active",
    )
    .forEach(function (el) {
      activeLinks.push(el);
    });

  // Restaurar estado inmediatamente después de que app.js (IIFE) termine
  // requestAnimationFrame asegura que corremos en el siguiente frame de render,
  // lo que es visualmente imperceptible (< 16ms)
  requestAnimationFrame(function () {
    // Restaurar collapses
    openCollapseIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.classList.add("show");
      var toggle = document.querySelector(
        '[data-bs-toggle="collapse"][aria-controls="' + id + '"]',
      );
      if (toggle) {
        toggle.setAttribute("aria-expanded", "true");
        toggle.classList.remove("collapsed");
      }
    });

    // Restaurar links activos
    activeLinks.forEach(function (el) {
      el.classList.add("active");
    });
  });
})();
