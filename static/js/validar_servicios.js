$(document).ready(function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

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

    $(document).on('click', '.btn-eliminar-servicio', function () {
        const url = $(this).data('url');
        const nombre = $(this).data('nombre') || 'este servicio';

        Swal.fire({
            title: '¿Deseas eliminar este servicio?',
            text: `Vas a inactivar ${nombre}.`,
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

    $(document).on('click', '.btn-finalizar-servicio', function () {
        const url = $(this).data('url');
        const nombre = $(this).data('nombre') || 'este servicio';
        const costoFinal = $(this).data('costoFinal');

        if (!costoFinal || String(costoFinal).trim() === '') {
            Swal.fire({
                title: 'Ingresar Costo Final',
                text: `El servicio '${nombre}' no tiene un costo final asignado. Ingrésalo para finalizar:`,
                input: 'text',
                inputPlaceholder: '0.00',
                showCancelButton: true,
                confirmButtonText: 'Guardar y Finalizar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#198754',
                cancelButtonColor: '#6c757d',
                inputValidator: (value) => {
                    if (!value || value.trim() === '') {
                        return 'Debes ingresar el costo final para continuar.';
                    }
                    const num = parseFloat(value.replace(',', '.'));
                    if (isNaN(num) || num < 0) {
                        return 'Ingresa un monto válido.';
                    }
                    if (num > 1000000) {
                        return 'El costo final no puede ser mayor a 1,000,000.';
                    }
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = url;

                    const inputCosto = document.createElement('input');
                    inputCosto.type = 'hidden';
                    inputCosto.name = 'costo_final';
                    inputCosto.value = result.value;
                    form.appendChild(inputCosto);

                    document.body.appendChild(form);
                    form.submit();
                }
            });
        } else {
            Swal.fire({
                title: '¿Deseas finalizar este servicio?',
                text: `Se finalizará ${nombre} y se reactivará el vehículo.`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Sí, finalizar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#198754',
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
        }
    });

    function mostrarMensajeDebajo(inputElem, mensaje) {
        inputElem.next('.mensaje-error-simple').remove();
        var mensajeDiv = $('<div class="mensaje-error-simple text-danger small mt-1"></div>').text(mensaje);
        inputElem.after(mensajeDiv);
        inputElem.one('input change', function () {
            mensajeDiv.remove();
        });
    }

    function formatearFechaHoy() {
        const hoy = new Date();
        const year = hoy.getFullYear();
        const month = String(hoy.getMonth() + 1).padStart(2, '0');
        const day = String(hoy.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    const fechaHoy = formatearFechaHoy();

    if ($('#fecha_realizacion').length) {
        $('#fecha_realizacion').attr('min', fechaHoy);
    }

    if ($('#nombre_servicio').length) {
        $('#nombre_servicio').attr('maxlength', '50');
    }
    if ($('#descripcion_especifica').length) {
        $('#descripcion_especifica').attr('maxlength', '150');
    }

    $('#nombre_servicio').on('input', function () {
        let val = $(this).val();
        let limpio = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, '');

        if (limpio.length > 50) {
            limpio = limpio.substring(0, 50);
        }

        if (val !== limpio) {
            $(this).val(limpio);
        }
        validarNombreServicio();
    });

    $('#costo_base, #costo_final').on('input', function () {
        let val = $(this).val();
        let limpio = val.replace(/[^0-9.,]/g, '');
        let parts = limpio.split(/[\.,]/);
        if (parts.length > 2) {
            let firstSepMatch = limpio.match(/[\.,]/);
            let sep = firstSepMatch ? firstSepMatch[0] : '';
            limpio = parts[0] + (sep ? sep + parts.slice(1).join('') : '');
        }

        if (limpio !== '') {
            let numVal = parseFloat(limpio.replace(',', '.'));
            if (!isNaN(numVal) && numVal > 1000000) {
                limpio = '1000000';
            }
        }

        if (val !== limpio) {
            $(this).val(limpio);
        }

        if ($(this).attr('id') === 'costo_base') {
            validarCostoBase();
        } else {
            validarCostoFinal();
        }
    });

    $('#descripcion_especifica').on('input', function () {
        let val = $(this).val();
        let limpio = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]/g, '');

        if (limpio.length > 150) {
            limpio = limpio.substring(0, 150);
        }

        if (val !== limpio) {
            $(this).val(limpio);
        }
        validarDescripcionEspecifica();
    });

    function validarNombreServicio() {
        const $campo = $('#nombre_servicio');
        const val = $campo.val().trim();
        const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{3,50}$/;

        if (val === '') {
            mostrarMensajeDebajo($campo, 'El nombre del servicio es obligatorio.');
            return false;
        } else if (val.length < 3) {
            mostrarMensajeDebajo($campo, 'El nombre del servicio debe tener al menos 3 caracteres.');
            return false;
        } else if (val.length > 50) {
            mostrarMensajeDebajo($campo, 'El nombre del servicio no puede superar los 50 caracteres.');
            return false;
        } else if (!regex.test(val)) {
            mostrarMensajeDebajo($campo, 'El nombre del servicio solo permite letras y espacios.');
            return false;
        } else {
            $campo.next('.mensaje-error-simple').remove();
            return true;
        }
    }

    function validarCostoBase() {
        const $campo = $('#costo_base');
        const val = $campo.val().trim();

        if (val !== '') {
            const num = parseFloat(val.replace(',', '.'));
            if (isNaN(num) || num < 0) {
                mostrarMensajeDebajo($campo, 'El costo base debe ser un número válido.');
                return false;
            } else if (num > 1000000) {
                mostrarMensajeDebajo($campo, 'El costo base no puede ser mayor a 1,000,000.');
                return false;
            }
        }
        $campo.next('.mensaje-error-simple').remove();
        return true;
    }

    function validarCostoFinal() {
        const $campo = $('#costo_final');
        const val = $campo.val().trim();

        if (val !== '') {
            const num = parseFloat(val.replace(',', '.'));
            if (isNaN(num) || num < 0) {
                mostrarMensajeDebajo($campo, 'El costo final debe ser un número válido.');
                return false;
            } else if (num > 1000000) {
                mostrarMensajeDebajo($campo, 'El costo final no puede ser mayor a 1,000,000.');
                return false;
            }
        }
        $campo.next('.mensaje-error-simple').remove();
        return true;
    }

    function validarFechaRealizacion() {
        const $campo = $('#fecha_realizacion');
        const val = $campo.val().trim();

        if (val === '') {
            mostrarMensajeDebajo($campo, 'La fecha de realización es obligatoria.');
            return false;
        } else if (val < fechaHoy) {
            mostrarMensajeDebajo($campo, 'La fecha de realización no puede ser anterior al día de hoy.');
            $campo.val('');
            return false;
        } else {
            $campo.next('.mensaje-error-simple').remove();
            return true;
        }
    }

    function validarPlaca() {
        const $campo = $('#placa');
        if ($campo.val() === '') {
            mostrarMensajeDebajo($campo, 'Seleccione un vehículo.');
            return false;
        } else {
            $campo.next('.mensaje-error-simple').remove();
            return true;
        }
    }

    function validarDescripcionEspecifica() {
        const $campo = $('#descripcion_especifica');
        const val = $campo.val().trim();
        const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]{10,150}$/;

        if (val === '') {
            mostrarMensajeDebajo($campo, 'La descripción específica es obligatoria.');
            return false;
        } else if (val.length < 10) {
            mostrarMensajeDebajo($campo, 'La descripción específica debe tener al menos 10 caracteres.');
            return false;
        } else if (val.length > 150) {
            mostrarMensajeDebajo($campo, 'La descripción no puede superar los 150 caracteres.');
            return false;
        } else if (!regex.test(val)) {
            mostrarMensajeDebajo($campo, 'La descripción solo permite letras, números, espacios y comas.');
            return false;
        } else {
            $campo.next('.mensaje-error-simple').remove();
            return true;
        }
    }

    $('#nombre_servicio').on('blur', validarNombreServicio);
    $('#costo_base').on('blur', validarCostoBase);
    $('#costo_final').on('blur', validarCostoFinal);
    $('#fecha_realizacion').on('change blur', validarFechaRealizacion);
    $('#placa').on('change blur', validarPlaca);
    $('#descripcion_especifica').on('blur', validarDescripcionEspecifica);

    $('form').on('submit', function (e) {
        if ($(this).attr('action') && $(this).attr('action').includes('generar_reporte_servicios')) {
            return;
        }

        const $form = $(this);
        if (!$form.find('#nombre_servicio').length && !$form.find('#costo_base').length) {
            return;
        }

        $('.mensaje-error-simple').remove();
        let error = false;

        if (!validarPlaca()) {
            $('#placa').focus();
            error = true;
        }
        if (!validarNombreServicio()) {
            $('#nombre_servicio').focus();
            error = true;
        }
        if (!validarCostoBase()) {
            if (!error) $('#costo_base').focus();
            error = true;
        }
        if (!validarCostoFinal()) {
            if (!error) $('#costo_final').focus();
            error = true;
        }
        if (!validarFechaRealizacion()) {
            if (!error) $('#fecha_realizacion').focus();
            error = true;
        }
        if (!validarDescripcionEspecifica()) {
            if (!error) $('#descripcion_especifica').focus();
            error = true;
        }

        if (error) {
            e.preventDefault();
        }
    });

    if ($('#tablaServicios').length && $.fn.DataTable) {
        if ($.fn.DataTable.isDataTable('#tablaServicios')) {
            $('#tablaServicios').DataTable().destroy();
        }

        $('#tablaServicios').DataTable({
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
                emptyTable: "No hay servicios registrados."
            }
        });
    }
});