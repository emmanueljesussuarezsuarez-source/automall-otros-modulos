document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("form-abono");
    if (!formulario) {
        console.error("No se encontró el formulario #form-abono");
        return;
    }

    const cuentaSelect = document.getElementById("cod_cuentas");
    const cuotaSelect = document.getElementById("cod_cuota");
    const bloqueCuotas = document.getElementById("bloque_cuotas_cuenta");
    const tbodyCuotas = document.getElementById("tbody_cuotas_cuenta");
    const resumenPlanCuotas = document.getElementById("resumen_plan_cuotas");

    const montoInput = document.getElementById("monto_pago");
    const metodoSelect = document.getElementById("cod_metodo");
    const monedaSelect = document.getElementById("cod_moneda");
    const bancoSelect = document.getElementById("cod_banco");
    const digitalSelect = document.getElementById("cod_mon_digital");
    const referenciaInput = document.getElementById("referencia");
    const descripcionInput = document.getElementById("descripcion");

    const saldoInput = document.getElementById("saldo_actual_val");
    const tasaInput = document.getElementById("tasa_actual");

    const wrapperMoneda = document.getElementById("wrapper_moneda");
    const wrapperBanco = document.getElementById("div_banco");
    const wrapperDigital = document.getElementById("wrapper_moneda_digital");

    const lblTotal = document.getElementById("lbl_total");
    const lblSaldo = document.getElementById("lbl_saldo");
    const lblNuevoSaldo = document.getElementById("lbl_nuevo_saldo");
    const lblNuevoSaldoVES = document.getElementById("lbl_nuevo_saldo_ves");
    const lblTasa = document.getElementById("lbl_tasa");
    const lblTasaConversion = document.getElementById("lbl_tasa_conversion");
    const lblMontoConversion = document.getElementById("lbl_monto_conversion");
    const lblEquivalenteUSD = document.getElementById("lbl_equivalente_usd");
    const ayudaMonto = document.getElementById("ayuda-monto");

    const botonProcesar = document.getElementById("btn-procesar");
    const botonActualizarTasa = document.getElementById("btn-actualizar-tasa");
    const preselectCuenta = document.getElementById("preselect_cod_cuentas")?.value || "";
    const preselectCuota = document.getElementById("preselect_cod_cuota")?.value || "";

    const METODO_EFECTIVO = "2";
    const METODOS_BANCARIOS = ["3", "5"];
    const METODOS_DIGITALES = ["1", "4", "6"];

    let cuotasCargadas = [];

    // =========================================================
    // TASA BCV
    // =========================================================
    async function cargarTasa() {
        try {
            const respuesta = await fetch("/tasa/api/obtener_tasa", {
                method: "GET",
                headers: { Accept: "application/json" },
                cache: "no-cache"
            });
            const data = await respuesta.json();
            const tasa = parseFloat(data.tasa);

            if (!isNaN(tasa) && tasa > 0) {
                if (tasaInput) tasaInput.value = tasa;
                if (lblTasa) {
                    lblTasa.textContent = `Bs. ${tasa.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 6 })} / USD`;
                }
                if (lblTasaConversion) {
                    lblTasaConversion.textContent = tasa.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 6 });
                }
                calcularNuevoSaldo();
            }
        } catch (error) {
            console.error("Error consultando tasa:", error);
        }
    }

    function esBolivar() {
        if (!monedaSelect || monedaSelect.disabled || !monedaSelect.value) return false;
        const opcion = monedaSelect.options[monedaSelect.selectedIndex];
        if (!opcion) return false;
        const texto = (opcion.textContent || "").toLowerCase();
        return texto.includes("bolivar") || texto.includes("bolívar") || texto.includes("ves") || texto.includes("bs");
    }

    function obtenerMontoUSD() {
        const monto = parseFloat(montoInput?.value || 0) || 0;
        if (monto <= 0) return 0;

        const metodo = String(metodoSelect?.value || "");
        if (METODOS_DIGITALES.includes(metodo) || !esBolivar()) {
            return monto;
        }

        const tasa = parseFloat(tasaInput?.value || 0) || 0;
        return tasa > 0 ? monto / tasa : 0;
    }

    function convertirUSDaMonedaSeleccionada(montoUSD) {
        const metodo = String(metodoSelect?.value || "");
        if (!METODOS_DIGITALES.includes(metodo) && esBolivar()) {
            const tasa = parseFloat(tasaInput?.value || 0) || 0;
            if (tasa > 0) return (montoUSD * tasa).toFixed(2);
        }
        return Number(montoUSD).toFixed(2);
    }

    // =========================================================
    // CUOTAS DE LA CUENTA SELECCIONADA
    // =========================================================
    function limpiarCuotasUI() {
        cuotasCargadas = [];
        if (bloqueCuotas) bloqueCuotas.classList.add("d-none");
        if (cuotaSelect) {
            cuotaSelect.innerHTML = '<option value="">Abono automático (aplicar a cuota más antigua)</option>';
        }
        if (tbodyCuotas) {
            tbodyCuotas.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-2">Seleccione una cuenta para ver sus cuotas.</td></tr>';
        }
        if (resumenPlanCuotas) resumenPlanCuotas.textContent = "";
    }

    function formatearFechaCorta(fechaStr) {
        if (!fechaStr) return "N/A";
        const partes = String(fechaStr).slice(0, 10).split("-");
        if (partes.length !== 3) return fechaStr;
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }

    function badgeEstadoCuota(estado) {
        const est = String(estado || "").toLowerCase();
        if (est === "pagada") return '<span class="badge bg-success">Pagada</span>';
        if (est === "parcial") return '<span class="badge bg-info text-dark">Parcial</span>';
        if (est === "vencida") return '<span class="badge bg-danger">Vencida</span>';
        if (est === "anulada") return '<span class="badge bg-secondary">Anulada</span>';
        return '<span class="badge bg-warning text-dark">Pendiente</span>';
    }

    window.seleccionarCuotaParaPagar = function (codCuota) {
        if (!cuotaSelect) return;
        cuotaSelect.value = codCuota ? String(codCuota) : "";

        const cuota = cuotasCargadas.find(c => String(c.cod_cuota) === String(codCuota));
        if (cuota && montoInput) {
            const saldoCuotaUSD = Math.max(0, Number(cuota.saldo_cuota || 0));
            if (saldoCuotaUSD > 0) {
                montoInput.value = convertirUSDaMonedaSeleccionada(saldoCuotaUSD);
                calcularNuevoSaldo();
            }
        }
    };

    async function cargarCuotasCuenta(codCuentas, codCuotaPreselect = "") {
        limpiarCuotasUI();
        if (!codCuentas) return;

        try {
            const resp = await fetch(`/pagos/api/cuotas/${encodeURIComponent(codCuentas)}`, {
                headers: { Accept: "application/json" }
            });
            if (!resp.ok) return;
            const data = await resp.json();
            if (!data.exito || !Array.isArray(data.cuotas) || data.cuotas.length === 0) {
                return;
            }

            cuotasCargadas = data.cuotas;
            if (bloqueCuotas) bloqueCuotas.classList.remove("d-none");

            const pagadas = cuotasCargadas.filter(c => String(c.estado).toLowerCase() === "pagada").length;
            const frec = data.frecuencia_pago || "Mensual";
            if (resumenPlanCuotas) {
                resumenPlanCuotas.textContent = `${pagadas}/${cuotasCargadas.length} pagadas • ${frec}`;
            }

            if (cuotaSelect) {
                cuotaSelect.innerHTML = '<option value="">Abono automático (aplicar a cuota más antigua)</option>';
                cuotasCargadas.forEach(c => {
                    const est = String(c.estado_actual || c.estado).toLowerCase();
                    if (["pendiente", "parcial", "vencida"].includes(est)) {
                        const opt = document.createElement("option");
                        opt.value = c.cod_cuota;
                        opt.dataset.saldoUsd = Number(c.saldo_cuota || 0).toFixed(2);
                        const etiquetaVenc = est === "vencida" ? " [VENCIDA]" : "";
                        opt.textContent = `Cuota #${c.numero_cuota} (${formatearFechaCorta(c.fecha_vencimiento)}) - Saldo: $${Number(c.saldo_cuota).toFixed(2)}${etiquetaVenc}`;
                        cuotaSelect.appendChild(opt);
                    }
                });
            }

            if (tbodyCuotas) {
                tbodyCuotas.innerHTML = "";
                cuotasCargadas.forEach(c => {
                    const est = String(c.estado_actual || c.estado).toLowerCase();
                    const pendiente = ["pendiente", "parcial", "vencida"].includes(est);
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td class="ps-2 fw-bold">#${c.numero_cuota}</td>
                        <td>${formatearFechaCorta(c.fecha_vencimiento)}</td>
                        <td class="text-end fw-bold">$${Number(c.saldo_cuota).toFixed(2)}</td>
                        <td class="text-center">${badgeEstadoCuota(c.estado_actual || c.estado)}</td>
                        <td class="text-end pe-2">
                            ${pendiente
                                ? `<button type="button" class="btn btn-outline-primary btn-xs py-0 px-2 btn-elegir-cuota" style="font-size:0.72rem;" data-cuota="${c.cod_cuota}">Elegir</button>`
                                : '<span class="text-muted">—</span>'}
                        </td>
                    `;
                    tbodyCuotas.appendChild(tr);
                });

                tbodyCuotas.querySelectorAll(".btn-elegir-cuota").forEach(btn => {
                    btn.addEventListener("click", () => window.seleccionarCuotaParaPagar(btn.dataset.cuota));
                });
            }

            if (codCuotaPreselect) {
                window.seleccionarCuotaParaPagar(codCuotaPreselect);
            }
        } catch (error) {
            console.error("Error cargando cuotas de la cuenta:", error);
        }
    }

    // =========================================================
    // ACTUALIZAR INFO DE DEUDA
    // =========================================================
    window.actualizarInfoDeuda = function () {
        if (!cuentaSelect) return;
        const opcion = cuentaSelect.options[cuentaSelect.selectedIndex];

        if (!opcion || !opcion.value) {
            if (saldoInput) saldoInput.value = "0";
            if (lblTotal) lblTotal.textContent = "$ 0.00";
            if (lblSaldo) lblSaldo.textContent = "$ 0.00";
            limpiarCuotasUI();
            calcularNuevoSaldo();
            return;
        }

        const total = parseFloat(opcion.dataset.total) || 0;
        const saldo = parseFloat(opcion.dataset.saldo) || 0;

        if (saldoInput) saldoInput.value = saldo;
        if (lblTotal) {
            lblTotal.textContent = `$ ${total.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        if (lblSaldo) {
            lblSaldo.textContent = `$ ${saldo.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        calcularNuevoSaldo();
        cargarCuotasCuenta(opcion.value, preselectCuenta === opcion.value ? preselectCuota : "");
    };

    // =========================================================
    // EVALUAR MÉTODO DE PAGO
    // =========================================================
    function actualizarAyudaMonto(esDigital) {
        if (!ayudaMonto) return;
        if (esDigital) {
            ayudaMonto.textContent = "Ingrese el monto equivalente en USD.";
        } else if (esBolivar()) {
            ayudaMonto.textContent = "El monto ingresado en VES será convertido a USD usando la tasa del día.";
        } else {
            ayudaMonto.textContent = "Ingrese el monto correspondiente a la moneda seleccionada.";
        }
    }

    window.evaluarMetodo = function () {
        const metodo = String(metodoSelect?.value || "");
        const esDigital = METODOS_DIGITALES.includes(metodo);
        const esBanco = METODOS_BANCARIOS.includes(metodo);
        const esEfectivo = metodo === METODO_EFECTIVO;

        if (wrapperMoneda) wrapperMoneda.style.display = esDigital ? "none" : "block";
        if (monedaSelect) {
            monedaSelect.disabled = esDigital;
            monedaSelect.required = !esDigital;
            if (esDigital) monedaSelect.value = "";
        }

        if (wrapperBanco) wrapperBanco.style.display = esBanco ? "block" : "none";
        if (bancoSelect) {
            bancoSelect.disabled = !esBanco;
            bancoSelect.required = esBanco;
            if (!esBanco) bancoSelect.value = "";
        }

        if (wrapperDigital) wrapperDigital.style.display = esDigital ? "block" : "none";
        if (digitalSelect) {
            digitalSelect.disabled = !esDigital;
            digitalSelect.required = esDigital;
            if (!esDigital) digitalSelect.value = "";
        }

        if (referenciaInput) {
            referenciaInput.disabled = esEfectivo;
            referenciaInput.required = !esEfectivo;
            if (esEfectivo) referenciaInput.value = "";
        }

        actualizarAyudaMonto(esDigital);
        calcularNuevoSaldo();
    };

    // =========================================================
    // CALCULAR NUEVO SALDO
    // =========================================================
    window.calcularNuevoSaldo = function () {
        const saldo = parseFloat(saldoInput?.value || 0) || 0;
        const monto = parseFloat(montoInput?.value || 0) || 0;
        const montoUSD = obtenerMontoUSD();
        const metodo = String(metodoSelect?.value || "");
        const esDigital = METODOS_DIGITALES.includes(metodo);
        const enBs = !esDigital && esBolivar();

        actualizarAyudaMonto(esDigital);

        if (lblMontoConversion) {
            const prefijo = enBs ? "Bs. " : "$ ";
            lblMontoConversion.textContent = monto > 0
                ? `${prefijo}${monto.toLocaleString(enBs ? "es-VE" : "en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : "$ 0.00";
        }

        if (lblEquivalenteUSD) {
            lblEquivalenteUSD.textContent = montoUSD > 0
                ? `$ ${montoUSD.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : "$ 0.00";
        }

        const tasa = parseFloat(tasaInput?.value || 0) || 0;
        if (lblTasaConversion) {
            lblTasaConversion.textContent = (enBs && tasa > 0)
                ? tasa.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 6 })
                : "—";
        }

        const nuevoSaldo = Math.max(0, saldo - montoUSD);
        if (lblNuevoSaldo) {
            lblNuevoSaldo.textContent = `$ ${nuevoSaldo.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        if (lblNuevoSaldoVES) {
            if (tasa > 0 && enBs && nuevoSaldo > 0) {
                lblNuevoSaldoVES.textContent = `Equivalente: Bs. ${(nuevoSaldo * tasa).toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            } else {
                lblNuevoSaldoVES.textContent = "";
            }
        }
    };

    // =========================================================
    // LISTENERS
    // =========================================================
    cuentaSelect?.addEventListener("change", actualizarInfoDeuda);
    cuotaSelect?.addEventListener("change", () => window.seleccionarCuotaParaPagar(cuotaSelect.value));
    montoInput?.addEventListener("input", calcularNuevoSaldo);
    monedaSelect?.addEventListener("change", () => {
        if (cuotaSelect?.value) {
            window.seleccionarCuotaParaPagar(cuotaSelect.value);
        } else {
            calcularNuevoSaldo();
        }
    });
    metodoSelect?.addEventListener("change", evaluarMetodo);

    botonActualizarTasa?.addEventListener("click", async () => {
        botonActualizarTasa.disabled = true;
        try {
            await cargarTasa();
        } finally {
            botonActualizarTasa.disabled = false;
        }
    });

    // =========================================================
    // REGISTRAR PAGO
    // =========================================================
    formulario.addEventListener("submit", async (event) => {
        if (event.defaultPrevented) return;
        event.preventDefault();
        if (botonProcesar) botonProcesar.disabled = true;

        try {
            const codCuentas = cuentaSelect ? cuentaSelect.value : "";
            const codCuota = cuotaSelect && cuotaSelect.value ? cuotaSelect.value : null;
            const monto = parseFloat(montoInput?.value || 0) || 0;
            const metodo = String(metodoSelect?.value || "");
            const codMoneda = (monedaSelect && !monedaSelect.disabled) ? monedaSelect.value : null;
            const codBanco = (bancoSelect && !bancoSelect.disabled) ? bancoSelect.value : null;
            const codMonDigital = (digitalSelect && !digitalSelect.disabled) ? digitalSelect.value : null;
            const referencia = referenciaInput ? referenciaInput.value.trim() : "";
            const descripcion = descripcionInput ? descripcionInput.value.trim() : "";
            const montoUSD = obtenerMontoUSD();
            const saldo = parseFloat(saldoInput?.value || 0) || 0;

            if (!codCuentas) throw new Error("Debe seleccionar una cuenta por cobrar.");
            if (monto <= 0) throw new Error("El monto debe ser mayor a cero.");
            if (montoUSD <= 0) throw new Error("No se pudo calcular correctamente el monto en USD.");
            if (montoUSD > saldo + 0.01) {
                throw new Error(`El monto supera el saldo pendiente de $${saldo.toFixed(2)}.`);
            }

            const datos = {
                cod_cuentas: codCuentas,
                cod_cuota: codCuota,
                monto_pago: monto,
                cod_metodo: metodo,
                cod_moneda: codMoneda,
                cod_banco: codBanco,
                cod_mon_digital: codMonDigital,
                referencia: referencia,
                descripcion: descripcion
            };

            const respuesta = await fetch("/pagos/procesar", {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify(datos)
            });

            const texto = await respuesta.text();
            let resultado;
            try {
                resultado = JSON.parse(texto);
            } catch {
                throw new Error(`El servidor respondió con HTTP ${respuesta.status}, pero no devolvió JSON.`);
            }

            if (!respuesta.ok || resultado.success === false) {
                throw new Error(resultado.error || resultado.message || "No se pudo registrar el pago.");
            }

            if (resultado.success === true || resultado.status === true) {
                if (typeof Swal !== "undefined") {
                    await Swal.fire({
                        icon: "success",
                        title: "¡Pago registrado!",
                        text: resultado.message || "El abono fue registrado correctamente.",
                        confirmButtonText: "Aceptar",
                        allowOutsideClick: false
                    });
                } else {
                    alert(resultado.message || "¡Pago registrado correctamente!");
                }
                window.location.reload();
                return;
            }

            throw new Error(resultado.error || "El servidor no confirmó el registro del pago.");
        } catch (error) {
            console.error("ERROR AL REGISTRAR:", error);
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    icon: "error",
                    title: "No se pudo registrar",
                    text: error.message || "Ocurrió un error al registrar el pago.",
                    confirmButtonText: "Aceptar"
                });
            } else {
                alert(error.message || "Ocurrió un error al registrar el pago.");
            }
        } finally {
            if (botonProcesar) botonProcesar.disabled = false;
        }
    });

   // =========================================================
    // INICIALIZACIÓN Y PRESELECCIÓN POR URL (CLIENTE Y ADMIN)
    // =========================================================
    evaluarMetodo();
    const cedulaSelect = document.getElementById("cedula_cliente");

    if (preselectCuenta && cuentaSelect) {
        const existeOpcion = Array.from(cuentaSelect.options).some(op => op.value === preselectCuenta);
        if (existeOpcion) {
            cuentaSelect.value = preselectCuenta;
            actualizarInfoDeuda();
        } else if (cedulaSelect) {
            // Modo admin: consultamos a qué cliente pertenece la cuenta preseleccionada
            fetch(`/pagos/api/cuotas/${encodeURIComponent(preselectCuenta)}`, {
                headers: { Accept: "application/json" }
            })
                .then(r => (r.ok ? r.json() : null))
                .then(data => {
                    if (data && data.cedula_cliente) {
                        cedulaSelect.value = data.cedula_cliente;
                        if (typeof window.cargarDeudasCliente === "function") {
                            window.cargarDeudasCliente();
                        }
                    }
                })
                .catch(() => {});
        } else {
            actualizarInfoDeuda();
        }
    } else {
        actualizarInfoDeuda();
    }

    cargarTasa();
});