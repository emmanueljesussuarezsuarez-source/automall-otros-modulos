document.addEventListener("DOMContentLoaded", function () {
    if (typeof $ !== 'undefined' && $('#tablaVendedores').length) {
        $('#tablaVendedores').DataTable({
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

        $('#tablaVendedores').on('click', '.btn-cambiar-estado', function() {
            const cedula = $(this).data('cedula');
            const nombre = $(this).data('nombre');
            const estado = $(this).data('estado');

            const accion = estado == 1 ? 'inactivar' : 'activar';
            const urlDestino = '/vendedores/cambiar_estado/' + cedula;

            Swal.fire({
                title: '¿Confirmar Cambio de Estado?',
                text: '¿Está seguro de ' + accion + ' al vendedor ' + nombre + '?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#0d6efd',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, confirmar',
                cancelButtonText: 'Cancelar',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = urlDestino;
                }
            });
        });
    }

    $('.flash-item').each(function() {
        const category = $(this).attr('data-category');
        const message = $(this).attr('data-message');
        const isSuccess = category === 'success';
        
        Swal.fire({
            title: isSuccess ? '¡Éxito!' : '¡Atención!',
            text: message,
            icon: isSuccess ? 'success' : 'error',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: isSuccess ? '#198754' : '#dc3545'
        });
    });

    const formRegistro = document.getElementById("form-vendedor");

    const filtrarCedula = (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 10);
    };
    const filtrarTelefono = (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 11);
    };
    const filtrarLetras = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]/g, "").slice(0, 30);
    };
    const filtrarDireccion = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZÁÉÍÓÚáéíóúÑñ0-9, ]/g, "").slice(0, 100);
    };

    const inputCedula = document.getElementById("cedula");
    const inputNombre = document.getElementById("nombre");
    const inputApellido = document.getElementById("apellido");
    const inputTelefono = document.getElementById("telefono");
    const inputDireccion = document.getElementById("direccion");
    const inputEmail = document.getElementById("email");
    const inputPassword = document.getElementById("password");

    if (inputCedula) inputCedula.addEventListener("input", filtrarCedula);
    if (inputTelefono) inputTelefono.addEventListener("input", filtrarTelefono);
    if (inputNombre) inputNombre.addEventListener("input", filtrarLetras);
    if (inputApellido) inputApellido.addEventListener("input", filtrarLetras);
    if (inputDireccion) inputDireccion.addEventListener("input", filtrarDireccion);
    
    if (inputEmail) {
        inputEmail.addEventListener("input", (e) => {
            e.target.value = e.target.value.replace(/\s/g, "").slice(0, 100);
        });
    }

    function mostrarMensajeError(input, mensaje) {
        const contenedorPadre = input.closest('.input-group') || input.parentElement;
        const contenedorPrincipal = contenedorPadre.parentElement;

        const existingError = contenedorPrincipal.querySelector('.mensaje-error');
        if (existingError) existingError.remove();

        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'mensaje-error text-danger small mt-1';
        mensajeDiv.textContent = mensaje;
        contenedorPrincipal.appendChild(mensajeDiv);

        input.addEventListener('input', () => {
            mensajeDiv.remove();
        }, { once: true });
    }

    function validarCampo(input, condicion, mensaje) {
        if (!input) return true;
        const esValido = condicion(input.value);
        const contenedorPrincipal = (input.closest('.input-group') || input.parentElement).parentElement;

        if (esValido) {
            input.classList.remove("is-invalid");
            input.classList.add("is-valid");
            const existingError = contenedorPrincipal.querySelector('.mensaje-error');
            if (existingError) existingError.remove();
        } else {
            input.classList.remove("is-valid");
            input.classList.add("is-invalid");
            mostrarMensajeError(input, mensaje);
        }
        return esValido;
    }

    if (inputCedula) {
        inputCedula.addEventListener("blur", () => {
            validarCampo(inputCedula, (val) => /^\d{6,10}$/.test(val.trim()), "La cédula debe tener entre 6 y 10 dígitos.");
        });
    }
    if (inputNombre) {
        inputNombre.addEventListener("blur", () => {
            validarCampo(inputNombre, (val) => val.trim().length > 0 && val.trim().length <= 30, "El nombre es obligatorio y máximo 30 caracteres.");
        });
    }
    if (inputApellido) {
        inputApellido.addEventListener("blur", () => {
            validarCampo(inputApellido, (val) => val.trim().length > 0 && val.trim().length <= 30, "El apellido es obligatorio y máximo 30 caracteres.");
        });
    }
    if (inputTelefono) {
        inputTelefono.addEventListener("input", () => {
            validarCampo(inputTelefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.");
        });
    }
    if (inputDireccion) {
        inputDireccion.addEventListener("input", () => {
            validarCampo(inputDireccion, (val) => /^[a-zA-ZÁÉÍÓÚáéíóúÑñ0-9, ]{10,100}$/.test(val.trim()), "La dirección debe tener entre 10 y 100 caracteres válidos (solo letras, números y comas).");
        });
    }
    if (inputEmail) {
        inputEmail.addEventListener("input", () => {
            validarCampo(inputEmail, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.");
        });
    }
    if (inputPassword) {
        inputPassword.addEventListener("input", () => {
            validarCampo(inputPassword, (val) => /^(?=.*[A-Z])(?=.*[0-9])(?=.*[*#\/.])[A-Za-z0-9*#\/.]{8,}$/.test(val), "La clave debe tener al menos 8 caracteres, una mayúscula, un número y un carácter especial (*, #, / o .).");
        });
    }

    if (formRegistro) {
        formRegistro.addEventListener("submit", function (event) {
            let esValido = true;

            if (inputCedula && !validarCampo(inputCedula, (val) => /^\d{6,10}$/.test(val.trim()), "La cédula debe tener entre 6 y 10 dígitos.")) esValido = false;
            if (inputNombre && !validarCampo(inputNombre, (val) => val.trim().length > 0 && val.trim().length <= 30, "El nombre es obligatorio (máx 30 caracteres).")) esValido = false;
            if (inputApellido && !validarCampo(inputApellido, (val) => val.trim().length > 0 && val.trim().length <= 30, "El apellido es obligatorio (máx 30 caracteres).")) esValido = false;
            if (inputTelefono && !validarCampo(inputTelefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos.")) esValido = false;
            if (inputDireccion && !validarCampo(inputDireccion, (val) => /^[a-zA-ZÁÉÍÓÚáéíóúÑñ0-9, ]{10,100}$/.test(val.trim()), "Dirección requerida (10-100 caracteres, solo comas permitidas).")) esValido = false;
            if (inputEmail && !validarCampo(inputEmail, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Correo electrónico inválido.")) esValido = false;
            if (inputPassword && !validarCampo(inputPassword, (val) => /^(?=.*[A-Z])(?=.*[0-9])(?=.*[*#\/.])[A-Za-z0-9*#\/.]{8,}$/.test(val), "Contraseña inválida.")) esValido = false;

            if (!esValido) {
                event.preventDefault();
                event.stopPropagation();
                
                Swal.fire({
                    title: '¡Formulario incompleto!',
                    text: 'Por favor, corrige los errores marcados en rojo antes de registrar.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#dc3545'
                });

                const primerError = document.querySelector(".is-invalid");
                if (primerError) {
                    primerError.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            }
        });
    }

    const formsEditar = document.querySelectorAll('.form-vendedor-editar');
    formsEditar.forEach(form => {
        const editNombre = form.querySelector('input[name="nombre"]');
        const editApellido = form.querySelector('input[name="apellido"]');
        const editTelefono = form.querySelector('input[name="telefono"]');
        const editCorreo = form.querySelector('input[name="email"]');
        const editDireccion = form.querySelector('textarea[name="direccion"]');

        if (editNombre) {
            editNombre.addEventListener("input", (e) => {
                filtrarLetras(e);
                validarCampo(editNombre, (val) => val.trim().length > 0 && val.trim().length <= 30, "El nombre es obligatorio y máximo 30 caracteres.");
            });
            editNombre.addEventListener("blur", () => {
                validarCampo(editNombre, (val) => val.trim().length > 0 && val.trim().length <= 30, "El nombre es obligatorio y máximo 30 caracteres.");
            });
        }

        if (editApellido) {
            editApellido.addEventListener("input", (e) => {
                filtrarLetras(e);
                validarCampo(editApellido, (val) => val.trim().length > 0 && val.trim().length <= 30, "El apellido es obligatorio y máximo 30 caracteres.");
            });
            editApellido.addEventListener("blur", () => {
                validarCampo(editApellido, (val) => val.trim().length > 0 && val.trim().length <= 30, "El apellido es obligatorio y máximo 30 caracteres.");
            });
        }

        if (editTelefono) {
            editTelefono.addEventListener("input", (e) => {
                filtrarTelefono(e);
                validarCampo(editTelefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.");
            });
        }

        if (editCorreo) {
            editCorreo.addEventListener("input", (e) => {
                e.target.value = e.target.value.replace(/\s/g, "").slice(0, 100);
                validarCampo(editCorreo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.");
            });
        }

        if (editDireccion) {
            editDireccion.addEventListener("input", (e) => {
                filtrarDireccion(e);
                validarCampo(editDireccion, (val) => /^[a-zA-ZÁÉÍÓÚáéíóúÑñ0-9, ]{10,100}$/.test(val.trim()), "La dirección debe tener entre 10 y 100 caracteres válidos (solo letras, números y comas).");
            });
        }

        form.addEventListener("submit", function (e) {
            let validoModal = true;
            if (editNombre && !validarCampo(editNombre, (val) => val.trim().length > 0 && val.trim().length <= 30, "Nombre requerido (máx 30 caracteres).")) validoModal = false;
            if (editApellido && !validarCampo(editApellido, (val) => val.trim().length > 0 && val.trim().length <= 30, "Apellido requerido (máx 30 caracteres).")) validoModal = false;
            if (editTelefono && !validarCampo(editTelefono, (val) => /^\d{11}$/.test(val.trim()), "Teléfono de 11 dígitos.")) validoModal = false;
            if (editCorreo && !validarCampo(editCorreo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Correo inválido.")) validoModal = false;
            if (editDireccion && !validarCampo(editDireccion, (val) => /^[a-zA-ZÁÉÍÓÚáéíóúÑñ0-9, ]{10,100}$/.test(val.trim()), "Dirección inválida (10-100 caracteres, solo comas).")) validoModal = false;

            if (!validoModal) {
                e.preventDefault();
                Swal.fire({
                    title: '¡Formulario incompleto!',
                    text: 'Por favor, corrige los errores antes de guardar los cambios.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#dc3545'
                });
            }
        });
    });
});