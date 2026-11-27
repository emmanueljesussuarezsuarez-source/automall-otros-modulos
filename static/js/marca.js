document.addEventListener('DOMContentLoaded', function() {

    // ==========================================
    //   0. INICIALIZACIÓN DE DATATABLES
    // ==========================================
    if ($('#tablaMarcas').length) {
        $('#tablaMarcas').DataTable({
            responsive: true,
            autoWidth: false,
            language: {
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
                infoEmpty: "Mostrando 0 a 0 de 0 registros",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                zeroRecords: "No se encontraron resultados",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            }
        });
    }

    // --- REUTILIZABLE: FUNCIÓN PARA MOSTRAR ALERTAS ---
    const mostrarAlerta = (titulo, mensaje, icono) => {
        let configuracion = {
            title: titulo,
            text: mensaje,
            icon: icono,
            confirmButtonColor: '#3085d6'
        };

        if (icono === 'success') {
            configuracion.timer = 2000;
            configuracion.showConfirmButton = false;
        }

        Swal.fire(configuracion).then(() => {
            if (icono === 'success') {
                window.location.reload(); 
            }
        });
    };

    // --- FUNCIÓN DE VALIDACIÓN VISUAL ---
    const validarInputMarca = (input) => {
        const valor = input.value;
        const regexLetras = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/;
        const limite = 20;

        const esValido = regexLetras.test(valor) && valor.length <= limite && valor.length >= 2;

        if (valor.length === 0) {
            input.style.color = '';
            input.style.borderColor = '';
            input.classList.remove('is-valid', 'is-invalid');
        } else if (esValido) {
            input.style.color = 'green';
            input.style.borderColor = 'green';
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.style.color = 'red';
            input.style.borderColor = 'red';
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
        return esValido;
    };

    // ==========================================
    //   1. REGISTRO DE MARCAS (AJAX)
    // ==========================================
    const formMarca = document.getElementById('formMarca');
    const inputNombre = document.getElementById('nombre_marca');

    if (inputNombre) {
        inputNombre.addEventListener('input', () => validarInputMarca(inputNombre));
    }

    if (formMarca) {
        formMarca.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!validarInputMarca(inputNombre)) {
                return mostrarAlerta('Error', 'El nombre debe tener entre 2 y 20 caracteres, sin números ni símbolos.', 'error');
            }

            const formData = new FormData(formMarca);
            try {
                const response = await fetch(formMarca.action, { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    mostrarAlerta('¡Registrado!', data.message, 'success');
                } else {
                    mostrarAlerta('Error', data.message, 'error');
                }
            } catch (error) {
                mostrarAlerta('Error', 'No se pudo conectar con el servidor.', 'error');
            }
        });
    }

    // ==========================================
    //   2. EDICIÓN DE MARCAS (DELEGACIÓN PARA DATATABLES)
    // ==========================================
    const modalElement = document.getElementById('modalEditarMarca');
    const formEditar = document.getElementById('formEditarMarca');
    const inputEditNombre = document.getElementById('edit_nombre_marca');

    if (inputEditNombre) {
        inputEditNombre.addEventListener('input', () => validarInputMarca(inputEditNombre));
    }
    
    // Delegación con jQuery para soportar las filas paginadas de DataTables
    $(document).on('click', '.btn-editar-marca', function() {
        const id = $(this).attr('data-id');
        const nombre = $(this).attr('data-nombre');
        const estado = $(this).attr('data-estado') || 'Activo';

        document.getElementById('edit_nombre_marca').value = nombre;
        document.getElementById('edit_estado_marca').value = estado;
        formEditar.action = `/marcas/editar/${id}`;

        validarInputMarca(inputEditNombre);

        const modalEditar = new bootstrap.Modal(modalElement);
        modalEditar.show();
    });

    if (formEditar) {
        formEditar.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!validarInputMarca(inputEditNombre)) {
                return mostrarAlerta('Error', 'El nombre editado no es válido.', 'error');
            }

            const formData = new FormData(formEditar);
            try {
                const response = await fetch(formEditar.action, { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    mostrarAlerta('¡Actualizado!', data.message, 'success');
                } else {
                    mostrarAlerta('Error', data.message, 'error');
                }
            } catch (error) {
                mostrarAlerta('Error', 'Error al procesar la actualización.', 'error');
            }
        });
    }

    // ==========================================
    //   3. ELIMINACIÓN LÓGICA (DELEGACIÓN PARA DATATABLES)
    // ==========================================
    $(document).on('click', '.btn-eliminar-marca', function(e) {
        e.preventDefault();
        const id = $(this).attr('data-id');
        const url = `/marcas/eliminar/${id}`;

        Swal.fire({
            title: '¿Estás seguro?',
            text: "La marca se eliminará permanentemente.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch(url, { method: 'POST' });
                    const data = await response.json();
                    if (data.status === 'success') {
                        mostrarAlerta('Eliminado', data.message, 'success');
                    } else {
                        mostrarAlerta('Error', data.message, 'error');
                    }
                } catch (error) {
                    mostrarAlerta('Error', 'No se pudo eliminar la marca.', 'error');
                }
            }
        });
    });

});