$(document).ready(function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const appConfig = document.getElementById('app-config');
    if (appConfig && appConfig.dataset.mostrarModal === 'true') {
        const modalElem = document.getElementById('modalFinalizar');
        if (modalElem) {
            const modalFinalizar = new bootstrap.Modal(modalElem);
            modalFinalizar.show();
        }
    }

    $('#flash-messages > div').each(function() {
        const category = $(this).data('category');
        const message = $(this).data('message');
        const icon = category === 'danger' ? 'error' : category;
        const title = category === 'danger' ? 'Error' : (category.charAt(0).toUpperCase() + category.slice(1));
        
        Swal.fire({
            icon: icon,
            title: title,
            text: message,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    });

    $(document).on('click', '#btn-agregar-detalle', function() {
        const contenedor = document.getElementById('contenedor-detalles');
        if (!contenedor) return;
        const contadorDetalles = contenedor.querySelectorAll('.detalle-item').length;
        const nuevoDetalle = document.createElement('div');
        nuevoDetalle.className = 'row detalle-item mb-2';
        nuevoDetalle.innerHTML = `
            <div class="col-md-8">
                <input type="text" name="descripcion_detalle_${contadorDetalles}" class="form-control" placeholder="Descripción detallada">
            </div>
            <div class="col-md-3">
                <input type="number" name="cantidad_${contadorDetalles}" class="form-control" placeholder="Cantidad">
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-danger btn-sm btn-eliminar-detalle">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        contenedor.appendChild(nuevoDetalle);
    });

    $(document).on('click', '#contenedor-detalles .btn-eliminar-detalle', function(e) {
        const fila = e.target.closest('.detalle-item');
        if (fila && document.querySelectorAll('.detalle-item').length > 1) {
            fila.remove();
        }
    });

    $(document).on('click', '.btn-eliminar-mantenimiento', function () {
        const url = $(this).data('url');
        const codigo = $(this).data('codigo') || '';

        Swal.fire({
            title: '¿Deseas eliminar este mantenimiento?',
            text: `Vas a inactivar el registro N° ${codigo}.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d'
        }).then((result) => {
            if (result.isConfirmed) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;
                document.body.appendChild(form);
                form.submit();
            }
        });
    });

    $(document).on('click', '.btn-finalizar-mantenimiento', function () {
        const url = $(this).data('url');
        const codigo = $(this).data('codigo') || '';

        Swal.fire({
            title: '¿Deseas finalizar este mantenimiento?',
            text: `Se finalizará el registro N° ${codigo}. Deberás completar los campos de costo final y detalles.`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, finalizar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#198754',
            cancelButtonColor: '#6c757d'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = url;
            }
        });
    });

    function mostrarMensajeDebajo(inputElem, mensaje) {
        inputElem.nextAll('.mensaje-error-simple').remove();
        var mensajeDiv = $('<div class="mensaje-error-simple text-danger small mt-1"></div>').text(mensaje);
        inputElem.after(mensajeDiv);
    }

    function limpiarMensaje(inputElem) {
        inputElem.nextAll('.mensaje-error-simple').remove();
    }

    function formatearFechaHoy() {
        const hoy = new Date();
        const year = hoy.getFullYear();
        const month = String(hoy.getMonth() + 1).padStart(2, '0');
        const day = String(hoy.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    const fechaHoy = formatearFechaHoy();

    if ($('#fecha_solicitud').length) {
        $('#fecha_solicitud').attr('min', fechaHoy);
    }

    if ($('#descripcion_general').length) {
        $('#descripcion_general').attr('maxlength', '100');
    }

    $(document).on('input', '#descripcion_general', function () {
        let $input = $(this);
        let val = $input.val();
        let limpio = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]/g, '');
        
        if (limpio.length > 100) {
            limpio = limpio.substring(0, 100);
        }
        
        if (val !== limpio) {
            $input.val(limpio);
        }

        const valTrim = limpio.trim();
        if (valTrim.length > 0 && valTrim.length < 10) {
            mostrarMensajeDebajo($input, 'La descripción debe tener al menos 10 caracteres.');
        } else {
            limpiarMensaje($input);
        }
    });

    
    $(document).on('keydown', '#costo_base, #costo_final', function (e) {
        if (['e', 'E', '+', '-'].includes(e.key)) {
            e.preventDefault();
        }
    });

    
    $(document).on('input', '#costo_base, #costo_final', function () {
        let $input = $(this);
        let val = $input.val();
        
        
        let limpio = val.replace(/[^0-9.]/g, '');
        
        const partes = limpio.split('.');
        if (partes.length > 2) {
            limpio = partes[0] + '.' + partes.slice(1).join('');
        }

        if (parseFloat(limpio) > 1000000) {
            limpio = '1000000';
        }

        if (val !== limpio) {
            $input.val(limpio);
        }

        const valTrim = limpio.trim();
        if (valTrim !== '' && (isNaN(parseFloat(valTrim)) || parseFloat(valTrim) < 0)) {
            mostrarMensajeDebajo($input, 'Ingrese un costo válido.');
        } else {
            limpiarMensaje($input);
        }
    });

    $(document).on('input', 'input[name^="descripcion_detalle_"]', function () {
        let $input = $(this);
        let val = $input.val();
        let limpio = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]/g, '');

        if (limpio.length > 80) {
            limpio = limpio.substring(0, 80);
        }

        if (val !== limpio) {
            $input.val(limpio);
        }

        const valTrim = limpio.trim();
        if (valTrim.length > 0 && !/^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]+$/.test(valTrim)) {
            mostrarMensajeDebajo($input, 'Solo se permiten letras y números.');
        } else {
            limpiarMensaje($input);
        }
    });

    $(document).on('input', 'input[name^="cantidad_"]', function () {
        let $input = $(this);
        let val = $input.val();
        let limpio = val.replace(/[^0-9]/g, '');

        if (limpio !== '' && parseInt(limpio, 10) > 100) {
            limpio = '100';
        }

        if (val !== limpio) {
            $input.val(limpio);
        }

        const valTrim = limpio.trim();
        if (valTrim !== '' && parseInt(valTrim, 10) < 1) {
            mostrarMensajeDebajo($input, 'La cantidad mínima es 1.');
        } else {
            limpiarMensaje($input);
        }
    });

    function validarCostoBase() {
        const $campo = $('#costo_base');
        if (!$campo.length) return true;

        const val = $campo.val().trim();

        if (val === '') {
            limpiarMensaje($campo);
            return true;
        }

        const num = parseFloat(val);
        if (isNaN(num) || num < 0) {
            mostrarMensajeDebajo($campo, 'Ingrese un costo base válido.');
            return false;
        }

        if (num > 1000000) {
            mostrarMensajeDebajo($campo, 'El costo base no puede superar 1,000,000.');
            return false;
        }

        limpiarMensaje($campo);
        return true;
    }

    function validarCostoFinal(esObligatorio = false) {
        const $campo = $('#costo_final');
        if (!$campo.length) return true;

        const val = $campo.val().trim();

        if (esObligatorio && val === '') {
            mostrarMensajeDebajo($campo, 'El costo final es obligatorio para finalizar el mantenimiento.');
            return false;
        }

        if (val !== '') {
            const num = parseFloat(val);
            if (isNaN(num) || num < 0) {
                mostrarMensajeDebajo($campo, 'Ingrese un costo final válido.');
                return false;
            }

            if (num > 1000000) {
                mostrarMensajeDebajo($campo, 'El costo final no puede superar 1,000,000.');
                return false;
            }
        }

        limpiarMensaje($campo);
        return true;
    }

    function validarDetalles() {
        let esValido = true;

        $('input[name^="descripcion_detalle_"]').each(function () {
            const $campo = $(this);
            const val = $campo.val().trim();
            if (val !== '') {
                const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]+$/;
                if (!regex.test(val)) {
                    mostrarMensajeDebajo($campo, 'Solo se permiten letras y números.');
                    esValido = false;
                } else if (val.length > 80) {
                    mostrarMensajeDebajo($campo, 'No puede superar los 80 caracteres.');
                    esValido = false;
                }
            }
        });

        $('input[name^="cantidad_"]').each(function () {
            const $campo = $(this);
            const val = $campo.val().trim();
            if (val !== '') {
                const num = parseInt(val, 10);
                if (isNaN(num) || num < 1) {
                    mostrarMensajeDebajo($campo, 'Ingrese una cantidad válida.');
                    esValido = false;
                } else if (num > 100) {
                    mostrarMensajeDebajo($campo, 'La cantidad no puede superar 100.');
                    esValido = false;
                }
            }
        });

        return esValido;
    }

    function validarDescripcion() {
        const $campo = $('#descripcion_general');
        if (!$campo.length) return true;

        const val = $campo.val().trim();
        const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]{10,100}$/;

        if (val === '') {
            mostrarMensajeDebajo($campo, 'La descripción general es obligatoria.');
            return false;
        }
        if (val.length < 10) {
            mostrarMensajeDebajo($campo, 'La descripción debe tener al menos 10 caracteres.');
            return false;
        }
        if (val.length > 100) {
            mostrarMensajeDebajo($campo, 'La descripción general no puede superar los 100 caracteres.');
            return false;
        }
        if (!regex.test(val)) {
            mostrarMensajeDebajo($campo, 'La descripción solo permite letras, números y comas.');
            return false;
        }
        limpiarMensaje($campo);
        return true;
    }

    function validarQuienAutoriza() {
        const $campo = $('#quien_autoriza');
        if (!$campo.length) return true;

        if ($campo.val() === '') {
            mostrarMensajeDebajo($campo, 'Seleccione quién autoriza.');
            return false;
        }
        limpiarMensaje($campo);
        return true;
    }

    function validarTipo() {
        const $campo = $('#tipo');
        if (!$campo.length) return true;

        if ($campo.val() === '') {
            mostrarMensajeDebajo($campo, 'El tipo de mantenimiento es obligatorio.');
            return false;
        }
        limpiarMensaje($campo);
        return true;
    }

    function validarFechaSolicitud() {
        const $campo = $('#fecha_solicitud');
        if (!$campo.length) return true;

        const val = $campo.val();

        if (val === '') {
            mostrarMensajeDebajo($campo, 'Seleccione la fecha de solicitud.');
            return false;
        }
        if (val < fechaHoy) {
            mostrarMensajeDebajo($campo, 'La fecha de solicitud debe ser a partir del día de hoy.');
            $campo.val('');
            return false;
        }

        if ($('#fecha_completada').length) {
            $('#fecha_completada').attr('min', val);
        }

        limpiarMensaje($campo);
        return true;
    }

    function validarFechaCompletada() {
        const $campo = $('#fecha_completada');
        if (!$campo.length) return true;

        const fechaSolicitud = $('#fecha_solicitud').val();
        const fechaCompletada = $campo.val();

        if (fechaCompletada) {
            if (fechaSolicitud && fechaCompletada < fechaSolicitud) {
                mostrarMensajeDebajo($campo, 'La fecha completada no puede ser anterior a la fecha de solicitud.');
                $campo.val('');
                return false;
            }
        }

        limpiarMensaje($campo);
        return true;
    }

    function validarPlaca() {
        const $campo = $('#placa');
        if (!$campo.length) return true;

        if ($campo.val() === '') {
            mostrarMensajeDebajo($campo, 'Seleccione un vehículo.');
            return false;
        }
        limpiarMensaje($campo);
        return true;
    }

    function validarTaller() {
        const $campo = $('#cod_taller');
        if (!$campo.length) return true;

        if ($campo.val() === '') {
            mostrarMensajeDebajo($campo, 'Seleccione un taller.');
            return false;
        }
        limpiarMensaje($campo);
        return true;
    }

    $(document).on('change blur', '#quien_autoriza', validarQuienAutoriza);
    $(document).on('change blur', '#tipo', validarTipo);
    $(document).on('change blur', '#fecha_solicitud', function () {
        validarFechaSolicitud();
        validarFechaCompletada();
    });
    $(document).on('change blur', '#fecha_completada', validarFechaCompletada);
    $(document).on('change blur', '#placa', validarPlaca);
    $(document).on('change blur', '#cod_taller', validarTaller);

    $('form').on('submit', function (e) {
        if ($(this).attr('action') && $(this).attr('action').includes('generar_reporte_mantenimiento')) {
            return;
        }

        $('.mensaje-error-simple').remove();

        const esModalFinalizar = $(this).closest('#modalFinalizar').length > 0;
        let error = false;

        if (esModalFinalizar) {
            if (!validarCostoFinal(true)) error = true;
            if (!validarDetalles()) error = true;
        } else {
            if (!validarPlaca()) error = true;
            if (!validarTaller()) error = true;
            if (!validarQuienAutoriza()) error = true;
            if (!validarTipo()) error = true;
            if (!validarFechaSolicitud()) error = true;
            if (!validarFechaCompletada()) error = true;
            if (!validarDescripcion()) error = true;
            if (!validarCostoBase()) error = true;
            if (!validarCostoFinal(false)) error = true;
            if (!validarDetalles()) error = true;
        }

        if (error) {
            e.preventDefault();
        }
    });

    if ($('#tablaMantenimientoOperacional').length && $.fn.DataTable) {
        if ($.fn.DataTable.isDataTable('#tablaMantenimientoOperacional')) {
            $('#tablaMantenimientoOperacional').DataTable().destroy();
        }

        $('#tablaMantenimientoOperacional').DataTable({
            responsive: true,
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando desde _START_ al _END_ de _TOTAL_ registros",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                },
                zeroRecords: "No se encontraron registros coincidentes",
                emptyTable: "No hay mantenimientos registrados."
            }
        });
    }
});