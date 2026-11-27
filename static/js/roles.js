(function () {
    'use strict';

    // =========================================================
    // Eliminar rol (marcar como inactivo)
    // =========================================================
    function eliminarRol(id_rol, nombre_rol) {
        Swal.fire({
            title: '¿Eliminar rol ' + nombre_rol + '?',
            text: "Esta acción cambiará el estado del rol a inactivo.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch('/roles/eliminar/' + id_rol, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'success') {
                            Swal.fire('Eliminado!', data.message, 'success').then(() => {
                                location.reload();
                            });
                        } else {
                            Swal.fire('Error', data.message, 'error');
                        }
                    })
                    .catch(err => Swal.fire('Error', 'No se pudo procesar la solicitud', 'error'));
            }
        });
    }

    // =========================================================
    // Inicialización (jQuery + DataTables + eventos)
    // =========================================================
    $(document).ready(function () {
        // ---------- DataTables ----------
        $('#tablaRoles').DataTable({
            responsive: true,
            autoWidth: false,
            order: [[0, "desc"]],
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
                infoEmpty: "Mostrando 0 a 0 de 0 registros",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                zeroRecords: "No se encontraron registros coincidentes",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            }
        });

        // ---------- Eliminar rol (delegación de eventos) ----------
        $(document).on('click', '.btn-eliminar-rol', function () {
            const id = $(this).data('id');
            const nombre = $(this).data('nombre');
            eliminarRol(id, nombre);
        });

        // ---------- Llenar modal editar rol ----------
        $(document).on('click', '.btn-editar-rol', function () {
            const id = $(this).data('id');
            const nombre = $(this).data('nombre');
            const descripcion = $(this).data('descripcion');
            const estatus = $(this).data('estatus');

            $('#editRolId').val(id);
            $('#editRolNombre').val(nombre);
            $('#editRolDescripcion').val(descripcion);
            $('#editRolEstatus').val(estatus);
            $('#formEditarRol').data('url', '/roles/editar/' + id);
        });

        // ---------- Enviar formulario crear rol ----------
        $('#formCrearRol').on('submit', function (e) {
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

        // ---------- Enviar formulario editar rol ----------
        $('#formEditarRol').on('submit', function (e) {
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