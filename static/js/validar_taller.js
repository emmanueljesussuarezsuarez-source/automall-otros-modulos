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

    $(document).on('click', '.btn-editar-taller', function() {
        const id = $(this).data('id');
        const nombre = $(this).data('nombre');
        const direccion = $(this).data('direccion');
        const estado = String($(this).data('estado'));

        $('#edit_nombre_taller').val(nombre);
        $('#edit_direccion').val(direccion);
        $('#edit_estado').val(estado);
        $('#formEditarTaller').attr('action', '/taller/editar/' + id);

        const modalElem = document.getElementById('modalEditarTaller');
        if (modalElem) {
            const modal = new bootstrap.Modal(modalElem);
            modal.show();
        }
    });

    $(document).on('click', '.btn-eliminar-taller', function () {
        const url = $(this).data('url');
        const nombre = $(this).data('nombre') || 'este taller';

        Swal.fire({
            title: '¿Deseas eliminar este taller?',
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

    function mostrarMensajeDebajo(inputElem, mensaje) {
        inputElem.nextAll('.mensaje-error-simple').remove();
        var mensajeDiv = $('<div class="mensaje-error-simple text-danger small mt-1"></div>').text(mensaje);
        inputElem.after(mensajeDiv);
    }

    function limpiarMensaje(inputElem) {
        inputElem.nextAll('.mensaje-error-simple').remove();
    }

    $(document).on('input', '#nombre_taller, #edit_nombre_taller', function () {
        let $input = $(this);
        let val = $input.val();
        
        val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]/g, '');
        let contadorNumeros = 0;
        let valFiltrado = '';

        for (let i = 0; i < val.length; i++) {
            let char = val[i];
            if (/[0-9]/.test(char)) {
                if (contadorNumeros < 5) {
                    contadorNumeros++;
                    valFiltrado += char;
                }
            } else {
                valFiltrado += char;
            }
        }

        if (valFiltrado.length > 35) {
            valFiltrado = valFiltrado.substring(0, 35);
        }

        $input.val(valFiltrado);

        const valTrim = valFiltrado.trim();
        if (valTrim.length > 0 && valTrim.length < 3) {
            mostrarMensajeDebajo($input, 'El nombre debe tener al menos 3 caracteres.');
        } else {
            limpiarMensaje($input);
        }
    });

    $(document).on('input', '#direccion, #edit_direccion', function () {
        let $input = $(this);
        let val = $input.val();
        
        val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]/g, '');
        
        if (val.length > 60) {
            val = val.substring(0, 60); 
        }
        
        $input.val(val);

        const valTrim = val.trim();
        if (valTrim.length > 0 && valTrim.length < 10) {
            mostrarMensajeDebajo($input, 'La dirección debe tener al menos 10 caracteres.');
        } else {
            limpiarMensaje($input);
        }
    });

    $(document).on('submit', 'form', function (e) {
        if ($(this).attr('action') && $(this).attr('action').includes('generar_reporte')) {
            return;
        }

        const $form = $(this);
        if (!$form.find('input[name="nombre_taller"]').length) {
            return;
        }

        $form.find('.mensaje-error-simple').remove();
        let error = false;

        const $nombre = $form.find('input[name="nombre_taller"]');
        const $direccion = $form.find('textarea[name="direccion"]');
        const $estado = $form.find('select[name="estado"]');

        const nombre = $nombre.val().trim();
        const regexNombre = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{3,35}$/;
        const numerosNombre = (nombre.match(/[0-9]/g) || []).length;

        if (nombre === '') {
            mostrarMensajeDebajo($nombre, 'El nombre del taller es obligatorio.');
            error = true;
        } else if (nombre.length < 3) {
            mostrarMensajeDebajo($nombre, 'El nombre debe tener al menos 3 caracteres.');
            error = true;
        } else if (!regexNombre.test(nombre)) {
            mostrarMensajeDebajo($nombre, 'El nombre debe tener de 3 a 35 caracteres, solo letras, espacios y números.');
            error = true;
        } else if (numerosNombre > 5) {
            mostrarMensajeDebajo($nombre, 'El nombre no puede tener más de 5 números.');
            error = true;
        }

        const direccion = $direccion.val().trim();
        const regexDireccion = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s,]{10,60}$/;

        if (direccion === '') {
            mostrarMensajeDebajo($direccion, 'La dirección es obligatoria.');
            error = true;
        } else if (direccion.length < 10) {
            mostrarMensajeDebajo($direccion, 'La dirección debe tener al menos 10 caracteres.');
            error = true;
        } else if (!regexDireccion.test(direccion)) {
            mostrarMensajeDebajo($direccion, 'La dirección debe tener de 10 a 60 caracteres, solo letras, números, espacios y comas.');
            error = true;
        }

        if ($estado.length && $estado.val() === '') {
            mostrarMensajeDebajo($estado, 'Seleccione un estado.');
            error = true;
        }

        if (error) {
            e.preventDefault();
        }
    });

    if ($.fn.DataTable && $('#tablaTalleres').length) {
        if ($.fn.DataTable.isDataTable('#tablaTalleres')) {
            $('#tablaTalleres').DataTable().destroy();
        }

        $('#tablaTalleres').DataTable({
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
                emptyTable: "No hay talleres registrados."
            }
        });
    }
});