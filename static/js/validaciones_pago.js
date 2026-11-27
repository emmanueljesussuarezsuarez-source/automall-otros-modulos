// ==========================================
// FUNCIONES GLOBALES (Llamadas desde el HTML)
// ==========================================
window.cargarDeudasCliente = function () {
    const cedula = document.getElementById('cedula_cliente')?.value;
    const selectCuentas = document.getElementById('cod_cuentas');
    const lblTotal = document.getElementById('lbl_total');
    const lblSaldo = document.getElementById('lbl_saldo');
    const saldoActualVal = document.getElementById('saldo_actual_val');

    if (lblTotal) lblTotal.innerText = "$ 0.00";
    if (lblSaldo) lblSaldo.innerText = "$ 0.00";
    if (saldoActualVal) saldoActualVal.value = "0";
    document.getElementById('bloque_cuotas_cuenta')?.classList.add('d-none');

    if (!cedula) return;
    if (selectCuentas) {
        selectCuentas.innerHTML = '<option value="" disabled selected>Buscando vehículos...</option>';
    }

    fetch(`/pagos/obtener_deudas/${encodeURIComponent(cedula)}`)
        .then(response => response.json())
        .then(data => {
            if (!selectCuentas) return;
            selectCuentas.innerHTML = '<option value="" disabled selected>Seleccione una cuenta...</option>';

            if (!Array.isArray(data) || data.length === 0) {
                selectCuentas.innerHTML = '<option value="" disabled selected>Este cliente no tiene deudas activas.</option>';
            } else {
                const preCuenta = document.getElementById('preselect_cod_cuentas')?.value || '';
                data.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.cod_cuentas;
                    opt.dataset.total = d.deuda_total;
                    opt.dataset.saldo = d.saldo_pendiente;

                    const saldoFormat = parseFloat(d.saldo_pendiente).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                    opt.textContent = `Placa: ${d.placa} (Debe: $${saldoFormat})`;
                    selectCuentas.appendChild(opt);
                });

                if (preCuenta && Array.from(selectCuentas.options).some(o => o.value === preCuenta)) {
                    selectCuentas.value = preCuenta;
                    if (typeof window.actualizarInfoDeuda === 'function') {
                        window.actualizarInfoDeuda();
                    }
                }
            }
        })
        .catch(error => {
            console.error("Error al cargar deudas:", error);
            if (selectCuentas) {
                selectCuentas.innerHTML = '<option value="" disabled selected>Error al cargar.</option>';
            }
        });
};

// ==========================================
// INICIALIZACIÓN Y VALIDACIONES DEL FORMULARIO
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
    if (window.FLASH_MESSAGES && window.FLASH_MESSAGES.length > 0) {
        window.FLASH_MESSAGES.forEach(([category, message]) => {
            const isSuccess = category === 'success';
            Swal.fire({
                title: isSuccess ? '¡Éxito!' : '¡Atención!',
                text: message,
                icon: ['success', 'error', 'warning', 'info'].includes(category) ? category : 'info',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#0d6efd'
            });
        });
    }

    const formAbono = document.getElementById("form-abono");
    const selectCuenta = document.getElementById("cod_cuentas");
    const txtMontoPago = document.getElementById("monto_pago");
    const txtReferencia = document.getElementById("referencia");
    const txtDescripcion = document.getElementById("descripcion");
    const hdnSaldoActual = document.getElementById("saldo_actual_val");
    const divBanco = document.getElementById("div_banco");
    const wrapperMonedaDigital = document.getElementById("wrapper_moneda_digital");

    function esPagoEnBolivares() {
        const metodo = String(document.getElementById("cod_metodo")?.value || "");
        if (["1", "4", "6"].includes(metodo)) return false;

        const monedaSelect = document.getElementById("cod_moneda");
        if (!monedaSelect || monedaSelect.disabled || !monedaSelect.value) return false;
        const opcion = monedaSelect.options[monedaSelect.selectedIndex];
        const texto = (opcion?.textContent || "").toLowerCase();
        return texto.includes("bolivar") || texto.includes("bolívar") || texto.includes("ves") || texto.includes("bs");
    }

    if (txtMontoPago) {
        txtMontoPago.addEventListener("keydown", function (e) {
            if (["e", "E", "+", "-"].includes(e.key)) e.preventDefault();
        });

        txtMontoPago.addEventListener("input", function () {
            if (parseFloat(this.value) < 0) this.value = "";
            if (this.value.includes(".")) {
                const partes = this.value.split(".");
                if (partes[1].length > 2) {
                    this.value = `${partes[0]}.${partes[1].slice(0, 2)}`;
                }
            }
        });
    }

    if (txtReferencia) {
        txtReferencia.addEventListener("input", function () {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 64);
        });
    }

    if (txtDescripcion) {
        txtDescripcion.addEventListener("input", function () {
            // Permite letras, números, #, espacios, comas, puntos, guiones y paréntesis
            this.value = this.value.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s.,()#\-]/g, "").slice(0, 200);
        });
    }

    if (formAbono) {
        formAbono.addEventListener("submit", function (event) {
            let formValido = true;

            if (selectCuenta) {
                if (selectCuenta.value === "" || selectCuenta.selectedIndex === 0) {
                    mostrarError(selectCuenta, "Debe seleccionar un vehículo con deuda activa para procesar.");
                    formValido = false;
                } else {
                    quitarError(selectCuenta);
                }
            }

            if (txtMontoPago && hdnSaldoActual) {
                const montoAbonar = parseFloat(txtMontoPago.value) || 0;
                const saldoPendiente = parseFloat(hdnSaldoActual.value) || 0;
                const tasa = parseFloat(document.getElementById("tasa_actual")?.value) || 0;
                let montoUSD = montoAbonar;

                if (esPagoEnBolivares()) {
                    if (tasa <= 0) {
                        mostrarError(txtMontoPago, "No existe una tasa válida para convertir Bs. a USD.");
                        formValido = false;
                    } else {
                        montoUSD = montoAbonar / tasa;
                    }
                }

                if (montoAbonar <= 0) {
                    mostrarError(txtMontoPago, "Ingrese un monto válido y mayor a 0.00.");
                    formValido = false;
                } else if (montoUSD > saldoPendiente + 0.01) {
                    mostrarError(
                        txtMontoPago,
                        `El abono equivale a $${montoUSD.toFixed(2)} USD y no puede superar el saldo pendiente de $${saldoPendiente.toFixed(2)} USD.`
                    );
                    formValido = false;
                } else {
                    quitarError(txtMontoPago);
                }
            }

            const requiereReferencia =
                (divBanco && window.getComputedStyle(divBanco).display !== "none") ||
                (wrapperMonedaDigital && window.getComputedStyle(wrapperMonedaDigital).display !== "none");

            if (txtReferencia && requiereReferencia) {
                const refVal = txtReferencia.value.trim();
                if (refVal.length < 4) {
                    mostrarError(txtReferencia, "El número de referencia o TXID es obligatorio para este método de pago (Mín. 4 caracteres).");
                    formValido = false;
                } else if (refVal.length > 64) {
                    mostrarError(txtReferencia, "El número de referencia no puede exceder los 64 caracteres.");
                    formValido = false;
                } else {
                    quitarError(txtReferencia);
                }
            } else if (txtReferencia) {
                quitarError(txtReferencia);
            }

            if (txtDescripcion) {
                if (txtDescripcion.value.trim().length > 200) {
                    mostrarError(txtDescripcion, "La descripción es demasiado larga (Máx. 200 caracteres).");
                    formValido = false;
                } else {
                    quitarError(txtDescripcion);
                }
            }

            if (!formValido) {
                event.preventDefault();
                event.stopPropagation();
                document.querySelector(".is-invalid")?.focus();
            }
        });
    }

    function mostrarError(elemento, mensaje) {
        elemento.classList.remove("is-valid");
        elemento.classList.add("is-invalid");
        const contenedor = elemento.closest(".input-group") || elemento.parentNode;
        let feedback = contenedor.querySelector(".invalid-feedback");
        if (!feedback) {
            feedback = document.createElement("div");
            feedback.classList.add("invalid-feedback", "d-block", "mt-1", "text-start");
            contenedor.appendChild(feedback);
        }
        feedback.innerText = mensaje;
    }

    function quitarError(elemento) {
        elemento.classList.remove("is-invalid");
        elemento.classList.add("is-valid");
        const contenedor = elemento.closest(".input-group") || elemento.parentNode;
        contenedor.querySelector(".invalid-feedback")?.remove();
    }
});