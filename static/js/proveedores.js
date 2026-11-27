document.addEventListener('DOMContentLoaded', function () {

    // =========================================================================
    // 1. INICIALIZACIÓN DE DATATABLES
    // =========================================================================
    if ($('#tablaProveedores').length) {
        $('#tablaProveedores').DataTable({
            responsive: true,
            autoWidth: false,
            order: [[1, 'asc']], // Ordenar alfabéticamente por Razón Social
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
                infoEmpty: "Mostrando 0 a 0 de 0 registros",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                zeroRecords: "No se encontraron proveedores registrados",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            },
            drawCallback: function () {
                // Reactivar tooltips de Bootstrap en cada cambio de página
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            }
        });
    }

    // =========================================================================
    // 2. MENSAJES FLASH DE FLASK (Toasts con SweetAlert2)
    // =========================================================================
    const iconMap = {
        success: 'success',
        danger: 'error',
        warning: 'warning',
        info: 'info',
        message: 'info'
    };

    document.querySelectorAll('.flask-msg-data').forEach(function (el) {
        const msg = el.dataset.message;
        const cat = (el.dataset.category || 'info').toLowerCase();
        if (!msg) return;

        Swal.fire({
            icon: iconMap[cat] || 'info',
            title: msg,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3500,
            timerProgressBar: true
        });
    });

    // =========================================================================
    // 3. CONFIRMACIÓN CON SWEETALERT (Soporta paginación de DataTables)
    // =========================================================================
    $(document).on('submit', '.form-confirmar', function (e) {
        e.preventDefault();
        const form = this;

        Swal.fire({
            title: form.dataset.confirmTitle || '¿Está seguro?',
            text: form.dataset.confirm || '¿Desea continuar con esta acción?',
            icon: form.dataset.confirmIcon || 'warning',
            showCancelButton: true,
            confirmButtonText: form.dataset.confirmButton || 'Sí, continuar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: form.dataset.confirmColor || '#dc3545',
            cancelButtonColor: '#6c757d',
            reverseButtons: true,
            focusCancel: true
        }).then((result) => {
            if (result.isConfirmed) {
                form.classList.remove('form-confirmar');
                form.submit();
            }
        });
    });

});