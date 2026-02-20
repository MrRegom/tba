/**
 * EntregaBienes v3.6 - Solución al conflicto con bodega_modal.js
 */
var EntregaBienes = (function () {
    var state = {
        activos: [],
        contador: 0,
        pinOK: false,
        activosCargados: false
    };

    function log(m, d) { console.log("[EntregaBienes v3.6] " + m, d || ""); }

    return {
        init: function () {
            log("Init v3.6");
            state.activos = [];
            state.activosCargados = false;
            state.contador = 0;
            state.pinOK = false;
            this.bindEvents();

            var sel = document.getElementById('id_solicitud');
            if (sel && sel.value) {
                log("Detectada solicitud inicial: " + sel.value);
                this.cargarSolicitud(sel.value);
            }
        },

        bindEvents: function () {
            var self = this;
            var form = document.getElementById('formEntregaBien');
            if (!form) { log("FATAL: No existe #formEntregaBien"); return; }

            // Cambio de solicitud
            var selStr = document.getElementById('id_solicitud');
            if (selStr) {
                selStr.onchange = function () {
                    log("Solicitud cambiada a: " + this.value);
                    if (this.value) self.cargarSolicitud(this.value);
                    else self.resetTable();
                };
            }

            // Agregar manual
            var btnAdd = document.getElementById('btn-agregar-bien');
            if (btnAdd) {
                btnAdd.onclick = function () { self.addRowManual(); };
            }

            // El botón de registro (tomamos control total)
            var btnSubmit = document.getElementById('btn-registrar-entrega');
            if (btnSubmit) {
                btnSubmit.onclick = function () {
                    log("Click en Registrar Entrega");
                    self.validarYPreSubmit();
                };
            }
        },

        cargarSolicitud: function (id) {
            var self = this;
            log("AJAX Solicitud: " + id);
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/bodega/ajax/solicitud/' + id + '/bienes/', true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        if (data.success) {
                            self.renderInfo(data.solicitud);
                            self.renderBienes(data.bienes);
                            if (data.solicitud.motivo) {
                                var m = document.getElementById('id_motivo');
                                if (m && !m.value) m.value = data.solicitud.motivo;
                            }
                        }
                    } catch (e) { log("Error parsing solicitud goods", e); }
                }
            };
            xhr.send();
        },

        cargarTodosLosActivos: function (callback) {
            if (state.activosCargados) { if (callback) callback(); return; }
            var self = this;
            log("Cargando todos los activos vía AJAX...");
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/bodega/ajax/activos/todos/', true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        if (data.success) {
                            state.activos = data.activos;
                            state.activosCargados = true;
                            if (callback) callback();
                        }
                    } catch (e) { log("Error carga activos", e); }
                }
            };
            xhr.send();
        },

        renderInfo: function (sol) {
            var div = document.getElementById('infoSolicitud');
            var d = document.getElementById('datosSolicitud');
            if (div && d) {
                d.innerHTML = "<b>Núm:</b> " + sol.numero + " | <b>Solicitante:</b> " + sol.solicitante + "<br><b>Dep:</b> " + sol.departamento;
                div.classList.remove('d-none');
            }
        },

        renderBienes: function (bienes) {
            var tb = document.getElementById('tbody-bienes');
            var divTb = document.getElementById('div-tabla-bienes');
            var empty = document.getElementById('sin-bienes');
            if (!tb) return;
            tb.innerHTML = '';

            if (!bienes || bienes.length === 0) {
                if (divTb) divTb.style.display = 'none';
                if (empty) empty.style.display = 'block';
                return;
            }

            if (divTb) divTb.style.display = 'block';
            if (empty) empty.style.display = 'none';

            for (var i = 0; i < bienes.length; i++) {
                this.addRow(bienes[i], true);
            }
        },

        addRow: function (b, isSol) {
            var tb = document.getElementById('tbody-bienes');
            var i = state.contador++;
            var row = tb.insertRow();
            row.className = 'fila-bien';
            if (isSol) row.dataset.detalleSolicitudId = b.detalle_solicitud_id;

            var colActivo = isSol ?
                '<b>' + b.activo_codigo + '</b><br><small>' + b.activo_nombre + '</small><input type="hidden" class="input-equipo-id" value="' + b.activo_id + '">' :
                '<select class="form-select form-select-sm input-equipo-id" onchange="EntregaBienes.updateCatByRow(this)"><option value="">Cargando...</option></select>';

            row.innerHTML = '<td>' + colActivo + '</td>' +
                '<td class="celda-categoria">' + (b.categoria || '-') + '</td>' +
                '<td>' + (isSol ? b.cantidad_pendiente : '-') + '</td>' +
                '<td><input type="number" class="form-control form-control-sm input-cantidad" value="' + (isSol ? b.cantidad_pendiente : 1) + '" min="1"></td>' +
                '<td><input type="text" class="form-control form-control-sm input-observaciones" value="' + (b.observaciones || '') + '"></td>' +
                '<td class="text-center"><button type="button" class="btn btn-sm text-danger btn-borrar-fila"><i class="ri-delete-bin-line"></i></button></td>';

            var self = this;
            row.querySelector('.btn-borrar-fila').onclick = function () { row.remove(); if (tb.children.length === 0) self.resetTable(); };

            if (!isSol) {
                this.cargarTodosLosActivos(function () {
                    var sel = row.querySelector('.input-equipo-id');
                    if (sel) {
                        var h = '<option value="">Seleccione...</option>';
                        for (var j = 0; j < state.activos.length; j++) {
                            h += '<option value="' + state.activos[j].id + '">' + state.activos[j].codigo + ' - ' + state.activos[j].nombre + '</option>';
                        }
                        sel.innerHTML = h;
                    }
                });
            }
        },

        updateCatByRow: function (sel) {
            var row = sel.closest('tr');
            var catCel = row.querySelector('.celda-categoria');
            var id = sel.value;
            var a = state.activos.find(function (x) { return x.id == id; });
            catCel.innerText = a ? a.categoria : '-';
        },

        addRowManual: function () {
            document.getElementById('div-tabla-bienes').style.display = 'block';
            document.getElementById('sin-bienes').style.display = 'none';
            this.addRow({}, false);
        },

        resetTable: function () {
            var tb = document.getElementById('tbody-bienes');
            if (tb) tb.innerHTML = '';
            document.getElementById('div-tabla-bienes').style.display = 'none';
            document.getElementById('sin-bienes').style.display = 'block';
            document.getElementById('infoSolicitud').classList.add('d-none');
        },

        validarYPreSubmit: function () {
            log("Validando...");
            var rows = document.querySelectorAll('.fila-bien');
            if (rows.length === 0) { alert("Agregue al menos un bien."); return; }

            var det = [];
            for (var i = 0; i < rows.length; i++) {
                var r = rows[i];
                var actEl = r.querySelector('.input-equipo-id');
                var canEl = r.querySelector('.input-cantidad');
                var obsEl = r.querySelector('.input-observaciones');

                if (!actEl || !canEl) continue;

                var act = actEl.value;
                var can = canEl.value;
                var obs = obsEl ? obsEl.value : '';

                if (!act || !can || can < 1) { alert("Complete todos los campos de la tabla."); return; }
                det.push({
                    equipo_id: parseInt(act),
                    cantidad: parseInt(can),
                    observaciones: obs,
                    detalle_solicitud_id: r.dataset.detalleSolicitudId || null
                });
            }

            // Llenamos el input oculto
            document.getElementById('detallesJson').value = JSON.stringify(det);
            log("JSON Preparado: ", document.getElementById('detallesJson').value);

            // Verificamos PIN
            var self = this;
            var rec = document.getElementById('id_recibido_por');
            if (!rec || !rec.value) { alert("Seleccione receptor."); return; }

            if (window.EntregaPin) {
                window.EntregaPin.mostrarModal(rec.value, rec.options[rec.selectedIndex].text, function () {
                    log("PIN OK. Disparando submit final...");
                    self.submitFinal();
                });
            } else {
                this.submitFinal();
            }
        },

        submitFinal: function () {
            var form = document.getElementById('formEntregaBien');
            // Disparamos el evento submit manualmente para que bodega_modal.js lo capture y haga el fetch AJAX
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        }
    };
})();
window.EntregaBienes = EntregaBienes;
