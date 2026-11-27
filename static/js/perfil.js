document.addEventListener("DOMContentLoaded", function () {
    
    const mainContainer = document.getElementById("perfil-main-container");
    if (mainContainer) {
        const swalIcon = mainContainer.dataset.swalIcon;
        const swalTitle = mainContainer.dataset.swalTitle;
        const swalText = mainContainer.dataset.swalText;

        if (swalIcon && swalTitle && swalText) {
            Swal.fire({
                icon: swalIcon,
                title: swalTitle,
                text: swalText,
                confirmButtonText: "Aceptar"
            });
        }
    }

    const filtrarTelefono = (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 11);
    };

    const filtrarDireccion = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9,\s]/g, "").slice(0, 100);
    };

    const filtrarCorreo = (e) => {
        let val = e.target.value;
        // Solo permitir letras, números, puntos, guiones, guion bajo y una sola arroba
        val = val.replace(/[^a-zA-Z0-9.@-_]/g, '');
        const partes = val.split('@');
        if (partes.length > 2) {
            val = partes[0] + '@' + partes.slice(1).join('');
        }
        e.target.value = val.slice(0, 100);
    };

    const filtrarRespuesta = (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-Z0-9]/g, "").slice(0, 30);
    };

    function mostrarMensajeDebajo(inputElem, mensaje) {
        inputElem.parentElement.querySelectorAll('.mensaje-error-simple').forEach(el => el.remove());
        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'mensaje-error-simple text-danger small mt-1';
        mensajeDiv.textContent = mensaje;
        inputElem.insertAdjacentElement('afterend', mensajeDiv);

        const limpiar = function () {
            mensajeDiv.remove();
            inputElem.removeEventListener('input', limpiar);
            inputElem.removeEventListener('change', limpiar);
            inputElem.removeEventListener('blur', limpiar);
        };

        inputElem.addEventListener('input', limpiar, { once: true });
        inputElem.addEventListener('change', limpiar, { once: true });
        inputElem.addEventListener('blur', limpiar, { once: true });
    }

    function limpiarError(campo) {
        const contenedor = campo.parentElement;
        if (!contenedor) return;
        contenedor.querySelectorAll('.mensaje-error-simple').forEach(el => el.remove());
    }

    function setFieldError(campo, mensaje) {
        limpiarError(campo);
        mostrarMensajeDebajo(campo, mensaje);
    }

    function validarTelefono(campo) {
        const val = campo.value.trim();
        if (val === '') {
            setFieldError(campo, 'El teléfono es obligatorio.');
            return false;
        }
        if (!/^\d{11}$/.test(val)) {
            setFieldError(campo, 'El teléfono debe tener exactamente 11 dígitos numéricos.');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarCorreo(campo) {
        const val = campo.value.trim();
        if (val === '') {
            setFieldError(campo, 'El correo electrónico es obligatorio.');
            return false;
        }
        // Expresión regular robusta para validar formato de correo estándar
        const regexCorreo = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!regexCorreo.test(val)) {
            setFieldError(campo, 'Ingrese un correo electrónico válido (ej: usuario@dominio.com).');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarDireccion(campo) {
        const val = campo.value.trim();
        if (val === '') {
            setFieldError(campo, 'La dirección es obligatoria.');
            return false;
        }
        if (val.length < 15) {
            setFieldError(campo, 'La dirección debe tener al menos 15 caracteres.');
            return false;
        }
        if (val.length > 100) {
            setFieldError(campo, 'La dirección no puede exceder los 100 caracteres.');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarFoto(campo) {
        if (!campo.files || campo.files.length === 0) {
            limpiarError(campo);
            return true;
        }
        const archivo = campo.files[0];
        const extensionesPermitidas = ['jpg', 'jpeg', 'png'];
        const extensionArchivo = archivo.name.split('.').pop().toLowerCase();
        if (!extensionesPermitidas.includes(extensionArchivo)) {
            setFieldError(campo, 'Formato de imagen no válido. Use JPG, JPEG o PNG.');
            campo.value = '';
            return false;
        }
        const tamanoMaximoBytes = 2 * 1024 * 1024;
        if (archivo.size > tamanoMaximoBytes) {
            setFieldError(campo, 'La imagen no debe superar los 2MB.');
            campo.value = '';
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarPasswordSegura(campo) {
        const val = campo.value;
        if (val.trim() === '') {
            setFieldError(campo, 'La contraseña es obligatoria.');
            return false;
        }
        if (val.length < 8) {
            setFieldError(campo, 'La contraseña debe tener al menos 8 caracteres.');
            return false;
        }
        if (!/[A-Z]/.test(val)) {
            setFieldError(campo, 'La contraseña debe contener al menos una mayúscula.');
            return false;
        }
        if (!/[^a-zA-Z0-9]/.test(val)) {
            setFieldError(campo, 'La contraseña debe contener al menos un carácter especial.');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarConfirmacion(campoConfirmar, campoOriginal) {
        if (campoConfirmar.value !== campoOriginal.value) {
            setFieldError(campoConfirmar, 'La confirmación no coincide.');
            return false;
        }
        limpiarError(campoConfirmar);
        return true;
    }

    function validarPregunta(campo) {
        if (campo.value === '') {
            setFieldError(campo, 'Debe seleccionar una pregunta de seguridad.');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarRespuesta(campo) {
        const val = campo.value.trim();
        if (val === '') {
            setFieldError(campo, 'La respuesta es obligatoria.');
            return false;
        }
        if (val.length < 10) {
            setFieldError(campo, 'La respuesta debe tener al menos 10 caracteres.');
            return false;
        }
        if (val.length > 30) {
            setFieldError(campo, 'La respuesta no puede exceder los 30 caracteres.');
            return false;
        }
        if (!/^[a-zA-Z0-9]+$/.test(val)) {
            setFieldError(campo, 'La respuesta solo puede contener letras y números.');
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarPreguntasDistintas(campo1, campo2) {
        if (campo1.value && campo2.value && campo1.value === campo2.value) {
            setFieldError(campo2, 'Debe seleccionar dos preguntas diferentes.');
            return false;
        }
        limpiarError(campo2);
        return true;
    }

    const formDatos = document.querySelector('form[action*="actualizar_datos_perfil"]');
    const formPasswordTab = document.querySelector('form[action*="cambiar_password_perfil"]');
    const formGuardarPreguntas = document.querySelector('form[action*="guardar_preguntas"]');
    const formActualizarPreguntas = document.querySelector('form[action*="actualizar_preguntas"]');
    const formModalPassword = document.querySelector('#modalPassword form');

    if (formDatos) {
        formDatos.addEventListener('submit', function (e) {
            const correo = formDatos.querySelector('input[name="correo"]');
            const telefono = formDatos.querySelector('input[name="telefono"]');
            const direccion = formDatos.querySelector('textarea[name="direccion"]');
            const foto = formDatos.querySelector('input[name="foto_perfil"]');
            let error = false;

            if (!validarCorreo(correo)) error = true;
            if (!validarTelefono(telefono)) error = true;
            if (!validarDireccion(direccion)) error = true;
            if (foto && !validarFoto(foto)) error = true;

            if (error) e.preventDefault();
        });
    }

    const passwordForms = [formPasswordTab, formModalPassword].filter(Boolean);
    passwordForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const actual = form.querySelector('input[name="password_actual"]');
            const nueva = form.querySelector('input[name="nueva_password"]');
            const confirmar = form.querySelector('input[name="confirmar_password"]');
            let error = false;

            if (actual && actual.value.trim() === '') {
                setFieldError(actual, 'Debe ingresar la contraseña actual.');
                error = true;
            } else if (actual) {
                limpiarError(actual);
            }

            if (nueva && !validarPasswordSegura(nueva)) error = true;
            if (confirmar && nueva && !validarConfirmacion(confirmar, nueva)) error = true;

            if (error) e.preventDefault();
        });
    });

    if (formGuardarPreguntas) {
        formGuardarPreguntas.addEventListener('submit', function (e) {
            const p1 = formGuardarPreguntas.querySelector('select[name="pregunta_1"]');
            const p2 = formGuardarPreguntas.querySelector('select[name="pregunta_2"]');
            const r1 = formGuardarPreguntas.querySelector('input[name="respuesta_1"]');
            const c1 = formGuardarPreguntas.querySelector('input[name="confirmar_respuesta_1"]');
            const r2 = formGuardarPreguntas.querySelector('input[name="respuesta_2"]');
            const c2 = formGuardarPreguntas.querySelector('input[name="confirmar_respuesta_2"]');
            let error = false;

            if (!validarPregunta(p1)) error = true;
            if (!validarPregunta(p2)) error = true;
            if (!validarPreguntasDistintas(p1, p2)) error = true;
            if (!validarRespuesta(r1)) error = true;
            if (!validarConfirmacion(c1, r1)) error = true;
            if (!validarRespuesta(r2)) error = true;
            if (!validarConfirmacion(c2, r2)) error = true;

            if (error) e.preventDefault();
        });
    }

    if (formActualizarPreguntas) {
        formActualizarPreguntas.addEventListener('submit', function (e) {
            const rv1 = formActualizarPreguntas.querySelector('input[name="respuesta_vieja_1"]');
            const rv2 = formActualizarPreguntas.querySelector('input[name="respuesta_vieja_2"]');
            const p1 = formActualizarPreguntas.querySelector('select[name="pregunta_nueva_1"]');
            const p2 = formActualizarPreguntas.querySelector('select[name="pregunta_nueva_2"]');
            const r1 = formActualizarPreguntas.querySelector('input[name="respuesta_nueva_1"]');
            const c1 = formActualizarPreguntas.querySelector('input[name="confirmar_respuesta_nueva_1"]');
            const r2 = formActualizarPreguntas.querySelector('input[name="respuesta_nueva_2"]');
            const c2 = formActualizarPreguntas.querySelector('input[name="confirmar_respuesta_nueva_2"]');
            let error = false;

            if (!validarRespuesta(rv1)) error = true;
            if (!validarRespuesta(rv2)) error = true;
            if (!validarPregunta(p1)) error = true;
            if (!validarPregunta(p2)) error = true;
            if (!validarPreguntasDistintas(p1, p2)) error = true;
            if (!validarRespuesta(r1)) error = true;
            if (!validarConfirmacion(c1, r1)) error = true;
            if (!validarRespuesta(r2)) error = true;
            if (!validarConfirmacion(c2, r2)) error = true;

            if (error) e.preventDefault();
        });
    }

    // Event listeners para Correo en tiempo real
    document.querySelectorAll('input[name="correo"]').forEach(function (campo) {
        campo.addEventListener('input', function (e) {
            filtrarCorreo(e);
            validarCorreo(campo);
        });
        campo.addEventListener('blur', function () { validarCorreo(campo); });
    });

    document.querySelectorAll('input[name="telefono"]').forEach(function (campo) {
        campo.addEventListener('input', function (e) {
            filtrarTelefono(e);
            validarTelefono(campo);
        });
        campo.addEventListener('blur', function () { validarTelefono(campo); });
    });

    document.querySelectorAll('textarea[name="direccion"]').forEach(function (campo) {
        campo.addEventListener('input', function (e) {
            filtrarDireccion(e);
            validarDireccion(campo);
        });
        campo.addEventListener('blur', function () { validarDireccion(campo); });
    });

    document.querySelectorAll('input[name="foto_perfil"]').forEach(function (campo) {
        campo.addEventListener('change', function () { validarFoto(campo); });
    });

    document.querySelectorAll('input[name="password_actual"], input[name="nueva_password"], input[name="confirmar_password"]').forEach(function (campo) {
        campo.addEventListener('input', function () {
            const form = campo.closest('form');
            const nueva = form.querySelector('input[name="nueva_password"]');
            const confirmar = form.querySelector('input[name="confirmar_password"]');
            if (campo.name === 'nueva_password') validarPasswordSegura(campo);
            if (campo.name === 'confirmar_password' && nueva) validarConfirmacion(confirmar, nueva);
            if (campo.name === 'password_actual' && campo.value.trim() !== '') limpiarError(campo);
        });
        campo.addEventListener('blur', function () {
            const form = campo.closest('form');
            const nueva = form.querySelector('input[name="nueva_password"]');
            const confirmar = form.querySelector('input[name="confirmar_password"]');
            if (campo.name === 'nueva_password') validarPasswordSegura(campo);
            if (campo.name === 'confirmar_password' && nueva) validarConfirmacion(confirmar, nueva);
        });
    });

    document.querySelectorAll('select[name="pregunta_1"], select[name="pregunta_2"], select[name="pregunta_nueva_1"], select[name="pregunta_nueva_2"]').forEach(function (campo) {
        campo.addEventListener('change', function () { validarPregunta(campo); });
        campo.addEventListener('blur', function () { validarPregunta(campo); });
    });

    document.querySelectorAll('input[name="respuesta_1"], input[name="respuesta_2"], input[name="respuesta_vieja_1"], input[name="respuesta_vieja_2"], input[name="respuesta_nueva_1"], input[name="respuesta_nueva_2"]').forEach(function (campo) {
        campo.addEventListener('input', function (e) {
            filtrarRespuesta(e);
            validarRespuesta(campo);
            const form = campo.closest('form');
            if (form) {
                if (campo.name === 'respuesta_1') {
                    const confirmar = form.querySelector('input[name="confirmar_respuesta_1"]');
                    if (confirmar && confirmar.value) validarConfirmacion(confirmar, campo);
                } else if (campo.name === 'respuesta_2') {
                    const confirmar = form.querySelector('input[name="confirmar_respuesta_2"]');
                    if (confirmar && confirmar.value) validarConfirmacion(confirmar, campo);
                } else if (campo.name === 'respuesta_nueva_1') {
                    const confirmar = form.querySelector('input[name="confirmar_respuesta_nueva_1"]');
                    if (confirmar && confirmar.value) validarConfirmacion(confirmar, campo);
                } else if (campo.name === 'respuesta_nueva_2') {
                    const confirmar = form.querySelector('input[name="confirmar_respuesta_nueva_2"]');
                    if (confirmar && confirmar.value) validarConfirmacion(confirmar, campo);
                }
            }
        });
        campo.addEventListener('blur', function () {
            validarRespuesta(campo);
        });
    });

    document.querySelectorAll('input[name="confirmar_respuesta_1"], input[name="confirmar_respuesta_2"], input[name="confirmar_respuesta_nueva_1"], input[name="confirmar_respuesta_nueva_2"]').forEach(function (campo) {
        campo.addEventListener('input', function (e) {
            filtrarRespuesta(e);
            const form = campo.closest('form');
            if (form) {
                let original = null;
                if (campo.name === 'confirmar_respuesta_1') {
                    original = form.querySelector('input[name="respuesta_1"]');
                } else if (campo.name === 'confirmar_respuesta_2') {
                    original = form.querySelector('input[name="respuesta_2"]');
                } else if (campo.name === 'confirmar_respuesta_nueva_1') {
                    original = form.querySelector('input[name="respuesta_nueva_1"]');
                } else if (campo.name === 'confirmar_respuesta_nueva_2') {
                    original = form.querySelector('input[name="respuesta_nueva_2"]');
                }
                if (original) validarConfirmacion(campo, original);
            }
        });
        campo.addEventListener('blur', function () {
            const form = campo.closest('form');
            if (form) {
                let original = null;
                if (campo.name === 'confirmar_respuesta_1') {
                    original = form.querySelector('input[name="respuesta_1"]');
                } else if (campo.name === 'confirmar_respuesta_2') {
                    original = form.querySelector('input[name="respuesta_2"]');
                } else if (campo.name === 'confirmar_respuesta_nueva_1') {
                    original = form.querySelector('input[name="respuesta_nueva_1"]');
                } else if (campo.name === 'confirmar_respuesta_nueva_2') {
                    original = form.querySelector('input[name="respuesta_nueva_2"]');
                }
                if (original) validarConfirmacion(campo, original);
            }
        });
    });
});