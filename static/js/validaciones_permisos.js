document.addEventListener("DOMContentLoaded", function () {
    function mostrarMensajeError(input, mensaje) {
        const existingError = input.parentElement.querySelector('.mensaje-error');
        if (existingError) existingError.remove();

        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'mensaje-error text-danger small mt-1';
        mensajeDiv.textContent = mensaje;
        input.parentElement.appendChild(mensajeDiv);
    }

    function validarCampo(input, condicion, mensaje) {
        const valor = input.value.trim();
        const esValido = condicion(valor);

        if (esValido) {
            input.classList.remove("is-invalid");
            input.classList.add("is-valid");
            const existingError = input.parentElement.querySelector('.mensaje-error');
            if (existingError) existingError.remove();
        } else {
            input.classList.remove("is-valid");
            input.classList.add("is-invalid");
            mostrarMensajeError(input, mensaje);
        }

        return esValido;
    }

    const filtrarLetras = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]/g, "");
    };

    const filtrarLetrasMayusculas = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]/g, "").toUpperCase();
    };

    function validarRoles() {
        const inputsNombre = document.querySelectorAll('.input-nombre-rol');
        const inputsDescripcion = document.querySelectorAll('.input-descripcion-rol');
        const inputsEstatus = document.querySelectorAll('.input-estatus-rol');

        inputsNombre.forEach(input => {
            const funcionValidar = () => validarCampo(
                input, 
                (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{5,20}$/.test(val), 
                "El nombre del rol debe tener de 5 a 20 caracteres, solo letras."
            );

            input.addEventListener('input', (e) => {
                filtrarLetras(e);
                funcionValidar();
            });
            input.addEventListener('blur', funcionValidar);
        });

        inputsDescripcion.forEach(input => {
            const funcionValidar = () => validarCampo(
                input, 
                (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{10,50}$/.test(val), 
                "La descripción debe tener de 10 a 50 caracteres, solo letras."
            );

            input.addEventListener('input', (e) => {
                filtrarLetras(e);
                funcionValidar();
            });
            input.addEventListener('blur', funcionValidar);
        });

        inputsEstatus.forEach(input => {
            const funcionValidar = () => validarCampo(
                input, 
                (val) => val === "1" || val === "0", 
                "Debe seleccionar un estatus."
            );

            input.addEventListener('change', funcionValidar);
            input.addEventListener('blur', funcionValidar);
        });
    }

    function validarModulos() {
        const inputsNombre = document.querySelectorAll('.input-nombre-modulo');

        inputsNombre.forEach(input => {
            const funcionValidar = () => validarCampo(
                input, 
                (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{5,35}$/.test(val), 
                "El nombre del módulo debe tener de 5 a 35 caracteres, solo letras."
            );

            input.addEventListener('input', (e) => {
                filtrarLetras(e);
                funcionValidar();
            });
            input.addEventListener('blur', funcionValidar);
        });
    }

    function validarAcciones() {
        const inputsNombre = document.querySelectorAll('.input-nombre-accion');

        inputsNombre.forEach(input => {
            const funcionValidar = () => validarCampo(
                input, 
                (val) => /^[A-ZÁÉÍÓÚÑ\s]{5,15}$/.test(val), 
                "El nombre de la acción debe tener de 5 a 15 caracteres, solo letras en mayúsculas."
            );

            input.addEventListener('input', (e) => {
                filtrarLetrasMayusculas(e);
                funcionValidar();
            });
            input.addEventListener('blur', funcionValidar);
        });
    }

    validarRoles();
    validarModulos();
    validarAcciones();

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            validarRoles();
            validarModulos();
            validarAcciones();
        });
    });
});