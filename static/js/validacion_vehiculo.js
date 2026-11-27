// 1. FUNCIÓN GLOBAL PARA ELIMINAR 
function confirmarEliminar(placa) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Eliminarás el vehículo con placa " + placa + ". Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminarlo',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById('form-eliminar-' + placa).submit();
        }
    });
}

// 2. LÓGICA PRINCIPAL
document.addEventListener('DOMContentLoaded', function () {
    
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        Swal.fire({
            title: categoria === 'success' ? '¡Logrado!' : 'Aviso',
            text: mensaje,
            icon: categoria === 'error' ? 'error' : categoria, 
            timer: 3000,
            timerProgressBar: true,
            confirmButtonColor: '#3085d6'
        });
    });

    const form = document.querySelector('form:not([id^="form-eliminar"])');

    if (form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

        inputs.forEach(input => {
            ['input', 'blur'].forEach(evt => {
                input.addEventListener(evt, () => validarCampo(input));
            });
        });

        function validarCampo(input) {
            let esValido = true;
            let mensajeError = ""; 
            const valor = input.value.trim();

            if (input.type === 'file') {
                if (!input.files || input.files.length === 0) {
                    esValido = false;
                    mensajeError = "Debe seleccionar al menos una imagen.";
                } else {
                    esValido = true;
                }
            } else if (valor === "") {
                esValido = false;
                mensajeError = "Este campo es obligatorio.";
            } else {
                // --- VALIDACIÓN: COLOR (Solo letras y espacios) ---
                if (input.name === 'color') {
                    const regexSoloLetras = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
                    if (!regexSoloLetras.test(valor)) {
                        esValido = false;
                        mensajeError = "Solo letras (No se permiten puntos, comas ni símbolos).";
                    } else if (valor.length > 20) {
                        esValido = false;
                        mensajeError = "Máximo 20 caracteres.";
                    }
                }

                // --- VALIDACIÓN: PLACA (7-8 Caracteres, sin puntos/comas) ---
                if (input.name === 'placa') {
                    const regexPlaca = /^[A-Z0-9-]+$/i;
                    if (valor.length < 7 || valor.length > 8) {
                        esValido = false;
                        mensajeError = "La placa debe tener entre 7 y 8 caracteres.";
                    } else if (!regexPlaca.test(valor)) {
                        esValido = false;
                        mensajeError = "Solo letras, números y guiones (Sin puntos ni comas).";
                    }
                }

                // --- VALIDACIÓN: DESCRIPCIÓN (Letras, números, espacios, puntos y comas) ---
                if (input.name === 'descripcion_catalogo') {
                    const maxCaracteres = 100; 
                    // Permite letras, números, espacios, puntos y comas
                    const regexDescripcion = /^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,]+$/;

                    if (valor.length > maxCaracteres) {
                        esValido = false;
                        mensajeError = `Máximo ${maxCaracteres} caracteres.`;
                    } else if (!regexDescripcion.test(valor)) {
                        esValido = false;
                        mensajeError = "No se permiten símbolos especiales como @, #, $, etc.";
                    }
                }

                // --- VALIDACIÓN: AÑO ---
                if (input.name === 'anio') {
                    const anioActual = new Date().getFullYear();
                    const anioIngresado = parseInt(valor);
                    if (isNaN(anioIngresado) || anioIngresado < 1886 || anioIngresado > anioActual + 1) {
                        esValido = false;
                        mensajeError = `Rango válido: 1900 - ${anioActual + 1}.`;
                    }
                }

                // --- VALIDACIÓN: KILOMETRAJE ---
                if (input.name === 'kilometraje') {
                    const km = parseFloat(valor);
                    if (isNaN(km) || km < 0) {
                        esValido = false;
                        mensajeError = "Ingrese un kilometraje válido.";
                    }
                }

                // --- VALIDACIÓN: PRECIO ---
                if (input.name === 'precio') {
                    const precio = parseFloat(valor);
                    if (isNaN(precio) || precio <= 0) {
                        esValido = false;
                        mensajeError = "El precio debe ser mayor a 0.";
                    }
                }
            }

            // --- GESTIÓN VISUAL DEL ERROR ---
            let feedback = input.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.style.color = '#dc3545';
                feedback.style.fontSize = '0.85em';
                feedback.style.marginTop = '4px';
                input.parentNode.appendChild(feedback);
            }

            if (esValido) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
                feedback.style.display = 'none';
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                feedback.innerText = mensajeError;
                feedback.style.display = 'block';
            }
            return esValido;
        }

        form.addEventListener('submit', async function (e) {
            e.preventDefault(); 

            let formValido = true;
            inputs.forEach(input => {
                if (!validarCampo(input)) formValido = false;
            });

            if (!formValido) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Verifique los datos',
                    text: 'Hay campos con errores o caracteres no permitidos.',
                    confirmButtonColor: '#3085d6'
                });
                return;
            }

            Swal.fire({
                title: 'Guardando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form)
                });
                const result = await response.json();

                if (response.ok) {
                    const esEdicion = window.location.pathname.includes('editar');
                    Swal.fire({
                        icon: 'success',
                        title: esEdicion ? '¡Actualizado!' : '¡Registrado!',
                        text: result.message,
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.href = "/vehiculos-lista"; 
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: result.message });
                }
            } catch (error) {
                Swal.fire({ icon: 'error', title: 'Error', text: 'Error de conexión con el servidor.' });
            }
        });
    }
});