document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("formLogin");
    const emailInput = document.getElementById("emailInput");
    const passwordInput = document.getElementById("passwordInput");
    const btnSubmit = document.getElementById("btnSubmit");
    const errorContainer = document.getElementById("js-error-container");
    const passwordHelp = document.getElementById("passwordHelp");

    // CAPTCHA DAVID
    const captchaInput = document.getElementById("captchaInput");
    const imgCaptcha = document.getElementById("imgCaptcha");
    const btnRecargarCaptcha = document.getElementById("btnRecargarCaptcha");
    const captchaHelp = document.getElementById("captchaHelp");

    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    // CAPTCHA DAVID
    // CI-LOG-06 FIX: se agrega parámetro preservarError para evitar que
    // validarFormulario() borre el mensaje de error del servidor al recargar el CAPTCHA.
    function recargarCaptcha(preservarError = false) {
        if (imgCaptcha) {
            imgCaptcha.src = `/captcha?t=${Date.now()}`;
        }
        if (captchaInput) {
            captchaInput.value = "";
        }
        if (captchaHelp) {
            captchaHelp.textContent = "Ingresa los 5 caracteres de la imagen.";
            captchaHelp.className = "form-text small text-muted mt-1";
        }
        if (!preservarError) {
            validarFormulario();
        }
    }

    if (btnRecargarCaptcha) {
        btnRecargarCaptcha.addEventListener("click", function (e) {
            e.preventDefault();
            recargarCaptcha();
            if (captchaInput) {
                captchaInput.focus();
            }
        });
    }

    function validarFormulario() {
        const emailValue = emailInput.value.trim();
        const passwordValue = passwordInput.value;
        const captchaValue = captchaInput ? captchaInput.value.trim() : "";
        let errores = [];

        const correoValido = emailRegex.test(emailValue) && emailValue.length <= 35; 
        if (emailValue !== "" && !correoValido) {
            errores.push("El formato del correo no es válido.");
        }

        const passwordValida = passwordValue.length >= 8 && passwordValue.length <= 20;

        if (passwordValue.length > 0 && passwordValue.length < 8) {
            passwordHelp.textContent = `Te faltan ${8 - passwordValue.length} caracteres para el mínimo.`;
            passwordHelp.className = "form-text small text-danger mt-1";
        } else if (passwordValue.length > 20) {
            passwordHelp.textContent = "Has superado el límite de 20 caracteres.";
            passwordHelp.className = "form-text small text-danger mt-1";
        } else if (passwordValida) {
            passwordHelp.textContent = "¡Formato de contraseña correcto!";
            passwordHelp.className = "form-text small text-success mt-1";
        } else {
            passwordHelp.textContent = "Debe tener entre 8 y 20 caracteres.";
            passwordHelp.className = "form-text small text-muted mt-1";
        }

        // CAPTCHA DAVID
        const captchaValido = captchaValue.length === 5;
        if (captchaHelp) {
            if (captchaValue.length > 0 && captchaValue.length < 5) {
                captchaHelp.textContent = `Te faltan ${5 - captchaValue.length} caracter(es) para completar el captcha.`;
                captchaHelp.className = "form-text small text-danger mt-1";
            } else if (captchaValido) {
                captchaHelp.textContent = "¡Código de captcha completo!";
                captchaHelp.className = "form-text small text-success mt-1";
            } else {
                captchaHelp.textContent = "Ingresa los 5 caracteres de la imagen.";
                captchaHelp.className = "form-text small text-muted mt-1";
            }
        }

        if (errores.length > 0) {
            errorContainer.innerHTML = `
                <div class="alert alert-warning py-2 border-0 shadow-sm mb-4 small d-flex align-items-center">
                    <i class="bi bi-exclamation-circle-fill me-2"></i>
                    <div>${errores[0]}</div>
                </div>`;
        } else {
            errorContainer.innerHTML = "";
        }

        btnSubmit.disabled = !(correoValido && passwordValida && captchaValido);
    }

    emailInput.addEventListener("input", function () {
        this.value = this.value.replace(/[^a-zA-Z0-9@._%+-]/g, "");
        validarFormulario();
    });

    passwordInput.addEventListener("input", function () {
        if (this.value.length > 20) {
            this.value = this.value.slice(0, 20);
        }
        validarFormulario();
    });

    // CAPTCHA DAVID
    if (captchaInput) {
        captchaInput.addEventListener("input", function () {
            this.value = this.value.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
            if (this.value.length > 5) {
                this.value = this.value.slice(0, 5);
            }
            validarFormulario();
        });

        captchaInput.addEventListener("blur", function () {
            if (this.value.trim().length > 0 && this.value.trim().length < 5) {
                if (captchaHelp) {
                    captchaHelp.textContent = "Debes completar los 5 caracteres del captcha.";
                    captchaHelp.className = "form-text small text-danger mt-1";
                }
            }
        });
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        // CAPTCHA DAVID
        const captchaValue = captchaInput ? captchaInput.value.trim() : "";
        if (captchaValue.length < 5) {
            if (captchaHelp) {
                captchaHelp.textContent = "Debes completar los 5 caracteres del captcha antes de iniciar sesión.";
                captchaHelp.className = "form-text small text-danger mt-1";
            }
            if (captchaInput) {
                captchaInput.focus();
            }
            return;
        }

        btnSubmit.disabled = true;
        const originalBtnText = btnSubmit.innerHTML;
        btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Verificando...`;

        // CAPTCHA DAVID
        const data = {
            email: emailInput.value.trim(),
            password: passwordInput.value,
            captcha: captchaValue
        };

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.status === 'success') {
                window.location.href = result.redirect;
            } else {
                errorContainer.innerHTML = `
                    <div class="alert alert-danger py-2 border-0 shadow-sm mb-4 small d-flex align-items-center">
                        <i class="bi bi-x-circle-fill me-2"></i>
                        <div>${result.message}</div>
                    </div>`;
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = originalBtnText;

                // CAPTCHA DAVID - CI-LOG-06 FIX: preservarError=true evita que
                // validarFormulario() borre el mensaje de error al recargar el CAPTCHA.
                recargarCaptcha(true);
            }
        } catch (error) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger py-2 border-0 shadow-sm mb-4 small d-flex align-items-center">
                    <i class="bi bi-wifi-off me-2"></i>
                    <div>Error de conexión con el servidor.</div>
                </div>`;
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = originalBtnText;

            // CAPTCHA DAVID
            recargarCaptcha(true);
        }
    });
});