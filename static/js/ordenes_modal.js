/**
 * Manejo de modales para órdenes de compra
 * - Modal detalle (AJAX): cargar detalle en modal
 * - Modal editar (AJAX): cargar formulario de edición en modal y enviar via AJAX
 */

document.addEventListener("DOMContentLoaded", function () {
  // =========================================================================
  // MODAL DETALLE (AJAX)
  // =========================================================================
  var modalDetalleEl = document.getElementById("ordenesModal");
  var modalDetalleBody = document.getElementById("ordenesModalBody");
  var modalDetalleTitle = document.getElementById("ordenesModalLabel");
  var bsModalDetalle = null;

  if (modalDetalleEl && modalDetalleBody && modalDetalleTitle) {
    bsModalDetalle = new bootstrap.Modal(modalDetalleEl);

    document.querySelectorAll(".ordenes-modal-link").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var url = this.getAttribute("href");
        var title = this.getAttribute("data-modal-title") || "Detalle de Orden";

        modalDetalleTitle.textContent = title;
        modalDetalleBody.innerHTML =
          '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando información...</p></div>';
        bsModalDetalle.show();

        fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then(function (response) {
            if (!response.ok) throw new Error("Error al cargar la orden");
            return response.text();
          })
          .then(function (html) {
            modalDetalleBody.innerHTML = html;
          })
          .catch(function (error) {
            console.error("Error:", error);
            modalDetalleBody.innerHTML =
              '<div class="alert alert-danger"><h4 class="alert-heading">Error al cargar</h4><p>No se pudo cargar la información. Por favor, intente nuevamente.</p></div>';
          });
      });
    });

    modalDetalleEl.addEventListener("hidden.bs.modal", function () {
      modalDetalleBody.innerHTML =
        '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando información...</p></div>';
    });
  }

  // =========================================================================
  // MODAL EDITAR (AJAX - sin iframe)
  // =========================================================================
  var modalEditarEl = document.getElementById("editarOrdenModal");
  var modalEditarBody = document.getElementById("editarOrdenModalBody");
  var modalEditarTitle = document.getElementById("editarOrdenModalLabel");
  var bsModalEditar = null;
  var controladorOrden = null; // referencia al controlador de artículos/bienes

  if (modalEditarEl) {
    bsModalEditar = new bootstrap.Modal(modalEditarEl, {
      backdrop: "static",
      keyboard: false,
    });

    // Al cerrar: restaurar spinner para la próxima apertura
    modalEditarEl.addEventListener("hidden.bs.modal", function () {
      if (modalEditarBody) {
        modalEditarBody.innerHTML =
          '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Cargando...</p></div>';
      }
      controladorOrden = null;
    });
  }

  // =========================================================================
  // BUSCADOR INLINE REUTILIZABLE (reemplaza los sub-modales)
  // =========================================================================
  function inicializarBuscadorInline(opts) {
    var input = document.getElementById(opts.inputId);
    var dropdown = document.getElementById(opts.dropdownId);
    var btnLim = document.getElementById(opts.limpiarId);
    if (!input || !dropdown) return;

    function limpiar() {
      input.value = "";
      dropdown.style.display = "none";
      dropdown.innerHTML = "";
    }

    function renderizar(q) {
      q = (q || "").trim().toLowerCase();
      if (!q) {
        limpiar();
        return;
      }

      var filtrados = (opts.datos || []).filter(function (d) {
        return (d.codigo + " " + d.nombre).toLowerCase().includes(q);
      });

      if (!filtrados.length) {
        dropdown.innerHTML =
          '<div class="p-3 text-muted text-center small"><i class="ri-search-line me-1"></i>Sin resultados para "' +
          q +
          '"</div>';
        dropdown.style.display = "block";
        return;
      }

      dropdown.innerHTML = filtrados
        .slice(0, 12)
        .map(function (d) {
          return (
            '<div class="d-flex align-items-center gap-2 px-3 py-2 border-bottom resultado-item" ' +
            'style="cursor:pointer; transition: background .15s;" ' +
            'data-id="' +
            d.id +
            '" data-codigo="' +
            (d.codigo || "") +
            '" ' +
            'data-nombre="' +
            (d.nombre || "") +
            '">' +
            '<div class="flex-grow-1">' +
            '<span class="badge text-bg-' +
            opts.colorClase +
            ' me-1">' +
            (d.codigo || "") +
            "</span>" +
            '<span class="fw-medium">' +
            (d.nombre || "") +
            "</span>" +
            (d.categoria
              ? '<br><small class="text-muted">' + d.categoria + "</small>"
              : "") +
            "</div>" +
            '<button type="button" class="btn btn-sm btn-' +
            opts.colorClase +
            '">' +
            '<i class="ri-add-line"></i></button>' +
            "</div>"
          );
        })
        .join("");
      dropdown.style.display = "block";
    }

    // Hover effect
    dropdown.addEventListener("mouseover", function (e) {
      var item = e.target.closest(".resultado-item");
      if (item) item.style.background = "#f0f9ff";
    });
    dropdown.addEventListener("mouseout", function (e) {
      var item = e.target.closest(".resultado-item");
      if (item) item.style.background = "";
    });

    // Seleccionar
    dropdown.addEventListener("click", function (e) {
      var item = e.target.closest(".resultado-item");
      if (!item) return;
      opts.onSeleccionar({
        id: parseInt(item.getAttribute("data-id")),
        codigo: item.getAttribute("data-codigo"),
        nombre: item.getAttribute("data-nombre"),
      });
      limpiar();
      input.focus();
    });

    input.addEventListener("input", function () {
      renderizar(this.value);
    });

    if (btnLim) btnLim.addEventListener("click", limpiar);

    // Cerrar al hacer clic fuera
    document.addEventListener("click", function (e) {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });

    // Tecla Escape cierra
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") limpiar();
    });
  }

  /**
   * Inicializa el controlador de artículos y bienes dentro del modal de edición.
   */
  function inicializarControladorModal(data) {
    var articulosDisponibles = data.articulos || [];
    var activosDisponibles = data.activos || [];
    var articulosExistentes = data.articulosExistentes || [];
    var bienesExistentes = data.bienesExistentes || [];

    // Contadores
    var contadorArticulos = 0;
    var contadorBienes = 0;

    // Buscar artículos
    var buscarArticuloInput = document.getElementById("buscar-articulo-edit");
    if (buscarArticuloInput) {
      buscarArticuloInput.addEventListener("input", function () {
        var q = this.value.toLowerCase();
        document
          .querySelectorAll("#tbody-lista-articulos tr")
          .forEach(function (tr) {
            var texto = tr.textContent.toLowerCase();
            tr.style.display = texto.includes(q) ? "" : "none";
          });
      });
    }

    // Buscar bienes
    var buscarBienInput = document.getElementById("buscar-bien-edit");
    if (buscarBienInput) {
      buscarBienInput.addEventListener("input", function () {
        var q = this.value.toLowerCase();
        document
          .querySelectorAll("#tbody-lista-bienes tr")
          .forEach(function (tr) {
            var texto = tr.textContent.toLowerCase();
            tr.style.display = texto.includes(q) ? "" : "none";
          });
      });
    }

    // Toggle solicitudes
    var radioSi = document.getElementById("requiere_solicitud_si_m");
    var radioNo = document.getElementById("requiere_solicitud_no_m");
    var seccionSolicitudes = document.getElementById("seccion-solicitudes");
    if (radioSi && radioNo && seccionSolicitudes) {
      function toggleSolicitudes() {
        seccionSolicitudes.style.display = radioSi.checked ? "" : "none";
      }
      radioSi.addEventListener("change", toggleSolicitudes);
      radioNo.addEventListener("change", toggleSolicitudes);
    }

    /**
     * Actualiza visibilidad de "Sin artículos / bienes" y los totales.
     */
    function actualizarTotales() {
      var filas = document.querySelectorAll("#tbody-articulos-orden tr");
      var sinArticulos = document.getElementById("sin-articulos");
      if (sinArticulos)
        sinArticulos.classList.toggle("d-none", filas.length > 0);

      var totalArt = 0;
      filas.forEach(function (fila) {
        var subtotal = parseFloat(fila.getAttribute("data-subtotal") || 0);
        totalArt += subtotal;
      });
      var totalArticulosEl = document.getElementById("total-articulos");
      if (totalArticulosEl)
        totalArticulosEl.textContent =
          "$" + Math.round(totalArt).toLocaleString("es-CL");

      var filasBienes = document.querySelectorAll("#tbody-bienes-orden tr");
      var sinBienes = document.getElementById("sin-bienes");
      if (sinBienes)
        sinBienes.classList.toggle("d-none", filasBienes.length > 0);

      var totalBienes = 0;
      filasBienes.forEach(function (fila) {
        var subtotal = parseFloat(fila.getAttribute("data-subtotal") || 0);
        totalBienes += subtotal;
      });
      var totalBienesEl = document.getElementById("total-bienes");
      if (totalBienesEl)
        totalBienesEl.textContent =
          "$" + Math.round(totalBienes).toLocaleString("es-CL");

      serializarJsons();
    }

    /**
     * Serializa artículos y bienes a los campos hidden.
     */
    function serializarJsons() {
      var articulos = [];
      document
        .querySelectorAll("#tbody-articulos-orden tr")
        .forEach(function (tr) {
          var articuloId = tr.getAttribute("data-articulo-id");
          var cantInput = tr.querySelector(".input-cantidad-articulo");
          var precioInput = tr.querySelector(".input-precio-articulo");
          var descInput = tr.querySelector(".input-descuento-articulo");
          if (articuloId && cantInput && precioInput) {
            articulos.push({
              articulo_id: parseInt(articuloId),
              cantidad: parseFloat(cantInput.value) || 0,
              precio_unitario: parseFloat(precioInput.value) || 0,
              descuento: parseFloat(descInput ? descInput.value : 0) || 0,
            });
          }
        });
      var articulosJsonInput = document.getElementById("articulosJson");
      if (articulosJsonInput)
        articulosJsonInput.value = JSON.stringify(articulos);

      var bienes = [];
      document
        .querySelectorAll("#tbody-bienes-orden tr")
        .forEach(function (tr) {
          var activoId = tr.getAttribute("data-activo-id");
          var cantInput = tr.querySelector(".input-cantidad-bien");
          var precioInput = tr.querySelector(".input-precio-bien");
          var descInput = tr.querySelector(".input-descuento-bien");
          if (activoId && cantInput && precioInput) {
            bienes.push({
              activo_id: parseInt(activoId),
              cantidad: parseFloat(cantInput.value) || 0,
              precio_unitario: parseFloat(precioInput.value) || 0,
              descuento: parseFloat(descInput ? descInput.value : 0) || 0,
            });
          }
        });
      var bienesJsonInput = document.getElementById("bienesJson");
      if (bienesJsonInput) bienesJsonInput.value = JSON.stringify(bienes);
    }

    /**
     * Calcula el subtotal de una fila de artículo.
     */
    function calcularSubtotalFila(fila) {
      var cantInput = fila.querySelector(
        ".input-cantidad-articulo, .input-cantidad-bien",
      );
      var precioInput = fila.querySelector(
        ".input-precio-articulo, .input-precio-bien",
      );
      var descInput = fila.querySelector(
        ".input-descuento-articulo, .input-descuento-bien",
      );
      var cantidad = parseFloat((cantInput || {}).value) || 0;
      var precio = parseFloat((precioInput || {}).value) || 0;
      var descuento = parseFloat((descInput || {}).value) || 0;
      var subtotal = cantidad * precio * (1 - descuento / 100);
      fila.setAttribute("data-subtotal", subtotal.toFixed(2));
      var subtotalEl = fila.querySelector(".subtotal-articulo, .subtotal-bien");
      if (subtotalEl)
        subtotalEl.textContent =
          "$" + Math.round(subtotal).toLocaleString("es-CL");
      actualizarTotales();
    }

    /**
     * Agrega una fila de artículo a la tabla.
     */
    function agregarFilaArticulo(articulo, cantidad, precio, descuento) {
      var tbody = document.getElementById("tbody-articulos-orden");
      if (!tbody) return;
      var idx = contadorArticulos++;
      var fila = document.createElement("tr");
      fila.setAttribute("data-articulo-id", articulo.id);
      fila.setAttribute("data-subtotal", "0");
      fila.innerHTML =
        "<td><strong>" +
        articulo.nombre +
        '</strong><br><small class="text-muted">' +
        articulo.codigo +
        "</small></td>" +
        '<td><input type="number" class="form-control form-control-sm input-cantidad-articulo" id="cantidad_articulo_' +
        idx +
        '" value="' +
        (cantidad || 1) +
        '" min="0.01" step="0.01" style="width:80px;"></td>' +
        '<td><input type="number" class="form-control form-control-sm input-precio-articulo" id="precio_articulo_' +
        idx +
        '" value="' +
        (precio || 0) +
        '" min="0" style="width:110px;"></td>' +
        '<td><input type="number" class="form-control form-control-sm input-descuento-articulo" id="descuento_articulo_' +
        idx +
        '" value="' +
        (descuento || 0) +
        '" min="0" max="100" style="width:80px;"></td>' +
        '<td><span class="subtotal-articulo fw-bold">$0</span></td>' +
        '<td><button type="button" class="btn btn-danger btn-sm btn-eliminar-fila"><i class="ri-delete-bin-line"></i></button></td>';
      tbody.appendChild(fila);

      // Calcular subtotal inicial
      calcularSubtotalFila(fila);

      // Eventos de cambio
      fila.querySelectorAll("input").forEach(function (input) {
        input.addEventListener("input", function () {
          calcularSubtotalFila(fila);
        });
      });
      fila
        .querySelector(".btn-eliminar-fila")
        .addEventListener("click", function () {
          fila.remove();
          actualizarTotales();
        });
    }

    /**
     * Agrega una fila de bien/activo a la tabla.
     */
    function agregarFilaBien(activo, cantidad, precio, descuento) {
      var tbody = document.getElementById("tbody-bienes-orden");
      if (!tbody) return;
      var idx = contadorBienes++;
      var fila = document.createElement("tr");
      fila.setAttribute("data-activo-id", activo.id);
      fila.setAttribute("data-subtotal", "0");
      fila.innerHTML =
        "<td><strong>" +
        activo.nombre +
        '</strong><br><small class="text-muted">' +
        activo.codigo +
        "</small></td>" +
        '<td><input type="number" class="form-control form-control-sm input-cantidad-bien" id="cantidad_bien_' +
        idx +
        '" value="' +
        (cantidad || 1) +
        '" min="1" step="1" style="width:80px;"></td>' +
        '<td><input type="number" class="form-control form-control-sm input-precio-bien" id="precio_bien_' +
        idx +
        '" value="' +
        (precio || 0) +
        '" min="0" style="width:110px;"></td>' +
        '<td><input type="number" class="form-control form-control-sm input-descuento-bien" id="descuento_bien_' +
        idx +
        '" value="' +
        (descuento || 0) +
        '" min="0" max="100" style="width:80px;"></td>' +
        '<td><span class="subtotal-bien fw-bold">$0</span></td>' +
        '<td><button type="button" class="btn btn-danger btn-sm btn-eliminar-fila"><i class="ri-delete-bin-line"></i></button></td>';
      tbody.appendChild(fila);

      calcularSubtotalFila(fila);

      fila.querySelectorAll("input").forEach(function (input) {
        input.addEventListener("input", function () {
          calcularSubtotalFila(fila);
        });
      });
      fila
        .querySelector(".btn-eliminar-fila")
        .addEventListener("click", function () {
          fila.remove();
          actualizarTotales();
        });
    }

    // Pre-poblar artículos existentes
    articulosExistentes.forEach(function (item) {
      var articulo = {
        id: item.articulo_id,
        codigo: item.codigo,
        nombre: item.nombre,
      };
      agregarFilaArticulo(
        articulo,
        item.cantidad,
        item.precio_unitario,
        item.descuento,
      );
    });

    // Pre-poblar bienes existentes
    bienesExistentes.forEach(function (item) {
      var activo = {
        id: item.activo_id,
        codigo: item.codigo,
        nombre: item.nombre,
      };
      agregarFilaBien(
        activo,
        item.cantidad,
        item.precio_unitario,
        item.descuento,
      );
    });

    actualizarTotales();

    // =========================================================================
    // BUSCADOR INLINE DE ARTÍCULOS (sin sub-modal)
    // =========================================================================
    inicializarBuscadorInline({
      inputId: "buscar-articulo-inline",
      dropdownId: "resultados-articulo",
      limpiarId: "btn-limpiar-articulo",
      datos: articulosDisponibles,
      colorClase: "primary",
      onSeleccionar: function (item) {
        agregarFilaArticulo(item, 1, 0, 0);
      },
    });

    // =========================================================================
    // BUSCADOR INLINE DE BIENES/ACTIVOS (sin sub-modal)
    // =========================================================================
    inicializarBuscadorInline({
      inputId: "buscar-bien-inline",
      dropdownId: "resultados-bien",
      limpiarId: "btn-limpiar-bien",
      datos: activosDisponibles,
      colorClase: "info",
      onSeleccionar: function (item) {
        agregarFilaBien(item, 1, 0, 0);
      },
    });

    // Botones toggle solicitudes
    document.querySelectorAll(".btn-toggle-solicitud").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var solicitudId = this.getAttribute("data-solicitud-id");
        var hiddenInput = document.querySelector(
          '#solicitudes-hidden-inputs input[value="' + solicitudId + '"]',
        );
        if (hiddenInput) {
          // Ya agregada → quitar
          hiddenInput.remove();
          this.textContent = "Agregar";
          this.className = "btn btn-sm btn-success btn-toggle-solicitud";
          this.closest("tr").classList.remove("table-success");
          this.setAttribute("data-action", "agregar");
        } else {
          // Agregar
          var input = document.createElement("input");
          input.type = "hidden";
          input.name = "solicitudes";
          input.value = solicitudId;
          var div = document.getElementById("solicitudes-hidden-inputs");
          if (div) div.appendChild(input);
          this.innerHTML = '<i class="ri-check-line"></i> Quitar';
          this.className = "btn btn-sm btn-warning btn-toggle-solicitud";
          this.closest("tr").classList.add("table-success");
          this.setAttribute("data-action", "quitar");
        }
      });
    });

    // Retornar referencia al controlador
    return {
      serializarJsons: serializarJsons,
      actualizarTotales: actualizarTotales,
    };
  }

  /**
   * Inicializa el form del modal: eventos submit AJAX.
   */
  function inicializarFormModal(editUrl) {
    var form = document.getElementById("form-orden-compra-modal");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      // Serializar antes de enviar
      if (controladorOrden) controladorOrden.serializarJsons();

      var formData = new FormData(form);
      var btnSubmit = form.querySelector('[type="submit"]');
      var textoOriginal = btnSubmit ? btnSubmit.innerHTML : "";
      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML =
          '<span class="spinner-border spinner-border-sm me-1"></span> Guardando...';
      }

      fetch(form.getAttribute("action") || editUrl, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: formData,
      })
        .then(function (response) {
          if (response.ok) {
            return response.json().then(function (data) {
              if (data.success) {
                // Éxito: cerrar modal y recargar
                if (bsModalEditar) bsModalEditar.hide();
                window.location.reload();
              }
            });
          } else if (response.status === 422) {
            // Errores de validación: re-renderizar el body del modal
            return response.text().then(function (html) {
              if (modalEditarBody) {
                modalEditarBody.innerHTML = html;
                // Re-inicializar el controlador
                var modalData = window.MODAL_EDIT_DATA || {};
                controladorOrden = inicializarControladorModal(modalData);
                inicializarFormModal(editUrl);
              }
            });
          } else {
            throw new Error("Error del servidor: " + response.status);
          }
        })
        .catch(function (error) {
          console.error("Error al guardar:", error);
          if (modalEditarBody) {
            var alertDiv = modalEditarBody.querySelector(".alert-danger");
            if (!alertDiv) {
              alertDiv = document.createElement("div");
              alertDiv.className = "alert alert-danger";
              modalEditarBody.insertBefore(
                alertDiv,
                modalEditarBody.firstChild,
              );
            }
            alertDiv.textContent =
              "Error al guardar la orden. Por favor intente nuevamente.";
          }
        })
        .finally(function () {
          if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = textoOriginal;
          }
        });
    });
  }

  /**
   * Abre el modal de edición cargando el formulario via AJAX.
   */
  function abrirModalEditar(editUrl, numero) {
    // Cerrar modal de detalle si está abierto
    if (bsModalDetalle) bsModalDetalle.hide();

    if (!bsModalEditar || !modalEditarBody) {
      // Fallback: navegar a la página de edición
      window.location.href = editUrl;
      return;
    }

    // Actualizar título
    if (modalEditarTitle) {
      modalEditarTitle.textContent = "Editar Orden " + (numero || "");
    }

    // Mostrar spinner
    modalEditarBody.innerHTML =
      '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando formulario...</p></div>';
    bsModalEditar.show();

    // Cargar el partial via AJAX
    fetch(editUrl, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Error al cargar el formulario");
        return response.text();
      })
      .then(function (html) {
        modalEditarBody.innerHTML = html;

        // Ejecutar los scripts que vienen en el HTML del partial
        var scripts = modalEditarBody.querySelectorAll("script");
        scripts.forEach(function (script) {
          var nuevoScript = document.createElement("script");
          nuevoScript.textContent = script.textContent;
          document.body.appendChild(nuevoScript);
          document.body.removeChild(nuevoScript);
        });

        // Inicializar el controlador de artículos/bienes
        var data = window.MODAL_EDIT_DATA || {};
        controladorOrden = inicializarControladorModal(data);

        // Inicializar el form con envío AJAX
        inicializarFormModal(editUrl);
      })
      .catch(function (error) {
        console.error("Error:", error);
        modalEditarBody.innerHTML =
          '<div class="alert alert-danger"><h4 class="alert-heading">Error al cargar</h4><p>No se pudo cargar el formulario de edición. Por favor, intente nuevamente.</p><a href="' +
          editUrl +
          '" class="btn btn-primary">Ir a la página de edición</a></div>';
      });
  }

  // =========================================================================
  // EVENT DELEGATION para botones de editar (funciona en lista y menú)
  // =========================================================================
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".btn-editar-orden");
    if (btn) {
      e.preventDefault();
      var editUrl = btn.getAttribute("data-edit-url");
      var numero = btn.getAttribute("data-numero");
      abrirModalEditar(editUrl, numero);
    }
  });

  // =========================================================================
  // EVENT DELEGATION para botones de APROBAR / RECHAZAR
  // =========================================================================
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".btn-cambiar-estado");
    if (!btn) return;
    e.preventDefault();

    var url = btn.getAttribute("data-url");
    var numero = btn.getAttribute("data-orden-numero");
    var nuevoEstado = btn.getAttribute("data-nuevo-estado");
    var pk = btn.getAttribute("data-orden-pk");

    var accion = nuevoEstado === "APROBADA" ? "aprobar" : "rechazar";
    var colorConfig =
      nuevoEstado === "APROBADA"
        ? { confirmButtonColor: "#28a745", icon: "question" }
        : { confirmButtonColor: "#dc3545", icon: "warning" };

    // Confirmación con SweetAlert2 (si está disponible) o confirm nativo
    var confirmar =
      typeof Swal !== "undefined"
        ? Swal.fire({
            title:
              "¿" +
              accion.charAt(0).toUpperCase() +
              accion.slice(1) +
              " orden?",
            text: "Se va a " + accion + " la orden " + numero + ".",
            icon: colorConfig.icon,
            showCancelButton: true,
            confirmButtonColor: colorConfig.confirmButtonColor,
            cancelButtonColor: "#6c757d",
            confirmButtonText: "Sí, " + accion,
            cancelButtonText: "Cancelar",
          })
        : Promise.resolve({
            isConfirmed: window.confirm(
              "¿Desea " + accion + " la orden " + numero + "?",
            ),
          });

    confirmar.then(function (result) {
      if (!result.isConfirmed) return;

      // Deshabilitar botón mientras procesa
      btn.disabled = true;
      var textoOrig = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

      // Obtener CSRF token
      var csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
      var csrf = csrfToken ? csrfToken.value : getCookie("csrftoken");

      var formData = new FormData();
      formData.append("estado_codigo", nuevoEstado);
      if (csrf) formData.append("csrfmiddlewaretoken", csrf);

      fetch(url, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: formData,
      })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          if (data.success) {
            // Actualizar badge de estado en la fila sin recargar
            var fila = btn.closest("tr");
            if (fila) {
              var badge = fila.querySelector(".badge");
              if (badge && data.nuevo_estado) {
                badge.textContent = data.nuevo_estado.nombre;
                badge.style.backgroundColor =
                  data.nuevo_estado.color || "#6c757d";
              }
              // Reconstruir los botones de acción: solo queda "Ver"
              // (los botones de estado dependen del nuevo estado)
              // La forma más limpia: recargar la página
            }

            if (typeof Swal !== "undefined") {
              Swal.fire({
                icon: "success",
                title: "Estado actualizado",
                text: data.message,
                timer: 2000,
                showConfirmButton: false,
              }).then(function () {
                window.location.reload();
              });
            } else {
              alert(data.message);
              window.location.reload();
            }
          } else {
            if (typeof Swal !== "undefined") {
              Swal.fire({
                icon: "error",
                title: "Error",
                text: data.error || "No se pudo cambiar el estado.",
              });
            } else {
              alert(data.error || "Error al cambiar estado.");
            }
            btn.disabled = false;
            btn.innerHTML = textoOrig;
          }
        })
        .catch(function (err) {
          console.error("Error al cambiar estado:", err);
          if (typeof Swal !== "undefined") {
            Swal.fire({
              icon: "error",
              title: "Error",
              text: "Error de conexión. Intente nuevamente.",
            });
          } else {
            alert("Error de conexión.");
          }
          btn.disabled = false;
          btn.innerHTML = textoOrig;
        });
    });
  });

  /** Leer cookie por nombre (para CSRF) */
  function getCookie(name) {
    var match = document.cookie.match(
      new RegExp("(?:^|; )" + name + "=([^;]*)"),
    );
    return match ? decodeURIComponent(match[1]) : null;
  }
});
