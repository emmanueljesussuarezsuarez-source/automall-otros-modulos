// ==========================================
// VARIABLES GLOBALES
// ==========================================
let paginaActual = 1;
const filasPorPagina = 8;

// ==========================================
// 1. LÓGICA DE PAGINACIÓN Y BÚSQUEDA
// ==========================================
window.filtrarYPaginar = function (pagina = 1) {
    paginaActual = pagina;
    const inputBuscar = document.getElementById('inputPlaca');
    if (!inputBuscar) return;

    const query = inputBuscar.value.toLowerCase().trim();
    const filas = Array.from(document.querySelectorAll('.fila-venta'));

    const filasFiltradas = filas.filter(tr => {
        const placa = tr.getAttribute('data-placa') || '';
        return placa.includes(query);
    });

    filas.forEach(tr => (tr.style.display = 'none'));

    const totalRegistros = filasFiltradas.length;
    const totalPaginas = Math.ceil(totalRegistros / filasPorPagina) || 1;
    if (paginaActual > totalPaginas) paginaActual = totalPaginas;

    const inicio = (paginaActual - 1) * filasPorPagina;
    const fin = inicio + filasPorPagina;
    filasFiltradas.slice(inicio, fin).forEach(tr => (tr.style.display = ''));

    renderizarPaginador(totalPaginas, totalRegistros, inicio, fin);
};

function renderizarPaginador(totalPaginas, totalRegistros, inicio, fin) {
    const ul = document.getElementById('ulPaginacion');
    const info = document.getElementById('infoPaginacion');
    if (!ul || !info) return;

    ul.innerHTML = '';
    if (totalRegistros === 0) {
        info.textContent = 'Mostrando 0 de 0 ventas';
        return;
    }

    const finReal = fin > totalRegistros ? totalRegistros : fin;
    info.textContent = `Mostrando ${inicio + 1} - ${finReal} de ${totalRegistros} ventas`;

    const liPrev = document.createElement('li');
    liPrev.className = `page-item ${paginaActual === 1 ? 'disabled' : ''}`;
    liPrev.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); window.filtrarYPaginar(${paginaActual - 1})">&laquo;</a>`;
    ul.appendChild(liPrev);

    for (let i = 1; i <= totalPaginas; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === paginaActual ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); window.filtrarYPaginar(${i})">${i}</a>`;
        ul.appendChild(li);
    }

    const liNext = document.createElement('li');
    liNext.className = `page-item ${paginaActual === totalPaginas ? 'disabled' : ''}`;
    liNext.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); window.filtrarYPaginar(${paginaActual + 1})">&raquo;</a>`;
    ul.appendChild(liNext);
}

// ==========================================
// 2. IMPRESIÓN DE RECIBO (CON CRONOGRAMA DE CUOTAS)
// ==========================================
function imprimirRecibo(codVenta) {
    const modal = document.querySelector(`#modalDetalle${codVenta}`);
    if (!modal) return;

    const getText = (sel) => {
        const el = modal.querySelector(sel);
        return el ? el.textContent.trim().replace(/\s+/g, ' ') : '';
    };

    const cedula = getText('div.fw-bold.fs-6') || 'N/A';
    const placa = getText('.badge.bg-dark') || 'N/A';

    const celdas = modal.querySelectorAll('.row.g-2.text-center .fw-bold');
    const anio = celdas[0]?.textContent.trim() || 'N/A';
    const color = celdas[1]?.textContent.trim() || 'N/A';
    const km = celdas[2]?.textContent.trim() || 'N/A';

    const filas = modal.querySelectorAll('.list-group-item');
    const datos = {};
    filas.forEach(fila => {
        const spans = fila.querySelectorAll('span');
        if (spans.length === 2) {
            const clave = spans[0].textContent.trim().replace(/\s+/g, ' ');
            const valor = spans[1].textContent.trim().replace(/\s+/g, ' ');
            datos[clave] = valor;
        }
    });

    const badgeEstado = modal.querySelector('.modal-header .badge.bg-white');
    const estadoRaw = badgeEstado ? badgeEstado.textContent.trim().toUpperCase() : 'ACTIVA';

    let colorEstado = '#0d6efd';
    let bgEstadoSuave = '#e7f0ff';
    if (estadoRaw.includes('ANULADA') || estadoRaw.includes('CANCELADA')) {
        colorEstado = '#dc3545'; bgEstadoSuave = '#fde8ea';
    } else if (estadoRaw.includes('COMPLETADA') || estadoRaw.includes('PAGADO')) {
        colorEstado = '#198754'; bgEstadoSuave = '#e6f4ed';
    } else if (estadoRaw.includes('PENDIENTE')) {
        colorEstado = '#fd7e14'; bgEstadoSuave = '#fff1e2';
    }

    const marcaModelo = modal.querySelector('.card-body .d-flex.align-items-center .fw-bold')?.textContent.trim() || 'N/A';
    const fechaVenc = datos['Fecha de Vencimiento Final'] || datos['Fecha de Vencimiento'] || '';
    const interes = datos['Tasa de Interés Aplicada'] || '';

    // Extraer tabla de cuotas si existe en el modal
    const tablaCuotasModal = modal.querySelector('table');
    let htmlCuotas = '';
    if (tablaCuotasModal) {
        const filasCuotas = Array.from(tablaCuotasModal.querySelectorAll('tbody tr'));
        if (filasCuotas.length > 0) {
            const rowsHtml = filasCuotas.map(tr => {
                const tds = tr.querySelectorAll('td');
                if (tds.length < 6) return '';
                return `<tr>
                    <td>${tds[0].textContent.trim()}</td>
                    <td>${tds[1].textContent.trim()}</td>
                    <td style="text-align:right;">${tds[2].textContent.trim()}</td>
                    <td style="text-align:right;">${tds[3].textContent.trim()}</td>
                    <td style="text-align:right;">${tds[4].textContent.trim()}</td>
                    <td style="text-align:center;">${tds[5].textContent.trim()}</td>
                </tr>`;
            }).join('');

            htmlCuotas = `
                <div class="seccion-titulo mt-3"><i class="bi bi-calendar2-week"></i> Cronograma de Cuotas</div>
                <div class="info-box p-0" style="overflow: hidden;">
                    <table class="tabla-financiera tabla-cuotas">
                        <thead>
                            <tr style="background:#f1f3f5; font-weight:700;">
                                <td>Cuota</td>
                                <td>Vencimiento</td>
                                <td style="text-align:right;">Monto</td>
                                <td style="text-align:right;">Pagado</td>
                                <td style="text-align:right;">Saldo</td>
                                <td style="text-align:center;">Estado</td>
                            </tr>
                        </thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                </div>
            `;
        }
    }

    const ventana = window.open('', '_blank', 'height=900,width=800');
    const logoUrl = window.LOGO_URL || '';
    const nombreEmp = window.NOMBRE_EMPRESA || '';

    ventana.document.write(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Recibo de Venta #${codVenta}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
            <style>
                @page { size: A4 portrait; margin: 10mm; }
                * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
                body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #212529; padding: 0; margin: 0; }
                .recibo { max-width: 780px; margin: 0 auto; padding: 12px; }
                .recibo-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid ${colorEstado}; padding-bottom: 8px; margin-bottom: 10px; }
                .logo-empresa { max-height: 55px; max-width: 140px; object-fit: contain; }
                .recibo-header h1 { font-size: 18px; margin: 0; font-weight: 800; color: ${colorEstado}; }
                .recibo-header .sub { font-size: 10px; color: #6c757d; margin: 0; }
                .estado-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 10px; letter-spacing: 0.5px; color: ${colorEstado}; background: ${bgEstadoSuave}; border: 1px solid ${colorEstado}; }
                .seccion-titulo { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #6c757d; font-weight: 700; margin: 10px 0 5px 0; padding-bottom: 3px; border-bottom: 1px dashed #dee2e6; }
                .grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
                .info-box { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 8px 10px; }
                .info-label { font-size: 9px; color: #6c757d; text-transform: uppercase; font-weight: 600; letter-spacing: 0.3px; }
                .info-valor { font-size: 12px; font-weight: 700; color: #212529; }
                .spec-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 6px; }
                .spec-item { background: #fff; border: 1px solid #e9ecef; border-radius: 5px; padding: 5px; text-align: center; }
                .spec-item .info-label { font-size: 8px; }
                .spec-item .info-valor { font-size: 11px; }
                .tabla-financiera { width: 100%; border-collapse: collapse; margin-top: 4px; }
                .tabla-financiera td { padding: 5px 10px; font-size: 11px; border-bottom: 1px solid #f1f3f5; }
                .tabla-financiera:not(.tabla-cuotas) td:last-child { text-align: right; font-weight: 700; }
                .tabla-cuotas td { font-size: 10px; padding: 4px 8px; }
                .tabla-financiera tr:last-child td { border-bottom: none; }
                .fila-total { background: ${bgEstadoSuave}; border-top: 2px solid ${colorEstado} !important; border-bottom: none !important; }
                .fila-total td { font-size: 14px !important; font-weight: 800 !important; color: ${colorEstado}; padding: 8px 10px !important; }
                .firmas { margin-top: 25px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; text-align: center; }
                .firma-linea { border-top: 1.5px solid #212529; margin-bottom: 4px; }
                .firma-texto { font-size: 10px; font-weight: 600; color: #495057; }
                .footer-print { margin-top: 15px; padding-top: 6px; border-top: 1px solid #dee2e6; font-size: 9px; text-align: center; color: #6c757d; }
                @media print { body { padding: 0; margin: 0; } .recibo { padding: 0; max-width: 100%; } }
            </style>
        </head>
        <body>
            <div class="recibo">
                <div class="recibo-header">
                    <div class="d-flex align-items-center gap-3">
                        ${logoUrl ? `<img src="${logoUrl}" alt="Logo" class="logo-empresa">` : ''}
                        <div>
                            <h1>${nombreEmp || 'COMPROBANTE DE VENTA'}</h1>
                            <p class="sub">Recibo N° <strong>#${codVenta}</strong> · Emitido el ${new Date().toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}</p>
                        </div>
                    </div>
                    <div class="text-end"><span class="estado-badge">${estadoRaw}</span></div>
                </div>
                <div class="grid-2col">
                    <div>
                        <div class="seccion-titulo"><i class="bi bi-person-badge"></i> Cliente</div>
                        <div class="info-box">
                            <div class="info-label">Cédula / Datos del Comprador</div>
                            <div class="info-valor">${cedula}</div>
                        </div>
                    </div>
                    <div>
                        <div class="seccion-titulo"><i class="bi bi-car-front-fill"></i> Vehículo</div>
                        <div class="info-box">
                            <div class="info-label">Marca / Modelo</div>
                            <div class="info-valor">${marcaModelo}</div>
                            <div class="info-label mt-2">Placa</div>
                            <div class="info-valor">${placa}</div>
                        </div>
                    </div>
                </div>
                <div class="seccion-titulo mt-3"><i class="bi bi-sliders"></i> Especificaciones</div>
                <div class="spec-grid">
                    <div class="spec-item"><div class="info-label">Año</div><div class="info-valor">${anio}</div></div>
                    <div class="spec-item"><div class="info-label">Color</div><div class="info-valor">${color}</div></div>
                    <div class="spec-item"><div class="info-label">Kilometraje</div><div class="info-valor">${km}</div></div>
                </div>
                <div class="seccion-titulo mt-3"><i class="bi bi-cash-stack"></i> Resumen Financiero</div>
                <div class="info-box p-0" style="overflow: hidden;">
                    <table class="tabla-financiera">
                        <tr><td>Modalidad de Pago</td><td>${datos['Modalidad de Pago'] || 'N/A'}</td></tr>
                        <tr><td>Fecha de Venta</td><td>${datos['Fecha de Venta'] || 'N/A'}</td></tr>
                        ${fechaVenc ? `<tr><td>Fecha de Vencimiento Final</td><td style="color:#dc3545;">${fechaVenc}</td></tr>` : ''}
                        ${interes ? `<tr><td>Tasa de Interés Aplicada</td><td>${interes}</td></tr>` : ''}
                        <tr><td>Monto Total</td><td>${datos['Monto Total'] || '$0.00'}</td></tr>
                        <tr><td>Total Abonado</td><td style="color:#198754;">${datos['Total Abonado'] || '$0.00'}</td></tr>
                        <tr class="fila-total"><td>SALDO PENDIENTE</td><td>${datos['Saldo Pendiente'] || '$0.00'}</td></tr>
                    </table>
                </div>
                ${htmlCuotas}
                <div class="firmas">
                    <div><div class="firma-linea"></div><div class="firma-texto">Firma del Vendedor</div></div>
                    <div><div class="firma-linea"></div><div class="firma-texto">Firma del Cliente</div></div>
                </div>
                <div class="footer-print">Este documento es un comprobante de venta generado automáticamente. Conserve este recibo para cualquier reclamo o consulta.</div>
            </div>
            <script>setTimeout(() => { window.print(); }, 600);<\/script>
        </body>
        </html>
    `);

    ventana.document.close();
    ventana.focus();
}

// ==========================================
// 3. INICIALIZACIÓN DE EVENTOS DEL DOM
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
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

    window.filtrarYPaginar(1);

    const hoy = new Date();
    const yyyy = hoy.getFullYear();
    const mm = String(hoy.getMonth() + 1).padStart(2, '0');
    const dd = String(hoy.getDate()).padStart(2, '0');
    const fechaMinima = `${yyyy}-${mm}-${dd}`;
    const fechaMaxima = `${yyyy + 10}-${mm}-${dd}`;

    document.querySelectorAll('.input-fecha-venc').forEach(input => {
        input.setAttribute('min', fechaMinima);
        input.setAttribute('max', fechaMaxima);
    });

    document.body.addEventListener('input', (e) => {
        if (e.target.classList.contains('input-deuda')) {
            let valor = e.target.value.replace(/[^0-9.]/g, '');
            const partes = valor.split('.');
            if (partes.length > 2) valor = partes[0] + '.' + partes.slice(1).join('').replace(/\./g, '');
            if (partes[0].length > 8) {
                partes[0] = partes[0].substring(0, 8);
                valor = partes.length > 1 ? partes[0] + '.' + partes[1] : partes[0];
            }
            if (partes.length > 1 && partes[1].length > 2) {
                valor = partes[0] + '.' + partes[1].substring(0, 2);
            }
            e.target.value = valor;
        }
    });

    document.body.addEventListener('focusout', (e) => {
        if (e.target.classList.contains('input-deuda') && e.target.value.trim() !== '') {
            const valorNumerico = parseFloat(e.target.value);
            if (!isNaN(valorNumerico)) e.target.value = valorNumerico.toFixed(2);
        }
    });

    document.querySelectorAll('.form-editar-venta').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const inputDeuda = form.querySelector('.input-deuda');
            if (inputDeuda) {
                const valor = parseFloat(inputDeuda.value);
                if (isNaN(valor) || valor <= 0) {
                    Swal.fire({ icon: 'error', title: 'Monto Inválido', text: 'El monto de la deuda debe ser mayor a 0.', confirmButtonColor: '#0d6efd' })
                        .then(() => inputDeuda.focus());
                    return;
                }
            }

            const inputCuotas = form.querySelector('input[name="cantidad_cuotas"]');
            if (inputCuotas) {
                const cant = parseInt(inputCuotas.value, 10);
                if (isNaN(cant) || cant < 1 || cant > 120) {
                    Swal.fire({ icon: 'error', title: 'Cuotas Inválidas', text: 'La cantidad de cuotas debe estar entre 1 y 120.', confirmButtonColor: '#0d6efd' })
                        .then(() => inputCuotas.focus());
                    return;
                }
            }

            const inputFecha = form.querySelector('.input-fecha-venc');
            if (inputFecha && inputFecha.value !== '') {
                if (inputFecha.value < fechaMinima) {
                    Swal.fire({ icon: 'error', title: 'Fecha Inválida', text: 'La fecha de vencimiento no puede ser anterior a la fecha actual.', confirmButtonColor: '#0d6efd' })
                        .then(() => inputFecha.focus());
                    return;
                }
                if (inputFecha.value > fechaMaxima) {
                    Swal.fire({ icon: 'error', title: 'Fecha Inválida', text: 'La fecha de vencimiento no puede ser superior a 10 años.', confirmButtonColor: '#0d6efd' })
                        .then(() => inputFecha.focus());
                    return;
                }
            }

            Swal.fire({
                title: '¿Guardar cambios?',
                text: 'Se actualizará la información de la venta seleccionada.',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#0d6efd',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, guardar',
                cancelButtonText: 'Cancelar'
            }).then(result => {
                if (result.isConfirmed) form.submit();
            });
        });
    });

    document.querySelectorAll('.form-eliminar-venta').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            Swal.fire({
                title: '¿Confirmar Anulación?',
                text: 'Esta acción marcará la venta como anulada y reincorporará el vehículo al inventario.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, anular',
                cancelButtonText: 'Cancelar'
            }).then(result => {
                if (result.isConfirmed) form.submit();
            });
        });
    });

    document.body.addEventListener('click', (e) => {
        const btnImprimir = e.target.closest('.btn-imprimir');
        if (btnImprimir) {
            const codVenta = btnImprimir.getAttribute('data-cod');
            if (codVenta) imprimirRecibo(codVenta);
        }
    });

    document.getElementById('inputPlaca')?.addEventListener('keyup', () => window.filtrarYPaginar(1));
});