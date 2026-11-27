(function () {
    'use strict';

    // =========================================================
    // Eliminar registro (módulo o acción)
    // =========================================================
    function eliminarRegistro(url, nombre) {
        Swal.fire({
            title: '¿Desactivar ' + nombre + '?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, proceder'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(url, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => location.reload());
            }
        });
    }

    // =========================================================
    // Inicialización (jQuery + DataTables + eventos)
    // =========================================================
    $(document).ready(function () {
        // ---------- DataTables ----------
        $('#tablaModulos').DataTable({
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
                zeroRecords: "No se encontraron registros coincidentes"
            }
        });

        $('#tablaAcciones').DataTable({
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
                zeroRecords: "No se encontraron registros coincidentes"
            }
        });

        // ---------- Eliminar (delegación de eventos) ----------
        $(document).on('click', '.btn-eliminar-registro', function () {
            const url = $(this).data('url');
            const nombre = $(this).data('nombre');
            eliminarRegistro(url, nombre);
        });

        // ---------- Llenar modal editar módulo ----------
        $(document).on('click', '.btn-editar-modulo', function () {
            const id = $(this).data('id');
            const nombre = $(this).data('nombre');
            const estatus = $(this).data('estatus');

            $('#editModuloId').val(id);
            $('#editModuloNombre').val(nombre);
            $('#editModuloEstatus').val(estatus);
            $('#formEditarModulo').data('url', '/modulos/editar/' + id);
        });

        // ---------- Llenar modal editar acción ----------
        $(document).on('click', '.btn-editar-accion', function () {
            const id = $(this).data('id');
            const nombre = $(this).data('nombre');
            const estatus = $(this).data('estatus');

            $('#editAccionId').val(id);
            $('#editAccionNombre').val(nombre);
            $('#editAccionEstatus').val(estatus);
            $('#formEditarAccion').data('url', '/acciones/editar/' + id);
        });

        // ---------- Enviar formulario crear módulo ----------
        $('#formCrearModulo').on('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();

            if ($(this).find('.is-invalid').length > 0) {
                Swal.fire('Error', 'Por favor corrige los campos con errores', 'error');
                return false;
            }

            const url = $(this).data('url');
            const formData = new FormData(this);

            fetch(url, { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    Swal.fire({ icon: 'success', title: '¡Listo!', text: data.message, timer: 1500, showConfirmButton: false })
                        .then(() => location.reload());
                })
                .catch(err => Swal.fire('Error', 'Error de conexión', 'error'));

            return false;
        });

        // ---------- Enviar formulario editar módulo ----------
        $('#formEditarModulo').on('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();

            if ($(this).find('.is-invalid').length > 0) {
                Swal.fire('Error', 'Por favor corrige los campos con errores', 'error');
                return false;
            }

            const url = $(this).data('url');
            const formData = new FormData(this);

            fetch(url, { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    Swal.fire({ icon: 'success', title: '¡Listo!', text: data.message, timer: 1500, showConfirmButton: false })
                        .then(() => location.reload());
                })
                .catch(err => Swal.fire('Error', 'Error de conexión', 'error'));

            return false;
        });

        // ---------- Enviar formulario crear acción ----------
        $('#formCrearAccion').on('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();

            if ($(this).find('.is-invalid').length > 0) {
                Swal.fire('Error', 'Por favor corrige los campos con errores', 'error');
                return false;
            }

            const url = $(this).data('url');
            const formData = new FormData(this);

            fetch(url, { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    Swal.fire({ icon: 'success', title: '¡Listo!', text: data.message, timer: 1500, showConfirmButton: false })
                        .then(() => location.reload());
                })
                .catch(err => Swal.fire('Error', 'Error de conexión', 'error'));

            return false;
        });

        // ---------- Enviar formulario editar acción ----------
        $('#formEditarAccion').on('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();

            if ($(this).find('.is-invalid').length > 0) {
                Swal.fire('Error', 'Por favor corrige los campos con errores', 'error');
                return false;
            }

            const url = $(this).data('url');
            const formData = new FormData(this);

            fetch(url, { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    Swal.fire({ icon: 'success', title: '¡Listo!', text: data.message, timer: 1500, showConfirmButton: false })
                        .then(() => location.reload());
                })
                .catch(err => Swal.fire('Error', 'Error de conexión', 'error'));

            return false;
        });
    });
})();