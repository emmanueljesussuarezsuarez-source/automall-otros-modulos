document.addEventListener("DOMContentLoaded", function () {
    // 1. MENSAJES FLASH SWEETALERT2 (Estilo Citas)
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: categoria === 'success' ? '¡Éxito!' : (categoria === 'warning' ? 'Advertencia' : 'Aviso'),
                text: mensaje,
                icon: categoria === 'error' ? 'error' : (categoria === 'success' ? 'success' : 'info'),
                timer: 3500,
                timerProgressBar: true,
                confirmButtonColor: '#3085d6'
            });
        }
    });

    const form = document.getElementById("form-registro");

    const filtrarCedula = (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 10);
    };
    const filtrarTelefono = (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 11);
    };

    if (document.getElementById("cedula")) {
        document.getElementById("cedula").addEventListener("input", filtrarCedula);
    }
    if (document.getElementById("telefono")) {
        document.getElementById("telefono").addEventListener("input", filtrarTelefono);
    }
    if (document.getElementById("editar_telefono")) {
        document.getElementById("editar_telefono").addEventListener("input", filtrarTelefono);
    }

    const filtrarLetras = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]/g, "");
    };
    if (document.getElementById("nombre")) {
        document.getElementById("nombre").addEventListener("input", filtrarLetras);
    }
    if (document.getElementById("apellido")) {
        document.getElementById("apellido").addEventListener("input", filtrarLetras);
    }

    if (document.getElementById("email")) {
        document.getElementById("email").addEventListener("input", (e) => {
            e.target.value = e.target.value.replace(/\s/g, "");
        });
    }

    function mostrarMensajeError(input, mensaje) {
        // Buscamos el contenedor principal que envuelve al input o a su input-group
        const contenedorPadre = input.closest('.input-group') || input.parentElement;
        const contenedorPrincipal = contenedorPadre.parentElement;

        const existingError = contenedorPrincipal.querySelector('.mensaje-error');
        if (existingError) {
            existingError.remove();
        }

        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'mensaje-error text-danger small mt-1';
        mensajeDiv.textContent = mensaje;
        
        // Adjuntamos el mensaje justo debajo del grupo o contenedor del input
        contenedorPrincipal.appendChild(mensajeDiv);

        input.addEventListener('input', () => {
            mensajeDiv.remove();
        }, { once: true });
    }

   function validarCampo(input, condicion, mensaje) {
        const esValido = condicion(input.value);
        const contenedorPrincipal = (input.closest('.input-group') || input.parentElement).parentElement;

        if (esValido) {
            input.classList.remove("is-invalid");
            input.classList.add("is-valid");
            const existingError = contenedorPrincipal.querySelector('.mensaje-error');
            if (existingError) {
                existingError.remove();
            }
        } else {
            input.classList.remove("is-valid");
            input.classList.add("is-invalid");
            mostrarMensajeError(input, mensaje);
        }

        return esValido;
    }

    if (document.getElementById("cedula")) {
        document.getElementById("cedula").addEventListener("blur", () => {
            const input = document.getElementById("cedula");
            validarCampo(input, (val) => /^\d{6,10}$/.test(val.trim()), "La cédula debe tener entre 6 y 10 dígitos.");
        });
    }

    if (document.getElementById("nombre")) {
        document.getElementById("nombre").addEventListener("blur", () => {
            const input = document.getElementById("nombre");
            validarCampo(input, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.");
        });
    }

    if (document.getElementById("apellido")) {
        document.getElementById("apellido").addEventListener("blur", () => {
            const input = document.getElementById("apellido");
            validarCampo(input, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.");
        });
    }

    if (document.getElementById("telefono")) {
        document.getElementById("telefono").addEventListener("input", () => {
            const input = document.getElementById("telefono");
            validarCampo(input, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.");
        });
    }

    if (document.getElementById("direccion")) {
        document.getElementById("direccion").addEventListener("input", () => {
            const input = document.getElementById("direccion");
            validarCampo(input, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.");
        });
    }

        const emailInput = document.getElementById("email");

        // 1. Verificamos si el elemento existe una sola vez
        if (emailInput) { 
            emailInput.addEventListener("input", () => {
                // 2. Usamos la referencia guardada y pasamos directamente el valor recortado
                validarCampo(
                    emailInput, 
                    (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), 
                    "Ingrese un correo electrónico válido."
                );
            });
        }
    if (document.getElementById("password")) {
        document.getElementById("password").addEventListener("input", () => {
            const input = document.getElementById("password");
            validarCampo(input, (val) => /^(?=.*[A-Z])(?=.*[0-9])(?=.*[*#\/.])[A-Za-z0-9*#\/.]{8,}$/.test(val), "La clave debe tener al menos 8 caracteres, una mayúscula, un número y un caracter especial (*, #, / o .).");
        });
    }

    if (form) {
        form.addEventListener("submit", function (event) {
            let esFormularioValido = true;

            const cedula = document.getElementById("cedula");
            const nombre = document.getElementById("nombre");
            const apellido = document.getElementById("apellido");
            const telefono = document.getElementById("telefono");
            const direccion = document.getElementById("direccion");
            const email = document.getElementById("email");
            const password = document.getElementById("password");

            if (cedula && !validarCampo(cedula, (val) => /^\d{6,10}$/.test(val.trim()), "La cédula debe tener entre 6 y 10 dígitos.")) {
                esFormularioValido = false;
            }

            if (nombre && !validarCampo(nombre, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.")) {
                esFormularioValido = false;
            }

            if (apellido && !validarCampo(apellido, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.")) {
                esFormularioValido = false;
            }

            if (telefono && !validarCampo(telefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.")) {
                esFormularioValido = false;
            }

            if (direccion && !validarCampo(direccion, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.")) {
                esFormularioValido = false;
            }

            if (email && !validarCampo(email, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.")) {
                esFormularioValido = false;
            }

            if (password && !validarCampo(password, (val) => /^(?=.*[A-Z])(?=.*[0-9])(?=.*[*#\/.])[A-Za-z0-9*#\/.]{8,}$/.test(val), "La clave debe tener al menos 8 caracteres, una mayúscula, un número y un caracter especial (*, #, / o .).")) {
                esFormularioValido = false;
            }

            const inputFoto = document.getElementById("foto_perfil");
            const fotoErrorTexto = document.getElementById("foto-error-msg");
            
            if (inputFoto && inputFoto.files.length > 0) {
                const imagen = inputFoto.files[0];
                const formatosValidos = /(\.jpg|\.jpeg|\.png|\.webp)$/i;
                const tamañoMaximoBytes = 3 * 1024 * 1024;

                if (!formatosValidos.exec(imagen.name) || imagen.size > tamañoMaximoBytes) {
                    fotoErrorTexto.innerText = "Error: La imagen debe ser JPG, PNG o WEBP y pesar menos de 3MB.";
                    fotoErrorTexto.className = "form-text mt-2 text-danger fw-bold";
                    esFormularioValido = false;
                } else {
                    fotoErrorTexto.innerText = "Imagen cargada correctamente.";
                    fotoErrorTexto.className = "form-text mt-2 text-success fw-bold";
                }
            }

            if (!esFormularioValido) {
                event.preventDefault();
                event.stopPropagation();

                const primerCampoInvalido = document.querySelector(".is-invalid");
                if (primerCampoInvalido) {
                    primerCampoInvalido.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            }
        });
    }

    const formEditar = document.getElementById("form-editar");
    if (formEditar) {
        const editar_nombre = document.getElementById("editar_nombre");
        const editar_apellido = document.getElementById("editar_apellido");
        const editar_telefono = document.getElementById("editar_telefono");
        const editar_direccion = document.getElementById("editar_direccion");
        const editar_correo = document.getElementById("editar_correo");

        if (editar_nombre) {
            editar_nombre.addEventListener("input", filtrarLetras);
            editar_nombre.addEventListener("blur", () => {
                validarCampo(editar_nombre, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.");
            });
        }

        if (editar_apellido) {
            editar_apellido.addEventListener("input", filtrarLetras);
            editar_apellido.addEventListener("blur", () => {
                validarCampo(editar_apellido, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.");
            });
        }

        if (editar_telefono) {
            editar_telefono.addEventListener("input", (e) => {
                filtrarTelefono(e);
                validarCampo(editar_telefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.");
            });
        }

        if (editar_direccion) {
            editar_direccion.addEventListener("input", () => {
                validarCampo(editar_direccion, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.");
            });
        }

        if (editar_correo) {
            editar_correo.addEventListener("input", () => {
                validarCampo(editar_correo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.");
            });
        }

        formEditar.addEventListener("submit", function (event) {
            let esFormularioValido = true;

            if (editar_nombre && !validarCampo(editar_nombre, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.")) {
                esFormularioValido = false;
            }

            if (editar_apellido && !validarCampo(editar_apellido, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.")) {
                esFormularioValido = false;
            }

            if (editar_telefono && !validarCampo(editar_telefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.")) {
                esFormularioValido = false;
            }

            if (editar_direccion && !validarCampo(editar_direccion, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.")) {
                esFormularioValido = false;
            }

            if (editar_correo && !validarCampo(editar_correo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.")) {
                esFormularioValido = false;
            }

            if (!esFormularioValido) {
                event.preventDefault();
                event.stopPropagation();

                const primerCampoInvalido = formEditar.querySelector(".is-invalid");
                if (primerCampoInvalido) {
                    primerCampoInvalido.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            }
        });
    }

    const formsVendedores = document.querySelectorAll('form[id^="form-editar-vendedor-"]');
    formsVendedores.forEach(form => {
        const cedula = form.id.replace('form-editar-vendedor-', '');
        const nombre = document.getElementById('editar_nombre_' + cedula);
        const apellido = document.getElementById('editar_apellido_' + cedula);
        const telefono = document.getElementById('editar_telefono_' + cedula);
        const direccion = document.getElementById('editar_direccion_' + cedula);
        const correo = document.getElementById('editar_correo_' + cedula);

        if (nombre) {
            nombre.addEventListener('input', filtrarLetras);
            nombre.addEventListener('blur', () => {
                validarCampo(nombre, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.");
            });
        }

        if (apellido) {
            apellido.addEventListener('input', filtrarLetras);
            apellido.addEventListener('blur', () => {
                validarCampo(apellido, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.");
            });
        }

        if (telefono) {
            telefono.addEventListener('input', () => {
                validarCampo(telefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.");
            });
        }

        if (direccion) {
            direccion.addEventListener('input', () => {
                validarCampo(direccion, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.");
            });
        }

        if (correo) {
            correo.addEventListener('input', () => {
                validarCampo(correo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.");
            });
        }

        form.addEventListener('submit', function(e) {
            let valido = true;

            if (nombre && !validarCampo(nombre, (val) => val.trim().length > 0 && val.trim().length <= 50, "El nombre es obligatorio y máximo 50 caracteres.")) {
                valido = false;
            }

            if (apellido && !validarCampo(apellido, (val) => val.trim().length > 0 && val.trim().length <= 50, "El apellido es obligatorio y máximo 50 caracteres.")) {
                valido = false;
            }

            if (telefono && !validarCampo(telefono, (val) => /^\d{11}$/.test(val.trim()), "El teléfono debe tener exactamente 11 dígitos numéricos.")) {
                valido = false;
            }

            if (direccion && !validarCampo(direccion, (val) => /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s]{10,50}$/.test(val.trim()), "La dirección debe tener de 10 a 50 caracteres, solo letras, números y espacios.")) {
                valido = false;
            }

            if (correo && !validarCampo(correo, (val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val.trim()), "Ingrese un correo electrónico válido.")) {
                valido = false;
            }

            if (!valido) {
                e.preventDefault();
            }
        });
    });
});

function previewImage(input) {
    const preview = document.getElementById('img-preview');
    const icon = document.getElementById('preview-icon');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.remove('d-none');
            icon.classList.add('d-none');
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}