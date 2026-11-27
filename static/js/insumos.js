document.addEventListener('DOMContentLoaded', function () {

    // =========================================================================
    // 1. INICIALIZACIÓN DE DATATABLES (Idéntico a Mantenimiento y Compras)
    // =========================================================================
    if ($('#tablaInsumos').length) {
        $('#tablaInsumos').DataTable({
            responsive: true,
            autoWidth: false,
            order: [[0, 'desc']], // Ordenar por código descendente
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
                infoEmpty: "Mostrando 0 a 0 de 0 registros",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                zeroRecords: "No se encontraron insumos registrados",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            },
            drawCallback: function () {
                // Reactivar tooltips de Bootstrap en cada paginación
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
    // 3. CONFIRMACIÓN PARA ELIMINAR INSUMO CON SWEETALERT2
    // =========================================================================
    $(document).on('click', '.btn-eliminar-insumo', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');
        const nombreInsumo = $(this).data('nombre') || 'este insumo';

        Swal.fire({
            title: '¿Eliminar insumo?',
            text: `¿Estás seguro de eliminar "${nombreInsumo}"? Se eliminarán también las compras asociadas a este insumo.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            reverseButtons: true,
            focusCancel: true
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = url;
            }
        });
    });

});