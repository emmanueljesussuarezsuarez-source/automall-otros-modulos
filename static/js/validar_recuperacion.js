document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("#form-cambio-password");
    const nuevaPassword = document.querySelector("#nueva_password");
    const confirmarPassword = document.querySelector("#confirmar_password");
    const errorNueva = document.querySelector("#error-nueva-password");
    const errorConfirmar = document.querySelector("#error-confirmar-password");

    if (!form || !nuevaPassword || !confirmarPassword) return;

    function validarPassword(password) {
        const errores = [];

        if (password.length < 8) {
            errores.push("Debe tener al menos 8 caracteres.");
        }
        if (!/[A-Z]/.test(password)) {
            errores.push("Debe tener al menos una letra mayúscula.");
        }
        if (!/[a-z]/.test(password)) {
            errores.push("Debe tener al menos una letra minúscula.");
        }
        
        if (!/\d/.test(password)) {
            errores.push("Debe tener al menos un número.");
        }
        if (!/[!@#$%^&*(),.?":{}|<>_\-+=/\\\[\];\']/.test(password)) {
            errores.push("Debe tener al menos un carácter especial.");
        }

        return errores;
    }

    function mostrarError(elemento, mensajes) {
        if (!elemento) return;
        elemento.innerHTML = mensajes.length ? mensajes.map(m => `<div>${m}</div>`).join("") : "";
    }

    function validarCampos() {
        const erroresNueva = validarPassword(nuevaPassword.value.trim());
        mostrarError(errorNueva, erroresNueva);

        let erroresConfirmar = [];
        if (confirmarPassword.value.trim() === "") {
            erroresConfirmar.push("Confirma la contraseña.");
        } else if (nuevaPassword.value.trim() !== confirmarPassword.value.trim()) {
            erroresConfirmar.push("Las contraseñas no coinciden.");
        }
        mostrarError(errorConfirmar, erroresConfirmar);

        return erroresNueva.length === 0 && erroresConfirmar.length === 0;
    }

    nuevaPassword.addEventListener("input", validarCampos);
    confirmarPassword.addEventListener("input", validarCampos);

    form.addEventListener("submit", function (e) {
        if (!validarCampos()) {
            e.preventDefault();
        }
    });
});