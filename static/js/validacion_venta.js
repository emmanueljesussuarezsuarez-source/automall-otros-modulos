// ==========================================================
// VALIDACIONES DE FORMULARIO DE VENTAS Y PLAN DE CUOTAS
// ==========================================================
document.addEventListener('DOMContentLoaded', () => {
    const txtBuscarCliente = document.getElementById('buscar_cliente');
    const txtPlaca = document.getElementById('buscar_placa');
    const txtReferencia = document.getElementById('referencia');
    const txtMonto = document.getElementById('monto_recibido');
    const txtCantidadCuotas = document.getElementById('cantidad_cuotas');
    const txtTasaInteres = document.getElementById('tasa_interes');

    // VALIDACIÓN CLIENTE: Letras, números y espacios
    if (txtBuscarCliente) {
        txtBuscarCliente.addEventListener('input', function () {
            this.value = this.value.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]/g, '').slice(0, 40);
        });
    }

    // VALIDACIÓN PLACA
    if (txtPlaca) {
        txtPlaca.addEventListener('input', function () {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 10);
        });
    }

    // VALIDACIÓN REFERENCIA (hasta 25 caracteres para Zelle/Binance/Bancos)
    if (txtReferencia) {
        txtReferencia.addEventListener('input', function () {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 25);
        });
    }

    // VALIDACIÓN MONTO RECIBIDO
    if (txtMonto) {
        txtMonto.addEventListener('keydown', (e) => {
            if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault();
        });
        txtMonto.addEventListener('input', function () {
            if (this.value.includes('.')) {
                const partes = this.value.split('.');
                if (partes[1].length > 2) {
                    this.value = `${partes[0]}.${partes[1].slice(0, 2)}`;
                }
            }
        });
    }

    // VALIDACIÓN CANTIDAD DE CUOTAS (solo enteros positivos 1-120)
    if (txtCantidadCuotas) {
        txtCantidadCuotas.addEventListener('keydown', (e) => {
            if (['e', 'E', '+', '-', '.', ','].includes(e.key)) e.preventDefault();
        });
        txtCantidadCuotas.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (parseInt(this.value, 10) > 120) this.value = '120';
        });
    }

    // VALIDACIÓN TASA DE INTERÉS (0 - 100%)
    if (txtTasaInteres) {
        txtTasaInteres.addEventListener('keydown', (e) => {
            if (['e', 'E', '+', '-'].includes(e.key)) e.preventDefault();
        });
        txtTasaInteres.addEventListener('input', function () {
            if (this.value.includes('.')) {
                const partes = this.value.split('.');
                if (partes[1].length > 2) {
                    this.value = `${partes[0]}.${partes[1].slice(0, 2)}`;
                }
            }
            if (parseFloat(this.value) > 100) this.value = '100';
        });
    }
});

window.validarFormularioVenta = function () {
    const txtBuscarCliente = document.getElementById('buscar_cliente');
    const hiddenCliente = document.getElementById('id_cliente_hidden');
    const txtPlaca = document.getElementById('buscar_placa');
    const hiddenVehiculo = document.getElementById('id_vehiculo_hidden');
    const txtReferencia = document.getElementById('referencia');
    const txtMonto = document.getElementById('monto_recibido');
    const selectTipoVenta = document.getElementById('tipo_operacion');
    const selectFrecuencia = document.getElementById('frecuencia_pago');
    const txtCantidadCuotas = document.getElementById('cantidad_cuotas');
    const txtTasaInteres = document.getElementById('tasa_interes');
    const txtFechaInicio = document.getElementById('fecha_inicio_cuotas');
    const txtFechaVencimiento = document.getElementById('fecha_vencimiento');
    const precioUSD = parseFloat(document.getElementById('v_precio_raw')?.value) || 0;
    const tasaBCV = parseFloat(document.getElementById('tasa_bcv')?.value) || 0;

    let formValido = true;

    const mostrarError = (elemento, mensaje) => {
        if (!elemento) return;
        elemento.classList.remove('is-valid');
        elemento.classList.add('is-invalid');
        const contenedor = elemento.closest('.input-group') || elemento.parentNode;
        let feedback = contenedor.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.classList.add('invalid-feedback', 'd-block', 'mt-1', 'text-start');
            contenedor.appendChild(feedback);
        }
        feedback.innerText = mensaje;
    };

    const quitarError = (elemento) => {
        if (!elemento) return;
        elemento.classList.remove('is-invalid');
        elemento.classList.add('is-valid');
        const contenedor = elemento.closest('.input-group') || elemento.parentNode;
        const feedback = contenedor.querySelector('.invalid-feedback');
        if (feedback) feedback.remove();
    };

    const hoyISO = () => {
        const d = new Date();
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    };

    // 1. Cliente
    if (!hiddenCliente || !hiddenCliente.value.trim()) {
        if (txtBuscarCliente) mostrarError(txtBuscarCliente, 'Debe seleccionar un cliente válido.');
        formValido = false;
    } else if (txtBuscarCliente) {
        quitarError(txtBuscarCliente);
    }

    // 2. Vehículo
    if (!hiddenVehiculo || !hiddenVehiculo.value.trim()) {
        if (txtPlaca) mostrarError(txtPlaca, 'Debe seleccionar un vehículo válido.');
        formValido = false;
    } else if (txtPlaca) {
        quitarError(txtPlaca);
    }

    const tipoVenta = selectTipoVenta?.value || 'contado';
    const montoVal = parseFloat(txtMonto?.value);

    // 3. Monto recibido
    if (txtMonto) {
        if (tipoVenta === 'contado') {
            if (isNaN(montoVal) || montoVal <= 0) {
                mostrarError(txtMonto, 'Debe ingresar un monto numérico válido y mayor a 0.00.');
                formValido = false;
            } else {
                quitarError(txtMonto);
            }
        } else {
            if (isNaN(montoVal) || montoVal < 0) {
                mostrarError(txtMonto, 'La inicial debe ser 0.00 o un monto positivo.');
                formValido = false;
            } else {
                // Verificar que la inicial no cubra el 100% en modalidad crédito
                const comboMoneda = document.getElementById('cod_moneda');
                let esBs = false;
                if (comboMoneda && !comboMoneda.disabled && comboMoneda.options[comboMoneda.selectedIndex]) {
                    const txtM = comboMoneda.options[comboMoneda.selectedIndex].textContent.toLowerCase();
                    esBs = txtM.includes('bolivar') || txtM.includes('bolívar') || txtM.includes('ves') || txtM.includes('bs');
                }
                const montoUSD = esBs ? (tasaBCV > 0 ? montoVal / tasaBCV : 0) : montoVal;
                if (precioUSD > 0 && montoUSD >= precioUSD) {
                    mostrarError(txtMonto, 'Si la inicial cubre el 100% del vehículo, seleccione venta de Contado.');
                    formValido = false;
                } else {
                    quitarError(txtMonto);
                }
            }
        }
    }

    // 4. Referencia (solo si el bloque está visible)
    const wrapperRef = document.getElementById('wrapper_referencia');
    const refVisible = wrapperRef && !wrapperRef.classList.contains('d-none') && window.getComputedStyle(wrapperRef).display !== 'none';
    if (txtReferencia && refVisible) {
        const refVal = txtReferencia.value.trim();
        if (refVal.length < 4) {
            mostrarError(txtReferencia, 'La referencia es obligatoria para este método (mínimo 4 caracteres).');
            formValido = false;
        } else {
            quitarError(txtReferencia);
        }
    } else if (txtReferencia) {
        quitarError(txtReferencia);
    }

    // 5. Plan de Crédito por Cuotas
    if (tipoVenta === 'credito') {
        if (selectFrecuencia && !['Semanal', 'Quincenal', 'Mensual'].includes(selectFrecuencia.value)) {
            mostrarError(selectFrecuencia, 'Seleccione una frecuencia válida.');
            formValido = false;
        } else if (selectFrecuencia) {
            quitarError(selectFrecuencia);
        }

        if (txtCantidadCuotas) {
            const cant = parseInt(txtCantidadCuotas.value, 10);
            if (isNaN(cant) || cant < 1 || cant > 120) {
                mostrarError(txtCantidadCuotas, 'Ingrese entre 1 y 120 cuotas.');
                formValido = false;
            } else {
                quitarError(txtCantidadCuotas);
            }
        }

        if (txtTasaInteres) {
            const interes = parseFloat(txtTasaInteres.value);
            if (isNaN(interes) || interes < 0 || interes > 100) {
                mostrarError(txtTasaInteres, 'El interés debe estar entre 0% y 100%.');
                formValido = false;
            } else {
                quitarError(txtTasaInteres);
            }
        }

        const hoy = hoyISO();
        if (txtFechaInicio) {
            if (!txtFechaInicio.value || txtFechaInicio.value < hoy) {
                mostrarError(txtFechaInicio, 'La fecha de la primera cuota debe ser hoy o posterior.');
                formValido = false;
            } else {
                quitarError(txtFechaInicio);
            }
        }

        if (txtFechaVencimiento) {
            if (!txtFechaVencimiento.value) {
                mostrarError(txtFechaVencimiento, 'La fecha de vencimiento final es obligatoria.');
                formValido = false;
            } else if (txtFechaVencimiento.value < hoy) {
                mostrarError(txtFechaVencimiento, 'La fecha de vencimiento no puede ser anterior a hoy.');
                formValido = false;
            } else if (txtFechaInicio?.value && txtFechaVencimiento.value < txtFechaInicio.value) {
                mostrarError(txtFechaVencimiento, 'La fecha final no puede ser menor a la primera cuota.');
                formValido = false;
            } else {
                quitarError(txtFechaVencimiento);
            }
        }
    }

    if (!formValido) {
        const primerError = document.querySelector('#form-venta .is-invalid');
        if (primerError) primerError.focus();
    }

    return formValido;
};