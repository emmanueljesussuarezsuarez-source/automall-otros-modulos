document.addEventListener('DOMContentLoaded', () => {
    inicializarEventos();
    toggleModoCliente('existente');

    const formClienteRapido = document.getElementById('form-cliente-rapido');
    if (formClienteRapido) {
        formClienteRapido.addEventListener('submit', registrarClienteRapido);
    }

    const hiddenCliente = document.getElementById('id_cliente_hidden');
    if (hiddenCliente?.value) {
        const inputBuscarC = document.getElementById('buscar_cliente');
        if (inputBuscarC) inputBuscarC.value = hiddenCliente.value;
        buscarCliente();
    }

    const hiddenVehiculo = document.getElementById('id_vehiculo_hidden');
    if (hiddenVehiculo?.value) {
        const inputBuscarV = document.getElementById('buscar_placa');
        if (inputBuscarV) inputBuscarV.value = hiddenVehiculo.value;
        buscarVehiculoPorPlaca();
    }

    const comboMetodo = document.getElementById('cod_metodo');
    const tipoOperacion = document.getElementById('tipo_operacion');
    if (comboMetodo?.value) {
        evaluarMetodoPago();
        filtrarMonedasPorMetodo();
    }
    if (tipoOperacion?.value) alternarModalidadPago();

    cargarTasaBCV();
});

function inicializarEventos() {
    document.getElementById('btn_buscar_cliente')?.addEventListener('click', buscarCliente);
    document.getElementById('btn_buscar_placa')?.addEventListener('click', buscarVehiculoPorPlaca);
    document.getElementById('btn_ir_paso_2')?.addEventListener('click', () => cambiarPaso(2));
    document.getElementById('btn_volver_paso_1')?.addEventListener('click', () => cambiarPaso(1));
    document.getElementById('btn_ir_paso_3')?.addEventListener('click', () => cambiarPaso(3));
    document.getElementById('btn_volver_paso_2')?.addEventListener('click', () => cambiarPaso(2));

    document.getElementById('monto_recibido')?.addEventListener('input', () => {
        actualizarRequeridoMetodoCredito();
        calcularBalances();
    });

    document.getElementById('cod_metodo')?.addEventListener('change', () => {
        evaluarMetodoPago();
        filtrarMonedasPorMetodo();
    });

    document.getElementById('cod_moneda')?.addEventListener('change', () => {
        actualizarSimboloMoneda();
        calcularBalances();
    });

    document.getElementById('tipo_operacion')?.addEventListener('change', alternarModalidadPago);
    document.getElementById('frecuencia_pago')?.addEventListener('change', () => {
        establecerFechaInicioPorDefecto(true);
        calcularBalances();
    });
    document.getElementById('cantidad_cuotas')?.addEventListener('input', calcularBalances);
    document.getElementById('tasa_interes')?.addEventListener('input', calcularBalances);
    document.getElementById('fecha_inicio_cuotas')?.addEventListener('change', calcularBalances);
    document.getElementById('form-venta')?.addEventListener('submit', manejarEnvioVenta);
}

function cargarTasaBCV() {
    fetch('/tasa/api/obtener_tasa')
        .then(res => {
            if (!res.ok) throw new Error('Error en red al buscar tasa');
            return res.json();
        })
        .then(data => {
            if (data.status === 'success' || data.status === 'warning') {
                const tasa = parseFloat(data.tasa) || 0;
                const inputTasaBcv = document.getElementById('tasa_bcv');
                const infoTasa = document.getElementById('info_tasa_bcv');
                if (inputTasaBcv && tasa > 0) {
                    inputTasaBcv.value = tasa;
                    if (infoTasa) infoTasa.textContent = `Tasa BCV del día: Bs. ${tasa}`;
                    calcularBalances();
                }
            }
        })
        .catch(err => console.error('No se pudo cargar la tasa BCV automática:', err));
}

/* ==========================================================================
   PASO 1: CLIENTES
   ========================================================================== */

function seleccionarClienteDeLista(selectElement) {
    if (selectElement.value) {
        document.getElementById('buscar_cliente').value = selectElement.value;
        buscarCliente();
    }
}

function normalizarTexto(texto) {
    return String(texto || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function limpiarFichaCliente() {
    ['lbl_cliente_doc', 'lbl_cliente_nombre', 'lbl_cliente_apellido', 'lbl_cliente_telefono', 'lbl_cliente_correo', 'lbl_cliente_direccion']
        .forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
}

function filtrarClientesEnTiempoReal() {
    const input = document.getElementById('buscar_cliente');
    const select = document.getElementById('select_cliente_lista');
    const hidden = document.getElementById('id_cliente_hidden');
    const resultados = document.getElementById('resultados_busqueda_clientes');
    if (!input || !select || !hidden || !resultados) return;

    const termino = normalizarTexto(input.value);
    hidden.value = '';
    input.classList.remove('is-valid', 'is-invalid');
    limpiarFichaCliente();
    resultados.innerHTML = '';
    resultados.style.display = 'none';

    if (!termino) {
        select.selectedIndex = 0;
        return;
    }

    const opciones = Array.from(select.options).filter(op => op.value.trim() !== '');
    const coincidencias = opciones.filter(op =>
        normalizarTexto(op.textContent).includes(termino) || normalizarTexto(op.value).includes(termino)
    );

    if (coincidencias.length > 0) {
        coincidencias.slice(0, 10).forEach(op => {
            const boton = document.createElement('button');
            boton.type = 'button';
            boton.className = 'list-group-item list-group-item-action text-start';
            boton.textContent = op.textContent.trim();
            boton.addEventListener('click', () => {
                input.value = op.value;
                select.value = op.value;
                resultados.innerHTML = '';
                resultados.style.display = 'none';
                buscarCliente();
            });
            resultados.appendChild(boton);
        });
    } else {
        const msg = document.createElement('div');
        msg.className = 'list-group-item text-muted small';
        msg.textContent = 'No hay coincidencias. Intenta otra búsqueda o registra un cliente nuevo.';
        resultados.appendChild(msg);
    }
    resultados.style.display = 'block';

    const exacta = opciones.find(op => normalizarTexto(op.value) === termino);
    if (exacta) {
        select.value = exacta.value;
        resultados.innerHTML = '';
        resultados.style.display = 'none';
        buscarCliente();
    }
}

function toggleModoCliente(modo) {
    document.getElementById('seccion_cliente_existente')?.classList.remove('d-none');
    const btnExistente = document.getElementById('btn_cliente_existente');
    if (btnExistente) {
        btnExistente.classList.toggle('btn-primary', modo === 'existente');
        btnExistente.classList.toggle('btn-outline-primary', modo !== 'existente');
    }
    if (modo === 'existente') document.getElementById('buscar_cliente')?.focus();
}

function abrirModalClienteRapido() {
    const formulario = document.getElementById('form-cliente-rapido');
    const alerta = document.getElementById('alerta-cliente-rapido');
    if (formulario) formulario.reset();
    if (alerta) {
        alerta.className = 'alert d-none';
        alerta.textContent = '';
    }
    const modalEl = document.getElementById('modalClienteRapido');
    if (!modalEl || !window.bootstrap?.Modal) {
        Swal.fire('Error', 'No se pudo abrir el formulario. Comprueba que Bootstrap JS esté cargado.', 'error');
        return;
    }
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function buscarCliente() {
    const inputBuscar = document.getElementById('buscar_cliente');
    const termino = inputBuscar?.value.trim();
    if (!termino) return;

    const lblDoc = document.getElementById('lbl_cliente_doc');
    const lblNombre = document.getElementById('lbl_cliente_nombre');
    const lblApellido = document.getElementById('lbl_cliente_apellido');
    const lblTelefono = document.getElementById('lbl_cliente_telefono');
    const lblCorreo = document.getElementById('lbl_cliente_correo');
    const lblDireccion = document.getElementById('lbl_cliente_direccion');
    const hiddenId = document.getElementById('id_cliente_hidden');

    lblNombre.innerHTML = '<span class="text-muted small">Buscando...</span>';
    lblApellido.innerHTML = '<span class="text-muted small">Buscando...</span>';

    fetch(`/ventas/api/cliente/${encodeURIComponent(termino)}`)
        .then(res => {
            if (!res.ok) throw new Error('No encontrado');
            return res.json();
        })
        .then(data => {
            if (!data.exito) throw new Error('Cliente no encontrado');
            if (lblDoc) lblDoc.textContent = data.cedula || '-';
            lblNombre.textContent = data.nombre || '-';
            lblApellido.textContent = data.apellido || '-';
            lblTelefono.textContent = data.telefono || 'No registrado';
            lblCorreo.textContent = data.correo || 'No registrado';
            lblDireccion.textContent = data.direccion || 'No registrada';
            hiddenId.value = data.cedula;

            const selectCliente = document.getElementById('select_cliente_lista');
            if (selectCliente) selectCliente.value = data.cedula;
            inputBuscar.classList.remove('is-invalid');
            inputBuscar.classList.add('is-valid');
        })
        .catch(() => {
            limpiarFichaCliente();
            hiddenId.value = '';
            inputBuscar.classList.remove('is-valid');
            inputBuscar.classList.add('is-invalid');
        });
}

async function registrarClienteRapido(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const boton = document.getElementById('btn_guardar_cliente_rapido');
    const alerta = document.getElementById('alerta-cliente-rapido');
    if (!formulario.reportValidity()) return;

    const datos = Object.fromEntries(new FormData(formulario).entries());
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Registrando...';
    alerta.className = 'alert d-none';
    alerta.textContent = '';

    try {
        const respuesta = await fetch('/ventas/api/cliente/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        const resultado = await respuesta.json();
        if (!respuesta.ok || !resultado.exito) {
            throw new Error(resultado.mensaje || 'No se pudo registrar el cliente.');
        }

        const c = resultado.cliente;
        document.getElementById('id_cliente_hidden').value = c.cedula;
        const ficha = {
            lbl_cliente_doc: c.cedula,
            lbl_cliente_nombre: c.nombre,
            lbl_cliente_apellido: c.apellido,
            lbl_cliente_telefono: c.telefono,
            lbl_cliente_correo: c.correo,
            lbl_cliente_direccion: c.direccion
        };
        Object.entries(ficha).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val || '-';
        });

        const buscar = document.getElementById('buscar_cliente');
        if (buscar) {
            buscar.value = c.cedula;
            buscar.classList.remove('is-invalid');
            buscar.classList.add('is-valid');
        }

        const lista = document.getElementById('select_cliente_lista');
        if (lista) {
            let opcion = Array.from(lista.options).find(item => item.value === c.cedula);
            if (!opcion) {
                opcion = document.createElement('option');
                opcion.value = c.cedula;
                opcion.textContent = `${c.nombre} ${c.apellido} (V-${c.cedula})`;
                lista.appendChild(opcion);
            }
            lista.value = c.cedula;
        }

        formulario.reset();
        bootstrap.Modal.getOrCreateInstance(document.getElementById('modalClienteRapido')).hide();
        toggleModoCliente('existente');

        await Swal.fire({
            icon: 'success',
            title: 'Cliente registrado',
            text: 'El cliente fue registrado y seleccionado para la venta.',
            confirmButtonText: 'Continuar'
        });
    } catch (error) {
        console.error('Error registrando cliente:', error);
        alerta.className = 'alert alert-danger';
        alerta.textContent = error.message || 'Ocurrió un error al registrar el cliente.';
    } finally {
        boton.disabled = false;
        boton.innerHTML = '<i class="bi bi-check-circle me-1"></i> Registrar y seleccionar';
    }
}

/* ==========================================================================
   PASO 2: VEHÍCULOS Y NAVEGACIÓN
   ========================================================================== */

function seleccionarDeLista(selectElement) {
    if (selectElement.value) {
        document.getElementById('buscar_placa').value = selectElement.value;
        buscarVehiculoPorPlaca();
    }
}

function buscarVehiculoPorPlaca() {
    const inputPlaca = document.getElementById('buscar_placa');
    const placa = inputPlaca?.value.trim().toUpperCase();
    if (!placa) return;

    const lblMarcaModelo = document.getElementById('v_marca_modelo');
    lblMarcaModelo.innerHTML = '<span class="text-muted small">Buscando...</span>';

    fetch(`/ventas/api/vehiculo/${encodeURIComponent(placa)}`)
        .then(res => {
            if (!res.ok) throw new Error('Vehículo no encontrado');
            return res.json();
        })
        .then(data => {
            if (!data.exito) throw new Error('Vehículo no encontrado');
            const v = data.vehiculo;

            lblMarcaModelo.textContent = `${v.marca} ${v.modelo}`;
            document.getElementById('v_tipo').textContent = v.tipo || 'No especificado';
            document.getElementById('v_anio_color').textContent = `${v.anio} / ${v.color}`;
            document.getElementById('v_estado').textContent = v.estado;

            const fotoContainer = document.getElementById('v_foto_container');
            const fotoImg = document.getElementById('v_foto_img');
            if (v.foto) {
                fotoImg.src = `/static/${v.foto}`;
                fotoContainer.style.display = 'flex';
            } else {
                fotoContainer.style.display = 'none';
                fotoImg.src = '';
            }

            document.getElementById('v_precio_raw').value = v.precio;
            document.getElementById('v_precio').textContent = '$ ' + Number(v.precio).toLocaleString('en-US', {
                minimumFractionDigits: 2, maximumFractionDigits: 2
            });
            document.getElementById('id_vehiculo_hidden').value = v.placa;

            const selectVehiculo = document.getElementById('select_vehiculo_lista');
            if (selectVehiculo) selectVehiculo.value = v.placa;

            inputPlaca.classList.remove('is-invalid');
            inputPlaca.classList.add('is-valid');
            alternarModalidadPago();
            calcularBalances();
        })
        .catch(error => {
            console.error(error);
            resetFichaVehiculo();
            inputPlaca.classList.remove('is-valid');
            inputPlaca.classList.add('is-invalid');
        });
}

function resetFichaVehiculo() {
    document.getElementById('v_marca_modelo').innerText = 'Seleccione un Vehículo';
    document.getElementById('id_vehiculo_hidden').value = '';
    document.getElementById('v_precio_raw').value = 0;
    document.getElementById('v_precio').innerText = '$ 0.00';
    document.getElementById('total_visual_usd').innerText = '$ 0.00';
    document.getElementById('total_visual_ves').innerText = 'Bs. 0.00';
    document.getElementById('resumen_total').innerText = '$ 0.00';
    const fotoContainer = document.getElementById('v_foto_container');
    if (fotoContainer) fotoContainer.style.display = 'none';
}

function cambiarPaso(nuevoPaso) {
    if (nuevoPaso === 2 && !document.getElementById('id_cliente_hidden')?.value) {
        Swal.fire('Atención', 'Debe identificar un cliente primero', 'warning');
        return;
    }
    if (nuevoPaso === 3 && !document.getElementById('id_vehiculo_hidden')?.value) {
        Swal.fire('Atención', 'Debe seleccionar un vehículo válido', 'warning');
        return;
    }
    document.querySelectorAll('.step-pane').forEach(pane => pane.classList.add('d-none'));
    document.getElementById(`step-${nuevoPaso}`)?.classList.remove('d-none');
    window.scrollTo(0, 0);
}

/* ==========================================================================
   PASO 3: MÉTODOS DE PAGO, BALANCES Y PLAN DE CUOTAS
   ========================================================================== */

function obtenerFlagsMetodo() {
    const metodo = document.getElementById('cod_metodo');
    if (!metodo || !metodo.value || !metodo.options[metodo.selectedIndex]) {
        return { codigo: '', esDigital: false, esBanco: false, esEfectivo: false, requiereRef: false, texto: '' };
    }
    const opcion = metodo.options[metodo.selectedIndex];
    const codigo = String(metodo.value || '');
    const texto = normalizarTexto(opcion.textContent);
    const reqAttr = opcion.getAttribute('data-requiere-ref');
    const requiereRef = reqAttr === '1' || reqAttr === 'true' || reqAttr === 'True';

    const esEfectivo = texto.includes('efectivo') || codigo === '2';
    const esDigital = texto.includes('binance') || texto.includes('zelle') || texto.includes('zinli') || ['1', '4', '6'].includes(codigo);
    const esBanco = !esEfectivo && !esDigital && (texto.includes('pago movil') || texto.includes('transferencia') || ['3', '5'].includes(codigo));

    return { codigo, esDigital, esBanco, esEfectivo, requiereRef, texto };
}

function filtrarMonedasPorMetodo() {
    const moneda = document.getElementById('cod_moneda');
    const digital = document.getElementById('cod_mon_digital');
    const banco = document.getElementById('cod_banco');
    const wrapperMoneda = document.getElementById('wrapper_moneda');
    const wrapperBanco = document.getElementById('wrapper_banco');
    const wrapperDigital = document.getElementById('wrapper_moneda_digital');

    const { esDigital, esBanco } = obtenerFlagsMetodo();
    const requierePago = requierePasarelaPago();

    if (wrapperDigital) wrapperDigital.style.display = (requierePago && esDigital) ? 'block' : 'none';
    if (wrapperBanco) {
        wrapperBanco.classList.toggle('d-none', !(requierePago && esBanco));
        wrapperBanco.style.display = (requierePago && esBanco) ? 'block' : 'none';
    }
    if (wrapperMoneda) wrapperMoneda.style.display = (!requierePago || esDigital) ? 'none' : 'block';

    if (digital) {
        digital.disabled = !(requierePago && esDigital);
        digital.required = requierePago && esDigital;
        if (!requierePago || !esDigital) digital.value = '';
    }
    if (banco) {
        banco.disabled = !(requierePago && esBanco);
        banco.required = requierePago && esBanco;
        if (!requierePago || !esBanco) banco.value = '';
    }
    if (moneda) {
        moneda.disabled = !requierePago || esDigital;
        moneda.required = requierePago && !esDigital;
        if (esDigital) moneda.value = '';
    }

    actualizarSimboloMoneda();
}

function evaluarMetodoPago() {
    const wrRef = document.getElementById('wrapper_referencia');
    const inputRef = document.getElementById('referencia');
    const lblRef = document.getElementById('label_referencia');
    const { requiereRef, texto } = obtenerFlagsMetodo();
    const requierePago = requierePasarelaPago();

    if (!requierePago || !requiereRef) {
        wrRef?.classList.add('d-none');
        if (inputRef) {
            inputRef.removeAttribute('required');
            inputRef.value = '';
        }
    } else {
        wrRef?.classList.remove('d-none');
        if (inputRef) inputRef.setAttribute('required', 'required');
        if (lblRef) {
            lblRef.innerText = (texto.includes('pago movil') || texto.includes('transferencia'))
                ? 'Nro. de Referencia o Transacción Bancaria'
                : 'Código de Referencia / ID de Pago';
        }
    }
}

function requierePasarelaPago() {
    const tipo = document.getElementById('tipo_operacion')?.value || 'contado';
    if (tipo !== 'credito') return true;
    const monto = parseFloat(document.getElementById('monto_recibido')?.value) || 0;
    return monto > 0;
}

function actualizarRequeridoMetodoCredito() {
    const comboMetodo = document.getElementById('cod_metodo');
    const requierePago = requierePasarelaPago();
    if (comboMetodo) {
        comboMetodo.required = requierePago;
        comboMetodo.disabled = !requierePago;
        if (!requierePago) comboMetodo.value = '';
    }
    evaluarMetodoPago();
    filtrarMonedasPorMetodo();
}

function actualizarSimboloMoneda() {
    const combo = document.getElementById('cod_moneda');
    const simbolo = document.getElementById('simbolo_moneda');
    if (!combo || !simbolo || combo.disabled || !combo.options[combo.selectedIndex]) {
        if (simbolo) simbolo.textContent = '$';
        return;
    }
    simbolo.textContent = combo.options[combo.selectedIndex].getAttribute('data-simbolo') || '$';
}

function alternarModalidadPago() {
    const tipoOperacion = document.getElementById('tipo_operacion')?.value;
    const wrapperCredito = document.getElementById('wrapper_credito');
    const hintInicial = document.getElementById('hint_inicial_credito');
    const labelMonto = document.getElementById('label_monto_dinamico');
    const fechaVenc = document.getElementById('fecha_vencimiento');
    const montoInput = document.getElementById('monto_recibido');
    if (!wrapperCredito || !tipoOperacion) return;

    const esCredito = tipoOperacion === 'credito';
    wrapperCredito.classList.toggle('d-none', !esCredito);
    hintInicial?.classList.toggle('d-none', !esCredito);
    if (fechaVenc) fechaVenc.required = esCredito;

    if (esCredito) {
        if (labelMonto) labelMonto.textContent = 'Inicial a Recibir (Opcional)';
        if (montoInput && montoInput.value === '') montoInput.value = '0.00';
        establecerFechaInicioPorDefecto(false);
    } else {
        if (labelMonto) labelMonto.textContent = 'Monto Líquido a Recibir';
    }

    actualizarRequeridoMetodoCredito();
    calcularBalances();
}

function redondear2(num) {
    return Math.round((Number(num) + Number.EPSILON) * 100) / 100;
}

function formatearFechaISO(dateObj) {
    const y = dateObj.getFullYear();
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const d = String(dateObj.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function parsearFechaLocal(fechaStr) {
    if (!fechaStr || !/^\d{4}-\d{2}-\d{2}$/.test(fechaStr)) return new Date();
    const [y, m, d] = fechaStr.split('-').map(Number);
    return new Date(y, m - 1, d);
}

function sumarMesSeguro(fechaBase, meses) {
    const resultado = new Date(fechaBase.getFullYear(), fechaBase.getMonth() + meses, fechaBase.getDate());
    if (resultado.getDate() !== fechaBase.getDate()) {
        resultado.setDate(0);
    }
    return resultado;
}

function establecerFechaInicioPorDefecto(forzar) {
    const inputInicio = document.getElementById('fecha_inicio_cuotas');
    if (!inputInicio) return;
    if (!forzar && inputInicio.value) return;

    const frecuencia = normalizarTexto(document.getElementById('frecuencia_pago')?.value || 'mensual');
    const hoy = new Date();
    let sugerida;
    if (frecuencia === 'semanal') {
        sugerida = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() + 7);
    } else if (frecuencia === 'quincenal') {
        sugerida = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() + 15);
    } else {
        sugerida = sumarMesSeguro(hoy, 1);
    }
    inputInicio.value = formatearFechaISO(sugerida);
}

function calcularBalances() {
    const precioUSD = parseFloat(document.getElementById('v_precio_raw')?.value) || 0;
    const tasa = parseFloat(document.getElementById('tasa_bcv')?.value) || 0;
    const totalUSD = document.getElementById('total_visual_usd');
    const totalVES = document.getElementById('total_visual_ves');
    const resumen = document.getElementById('resumen_total');
    const montoInput = document.getElementById('monto_recibido');
    const saldoInput = document.getElementById('saldo_pendiente');
    const deudaTotalInput = document.getElementById('deuda_total_credito');
    const deudaUSD = document.getElementById('deuda_usd');
    const deudaVES = document.getElementById('deuda_ves');
    const tipoOperacion = document.getElementById('tipo_operacion')?.value || 'contado';
    const comboMoneda = document.getElementById('cod_moneda');

    const precioVES = tasa > 0 ? precioUSD * tasa : 0;
    if (totalUSD) {
        totalUSD.textContent = `$ ${precioUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (totalVES) {
        totalVES.textContent = tasa > 0
            ? `Bs. ${precioVES.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : 'Bs. --';
    }

    let simbolo = '$';
    let esBolivar = false;
    if (comboMoneda && !comboMoneda.disabled && comboMoneda.options[comboMoneda.selectedIndex]) {
        const opcion = comboMoneda.options[comboMoneda.selectedIndex];
        simbolo = opcion.getAttribute('data-simbolo') || '$';
        const texto = normalizarTexto(opcion.textContent);
        esBolivar = texto.includes('bolivar') || texto.includes('ves') || texto.includes('bs');
    }

    const totalMostrar = esBolivar ? precioVES : precioUSD;
    if (resumen) {
        resumen.textContent = (esBolivar && tasa <= 0)
            ? 'Bs. --'
            : `${simbolo} ${totalMostrar.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    if (tipoOperacion === 'contado') {
        if (montoInput) montoInput.value = totalMostrar > 0 ? totalMostrar.toFixed(2) : '';
        if (saldoInput) saldoInput.value = '0.00';
        if (deudaTotalInput) deudaTotalInput.value = precioUSD.toFixed(2);
        if (deudaUSD) deudaUSD.textContent = 'USD: $0.00';
        if (deudaVES) deudaVES.textContent = 'VES: Bs. 0.00';
        return;
    }

    const montoRecibido = parseFloat(montoInput?.value) || 0;
    const montoRecibidoUSD = esBolivar ? (tasa > 0 ? montoRecibido / tasa : 0) : montoRecibido;
    const saldoBase = Math.max(0, precioUSD - montoRecibidoUSD);
    const tasaInteres = Math.max(0, parseFloat(document.getElementById('tasa_interes')?.value) || 0);
    const montoInteres = redondear2(saldoBase * (tasaInteres / 100));
    const deudaTotalConInteres = redondear2(precioUSD + montoInteres);
    const deudaRealUSD = Math.max(0, redondear2(saldoBase + montoInteres));
    const deudaRealVES = tasa > 0 ? deudaRealUSD * tasa : 0;

    if (saldoInput) saldoInput.value = deudaRealUSD.toFixed(2);
    if (deudaTotalInput) deudaTotalInput.value = deudaTotalConInteres.toFixed(2);
    if (deudaUSD) {
        deudaUSD.textContent = `USD: $ ${deudaRealUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (deudaVES) {
        deudaVES.textContent = tasa > 0
            ? `VES: Bs. ${deudaRealVES.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : 'VES: Bs. --';
    }

    generarPreviewCuotas(deudaRealUSD, tasa);
}

function generarPreviewCuotas(saldoFinanciarUSD, tasaBCV) {
    const tbody = document.getElementById('tbody_preview_cuotas');
    const badgeCuota = document.getElementById('badge_cuota_aprox');
    const inputCuotasJson = document.getElementById('cuotas_json');
    const inputFechaVenc = document.getElementById('fecha_vencimiento');
    const inputInicio = document.getElementById('fecha_inicio_cuotas');
    if (!tbody || !inputCuotasJson) return;

    const frecuencia = normalizarTexto(document.getElementById('frecuencia_pago')?.value || 'mensual');
    const cantidad = Math.min(120, Math.max(1, parseInt(document.getElementById('cantidad_cuotas')?.value, 10) || 1));

    if (!inputInicio?.value) establecerFechaInicioPorDefecto(true);
    const fechaBase = parsearFechaLocal(inputInicio?.value);

    if (saldoFinanciarUSD <= 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Sin saldo pendiente por financiar en cuotas.</td></tr>';
        if (badgeCuota) badgeCuota.textContent = 'Cuota aprox: $0.00';
        inputCuotasJson.value = '[]';
        if (inputFechaVenc) inputFechaVenc.value = formatearFechaISO(fechaBase);
        return;
    }

    const cuotaBase = redondear2(saldoFinanciarUSD / cantidad);
    const cuotas = [];
    tbody.innerHTML = '';

    for (let i = 1; i <= cantidad; i++) {
        const monto = (i === cantidad)
            ? redondear2(saldoFinanciarUSD - cuotaBase * (cantidad - 1))
            : cuotaBase;

        let fechaCuota;
        if (frecuencia === 'semanal') {
            fechaCuota = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), fechaBase.getDate() + (i - 1) * 7);
        } else if (frecuencia === 'quincenal') {
            fechaCuota = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), fechaBase.getDate() + (i - 1) * 15);
        } else {
            fechaCuota = sumarMesSeguro(fechaBase, i - 1);
        }

        const fechaISO = formatearFechaISO(fechaCuota);
        const montoVES = tasaBCV > 0 ? monto * tasaBCV : 0;
        cuotas.push({ numero_cuota: i, fecha_vencimiento: fechaISO, monto_cuota: Number(monto.toFixed(2)) });

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="ps-2 fw-bold">Cuota ${i}</td>
            <td><input type="date" class="form-control form-control-sm input-fecha-cuota" data-idx="${i - 1}" value="${fechaISO}"></td>
            <td class="text-end fw-bold">$ ${monto.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-end pe-2 text-muted">${tasaBCV > 0 ? 'Bs. ' + montoVES.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--'}</td>
        `;
        tbody.appendChild(tr);
    }

    tbody.querySelectorAll('.input-fecha-cuota').forEach(inp => {
        inp.addEventListener('change', () => {
            const idx = parseInt(inp.dataset.idx, 10);
            if (!isNaN(idx) && cuotas[idx]) {
                cuotas[idx].fecha_vencimiento = inp.value;
                inputCuotasJson.value = JSON.stringify(cuotas);
                if (idx === cuotas.length - 1 && inputFechaVenc) {
                    inputFechaVenc.value = inp.value;
                }
            }
        });
    });

    if (badgeCuota) {
        badgeCuota.textContent = `Cuota aprox: $ ${cuotaBase.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    inputCuotasJson.value = JSON.stringify(cuotas);
    if (inputFechaVenc && cuotas.length > 0) {
        inputFechaVenc.value = cuotas[cuotas.length - 1].fecha_vencimiento;
    }
}

/* ==========================================================================
   ENVÍO DEL FORMULARIO DE VENTA
   ========================================================================== */

function manejarEnvioVenta(e) {
    e.preventDefault();

    if (typeof window.validarFormularioVenta === 'function' && !window.validarFormularioVenta()) {
        return;
    }
    const form = e.currentTarget;
    const cedula = document.getElementById('id_cliente_hidden')?.value;
    const placa = document.getElementById('id_vehiculo_hidden')?.value;

    if (!cedula || !placa) {
        Swal.fire('Error', 'Debe seleccionar un cliente y un vehículo válidos.', 'error');
        return;
    }

    actualizarRequeridoMetodoCredito();

    const tipoOperacion = document.getElementById('tipo_operacion')?.value || 'contado';
    const requierePago = requierePasarelaPago();
    const comboMetodo = document.getElementById('cod_metodo');
    const { esDigital, esBanco, esEfectivo, esPagoMovil, texto } = (() => {
        const flags = obtenerFlagsMetodo();
        return { ...flags, esPagoMovil: flags.texto.includes('pago movil') };
    })();

    if (requierePago) {
        if (!comboMetodo || !comboMetodo.value) {
            Swal.fire('Error', 'Debe seleccionar un método de pago.', 'error');
            return;
        }
        if (esBanco) {
            const selectBanco = document.getElementById('cod_banco');
            const comboMoneda = document.getElementById('cod_moneda');
            if (!selectBanco?.value) {
                Swal.fire('Atención', `Debe seleccionar el banco para ${esPagoMovil ? 'Pago Móvil' : 'Transferencia'}.`, 'warning');
                return;
            }
            if (!comboMoneda || comboMoneda.disabled || !comboMoneda.value) {
                Swal.fire('Atención', 'Debe seleccionar la moneda de recepción.', 'warning');
                return;
            }
        }
        if (esDigital && !document.getElementById('cod_mon_digital')?.value) {
            Swal.fire('Atención', 'Debe seleccionar la moneda digital.', 'warning');
            return;
        }
    }

    const data = {};
    new FormData(form).forEach((value, key) => { data[key] = value; });

    // Normalizar inicial a USD si es crédito y se pagó en bolívares
    const monedaSelect = document.getElementById('cod_moneda');
    if (tipoOperacion === 'credito') {
        let esPagoEnBs = false;
        if (monedaSelect && !monedaSelect.disabled && monedaSelect.options[monedaSelect.selectedIndex]) {
            const txtMoneda = normalizarTexto(monedaSelect.options[monedaSelect.selectedIndex].textContent);
            esPagoEnBs = txtMoneda.includes('bolivar') || txtMoneda.includes('ves') || txtMoneda.includes('bs');
        }
        const montoNum = parseFloat(data.monto_recibido) || 0;
        if (esPagoEnBs && montoNum > 0) {
            const tasaCambio = parseFloat(document.getElementById('tasa_bcv')?.value) || 0;
            if (tasaCambio > 0) {
                data.monto_recibido_ves = montoNum.toFixed(2);
                data.monto_recibido = (montoNum / tasaCambio).toFixed(2);
            }
        } else {
            data.monto_recibido = montoNum.toFixed(2);
        }

        try {
            data.cuotas = JSON.parse(data.cuotas_json || '[]');
        } catch {
            data.cuotas = [];
        }
        data.deuda_total = document.getElementById('deuda_total_credito')?.value
            || document.getElementById('v_precio_raw')?.value
            || '0.00';
    } else {
        data.deuda_total = document.getElementById('v_precio_raw')?.value || '0.00';
    }

    // Limpieza según método de pago
    if (!requierePago) {
        delete data.cod_metodo;
        delete data.cod_banco;
        delete data.cod_moneda;
        delete data.cod_mon_digital;
        data.referencia = '';
    } else if (esEfectivo) {
        delete data.cod_banco;
        delete data.cod_mon_digital;
        data.referencia = '';
    } else if (esBanco) {
        delete data.cod_mon_digital;
    } else if (esDigital) {
        delete data.cod_banco;
        delete data.cod_moneda;
    }

    console.log('📤 Datos enviados:', data);

    fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(async response => {
            const res = await response.json();
            if (!response.ok) throw new Error(res.mensaje || 'Error procesando la venta');
            return res;
        })
        .then(res => {
            if (res.exito) {
                Swal.fire('Éxito', res.mensaje, 'success').then(() => {
                    if (res.pdf_url) window.open(res.pdf_url, '_blank');
                    window.location.href = '/ventas/lista_ventas';
                });
            } else {
                Swal.fire('Error', res.mensaje || 'Error procesando la solicitud', 'error');
            }
        })
        .catch(error => {
            console.error('Error en la petición:', error);
            Swal.fire('Error Crítico', error.message || 'Hubo un problema procesando la venta.', 'error');
        });
}