document.addEventListener('DOMContentLoaded', function() {

    // ==========================================
    //   0. INICIALIZACIÓN DE DATATABLES
    // ==========================================
    if ($('#tablaModelos').length) {
        $('#tablaModelos').DataTable({
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

    // --- 1. FUNCIÓN REUTILIZABLE PARA ALERTAS ---
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

        return Swal.fire(configuracion).then(() => {
            if (icono === 'success') {
                window.location.reload(); 
            }
        });
    };

    // --- 2. VALIDACIÓN VISUAL EN TIEMPO REAL ---
    const validarInputModelo = (input) => {
        const valor = input.value;
        const regexSoloLetras = /^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]*$/;
        const limite = 20;
        
        const esValido = valor.length >= 2 && valor.length <= limite && regexSoloLetras.test(valor);

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

    const inputNombre = document.getElementById('nombre_modelo');
    const inputEditNombre = document.getElementById('edit_nombre_modelo');

    if (inputNombre) {
        inputNombre.addEventListener('input', () => validarInputModelo(inputNombre));
    }
    if (inputEditNombre) {
        inputEditNombre.addEventListener('input', () => validarInputModelo(inputEditNombre));
    }

    // ==========================================
    //   3. LÓGICA DEL MODAL (DELEGACIÓN PARA DATATABLES)
    // ==========================================
    const modalEditarElement = document.getElementById('modalEditar');
    const formEditar = document.getElementById('formEditar');

    $(document).on('click', '.btn-editar', function() {
        const id = $(this).attr('data-id');
        const nombre = $(this).attr('data-nombre');
        const marca = $(this).attr('data-marca');

        document.getElementById('edit_nombre_modelo').value = nombre;
        document.getElementById('edit_cod_marca').value = marca;
        
        if (document.getElementById('edit_estado')) {
            document.getElementById('edit_estado').value = 'Activo';
        }
        
        formEditar.action = `/modelos/editar/${id}`;

        validarInputModelo(inputEditNombre);

        const modal = new bootstrap.Modal(modalEditarElement);
        modal.show();
    });

    // ==========================================
    //   4. REGISTRO DE MODELOS (AJAX)
    // ==========================================
    const formModelo = document.getElementById('formModelo');
    if (formModelo) {
        formModelo.addEventListener('submit', async function(e) {
            e.preventDefault();

            const codMarca = document.getElementById('cod_marca').value;

            if (!validarInputModelo(inputNombre)) {
                return mostrarAlerta('Error', 'El nombre debe tener entre 2 y 20 caracteres y no contener números ni símbolos.', 'error');
            }
            if (codMarca === "" || codMarca === "0") {
                return mostrarAlerta('Error', 'Debe seleccionar una marca válida.', 'error');
            }

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                });
                const result = await response.json();

                if (result.status === 'success') {
                    mostrarAlerta('¡Excelente!', result.message, 'success');
                } else {
                    mostrarAlerta('Error', result.message, 'error');
                }
            } catch (error) {
                mostrarAlerta('Error', 'No se pudo conectar con el servidor.', 'error');
            }
        });
    }

    // ==========================================
    //   5. EDICIÓN DE MODELOS (AJAX)
    // ==========================================
    if (formEditar) {
        formEditar.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (!validarInputModelo(inputEditNombre)) {
                return mostrarAlerta('Error', 'El nombre editado no es válido.', 'error');
            }

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                });
                const result = await response.json();

                if (result.status === 'success') {
                    mostrarAlerta('¡Actualizado!', result.message, 'success');
                } else {
                    mostrarAlerta('Error', result.message, 'error');
                }
            } catch (error) {
                mostrarAlerta('Error', 'Error de conexión con el servidor.', 'error');
            }
        });
    }

    // ==========================================
    //   6. ELIMINACIÓN LÓGICA (DELEGACIÓN PARA DATATABLES)
    // ==========================================
    $(document).on('click', '.btn-eliminar-modelo', function(e) {
        e.preventDefault();
        const id = $(this).attr('data-id');
        const url = `/modelos/eliminar/${id}`;

        Swal.fire({
            title: '¿Eliminar Modelo?',
            text: "El modelo se eliminará permanentemente.",
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
                    mostrarAlerta('Error', 'No se pudo procesar la eliminación.', 'error');
                }
            }
        });
    });

});