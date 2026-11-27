document.addEventListener("DOMContentLoaded", function() {

    // =========================================================================
    // 1. MENSAJES FLASH CON SWEETALERT2
    // =========================================================================
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: categoria === 'success' ? '¡Éxito!' : (categoria === 'warning' ? 'Advertencia' : 'Aviso'),
                text: mensaje,
                icon: categoria === 'error' ? 'error' : (categoria === 'success' ? 'success' : 'info'),
                timer: 3500,
                timerProgressBar: true,
                confirmButtonColor: '#3085d6'
            });
        }
    });

    if (typeof $.fn.dataTable !== 'undefined') {
        $.fn.dataTable.ext.errMode = 'throw';
    }

    // =========================================================================
    // 2. CONFIGURACIÓN FLATPICKR (FECHA Y HORA)
    // =========================================================================
    const inputFecha = document.getElementById("modal_fecha");
    let fpFecha = null;
    
    if (inputFecha && !inputFecha.hasAttribute("readonly")) {
        const fechaDefecto = typeof fecha !== 'undefined' ? fecha : "today";
        fpFecha = flatpickr("#modal_fecha", { 
            locale: "es",
            dateFormat: "Y-m-d", 
            minDate: "today", 
            defaultDate: fechaDefecto 
        });
    }

    const fpHora = flatpickr("#modal_hora", {
        locale: "es",
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i:S",
        time_24hr: true,
        minuteIncrement: 30,
        minTime: "8:00",
        maxTime: "18:00",
        allowInput: false,
        onOpen: function(selectedDates, dateStr, instance) {
            if (instance.timeContainer) {
                const inputs = instance.timeContainer.querySelectorAll('input');
                inputs.forEach(input => {
                    input.addEventListener('input', function() {
                        this.value = this.value.replace(/\D/g, '');
                    });
                });
            }
        }
    });

    // =========================================================================
    // 3. INICIALIZACIÓN DE DATATABLES (ACCIONES ARRIBA EN LA FILA)
    // =========================================================================
    const tablaCitasElemento = $('#tablaCitas');
    if (tablaCitasElemento.length > 0) {
        tablaCitasElemento.DataTable({
            responsive: false, // Desactiva el acordeón plegable que mandaba Acciones abajo
            autoWidth: false,
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
                infoEmpty: "Mostrando 0 a 0 de 0 registros",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                zeroRecords: "No se encontraron citas coincidentes",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            },
            pageLength: 10,
            order: [[0, "desc"]],
            drawCallback: function () {
                // Reactiva tooltips en cada cambio de página
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            }
        });
    }

    // =========================================================================
    // 4. ACCIONES DE TABLA: CANCELAR, FINALIZAR, EDITAR Y FOTO
    // =========================================================================
    if (tablaCitasElemento.length > 0) {
        
        // CANCELAR O ELIMINAR CITA CON SWEETALERT2
        tablaCitasElemento.on('click', '.btn-cancelar-cita', function(e) {
            e.preventDefault();
            const idDetectado = this.getAttribute('data-cod');

            if (!idDetectado) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({ icon: 'error', title: 'Error', text: 'No se pudo extraer el ID de la cita.' });
                }
                return;
            }

            const esCliente = document.getElementById('modal_estado') === null || document.getElementById('modal_estado').type === 'hidden';
            const tituloAccion = esCliente ? '¿Cancelar Cita?' : '¿Eliminar Cita?';
            const descAccion = esCliente ? 
                `¿Está seguro de cancelar su cita #${idDetectado}? El cupo se liberará de inmediato.` :
                `¿Está seguro de eliminar la cita #${idDetectado} de forma permanente?`;

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: tituloAccion,
                    text: descAccion,
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: esCliente ? 'Sí, Cancelar Cita' : 'Sí, Eliminar',
                    cancelButtonText: 'No, Mantener',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = `/eliminar/${idDetectado}`;
                        document.body.appendChild(form);
                        form.submit();
                    }
                });
            }
        });

        // FINALIZAR CITA CON SWEETALERT2
        tablaCitasElemento.on('click', '.btn-disparar-finalizar', function(e) {
            e.preventDefault();
            const idDetectado = $(this).attr('data-cod');

            if (!idDetectado) return;

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Finalizar Cita?',
                    text: `¿Desea marcar la cita #${idDetectado} como Concluida / Finalizada?`,
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#198754',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, Finalizar',
                    cancelButtonText: 'Cancelar',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = `/finalizar/${idDetectado}`;
                        document.body.appendChild(form);
                        form.submit();
                    }
                });
            }
        });

        // INYECTAR EN MODAL MODIFICAR
        tablaCitasElemento.on('click', '.btn-editar-cita', function() {
            const btn = $(this);
            const codCita = btn.attr('data-cod');
            const fechaCita = btn.attr('data-fecha');
            const horaCita = btn.attr('data-hora');
            const estadoCita = btn.attr('data-estado');

            $('#modal_cod_cita').val(codCita);
            $('#modal_estado').val(estadoCita);

            if (fechaCita) {
                if (fpFecha) {
                    fpFecha.setDate(fechaCita);
                } else {
                    $('#modal_fecha').val(fechaCita);
                }
            }
            
            if (horaCita && fpHora) {
                fpHora.setDate(horaCita);
            }

            $('#formModificarCita').attr('action', `/modificar/${codCita}`);
        });

        // VISTA FOTO VEHÍCULO
        $(document).on('click', '.btn-ver-foto', function() {
            const urlImagen = $(this).attr('data-imagen');
            const tituloVehiculo = $(this).attr('data-titulo') || 'Foto del Vehículo';

            const elTitulo = document.getElementById('tituloFotoVehiculo');
            if (elTitulo) elTitulo.textContent = tituloVehiculo;

            const elCuerpo = document.getElementById('cuerpoFotoVehiculo');
            if (elCuerpo) {
                if (urlImagen && urlImagen.trim() !== '') {
                    elCuerpo.innerHTML = `<img src="${urlImagen}" class="img-fluid rounded shadow-sm" alt="${tituloVehiculo}" style="max-height: 400px; object-fit: contain;">`;
                } else {
                    elCuerpo.innerHTML = `
                        <div class="py-4 text-muted">
                            <i class="bi bi-image" style="font-size: 3rem;"></i>
                            <p class="mt-3 fw-semibold">Este vehículo no tiene foto registrada.</p>
                        </div>`;
                }
            }
        });
    }

    // =========================================================================
    // 5. VALIDACIÓN EN TIEMPO REAL Y ENVÍO DEL MODAL
    // =========================================================================
    const formModificar = document.getElementById('formModificarCita');
    if (formModificar) {
        const inputsMod = formModificar.querySelectorAll('input[required], select[required]');

        inputsMod.forEach(input => {
            ['input', 'change', 'blur'].forEach(evt => {
                input.addEventListener(evt, () => validarCampoModificarCita(input));
            });
        });

        function validarCampoModificarCita(input) {
            let esValido = true;
            const valor = input.value ? input.value.trim() : '';

            if (valor === '') esValido = false;

            if (input.name === 'fecha' && !input.hasAttribute('readonly')) {
                if (!valor) esValido = false;
            }

            if (input.name === 'hora') {
                if (!valor) esValido = false;
            }

            if (input.name === 'estado') {
                if (!valor) esValido = false;
            }

            if (esValido) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
            return esValido;
        }

        formModificar.addEventListener('submit', function(e) {
            e.preventDefault();

            let formValido = true;
            inputsMod.forEach(input => {
                if (!validarCampoModificarCita(input)) formValido = false;
            });

            if (!formValido) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Datos Inválidos',
                        text: 'Por favor complete todos los campos requeridos en rojo.',
                        confirmButtonColor: '#ffc107'
                    });
                }
                return;
            }

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Guardar Cambios?',
                    text: 'Se procederá a actualizar los datos de la cita.',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#ffc107',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, Guardar',
                    cancelButtonText: 'Cancelar',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        formModificar.submit();
                    }
                });
            } else {
                formModificar.submit();
            }
        });
    }

});