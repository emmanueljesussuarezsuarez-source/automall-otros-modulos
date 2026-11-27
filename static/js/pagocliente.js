// =========================================================
// DATOS GLOBALES PARA TARJETAS, CUOTAS Y PAGINACIÓN
// =========================================================
const configuracion = window.pagoClienteConfig || {};
const resumenVehiculos = configuracion.resumenVehiculos || {};

const filasPorPagina = 10;
let paginaActual = 1;
let filasActivas = [];
let todasLasFilas = [];
let filasCuotasCliente = [];
const formateadorMoneda = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

document.addEventListener('DOMContentLoaded', () => {
    todasLasFilas = Array.from(document.querySelectorAll('.fila-pago'));
    filasCuotasCliente = Array.from(document.querySelectorAll('.fila-cuota-cliente'));

    if (Object.keys(resumenVehiculos).length > 0 || configuracion.hayPagos) {
        let totalGlobal = 0;
        let saldoGlobal = 0;
        for (const placa in resumenVehiculos) {
            if (placa === 'todos') continue;
            totalGlobal += Number(resumenVehiculos[placa].total || 0);
            saldoGlobal += Number(resumenVehiculos[placa].saldo || 0);
        }
        resumenVehiculos['todos'] = { total: totalGlobal, saldo: saldoGlobal };
        filtrarPorVehiculo('todos');
    }
});

// =========================================================
// FILTRADO Y ACTUALIZACIÓN DE TARJETAS + CUOTAS
// =========================================================
function filtrarPorVehiculo(placa) {
    if (placa === 'todos') {
        filasActivas = todasLasFilas;
    } else {
        filasActivas = todasLasFilas.filter(fila => fila.getAttribute('data-placa') === placa);
    }

    filasCuotasCliente.forEach(tr => {
        const placaCuota = tr.getAttribute('data-placa');
        tr.style.display = (placa === 'todos' || placaCuota === placa) ? '' : 'none';
    });

    paginaActual = 1;
    renderizarTabla();
    renderizarPaginacion();

    const datos = resumenVehiculos[placa];
    if (datos) {
        const elTotal = document.getElementById('card-total-auto');
        const elSaldo = document.getElementById('card-saldo-pendiente');
        const elProgresoTxt = document.getElementById('card-progreso-txt');
        const elProgresoBar = document.getElementById('card-progreso-bar');

        if (elTotal) elTotal.innerText = formateadorMoneda.format(datos.total);
        if (elSaldo) elSaldo.innerText = formateadorMoneda.format(datos.saldo);

        const pagado = datos.total - datos.saldo;
        let porcentaje = datos.total > 0 ? Math.round((pagado / datos.total) * 100) : 0;
        porcentaje = Math.max(0, Math.min(100, porcentaje));

        if (elProgresoTxt) elProgresoTxt.innerText = `${porcentaje}%`;
        if (elProgresoBar) elProgresoBar.style.width = `${porcentaje}%`;
    }
}

// =========================================================
// PAGINACIÓN LÓGICA
// =========================================================
function renderizarTabla() {
    todasLasFilas.forEach(fila => (fila.style.display = 'none'));
    const indiceInicio = (paginaActual - 1) * filasPorPagina;
    const filasAMostrar = filasActivas.slice(indiceInicio, indiceInicio + filasPorPagina);
    filasAMostrar.forEach(fila => (fila.style.display = ''));
}

function renderizarPaginacion() {
    const totalPaginas = Math.ceil(filasActivas.length / filasPorPagina);
    const ul = document.getElementById('paginacion-ul');
    if (!ul) return;

    ul.innerHTML = '';
    if (totalPaginas <= 1) return;

    ul.innerHTML += `<li class="page-item ${paginaActual === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="cambiarPagina(event, ${paginaActual - 1})">Anterior</a>
    </li>`;

    for (let i = 1; i <= totalPaginas; i++) {
        ul.innerHTML += `<li class="page-item ${paginaActual === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="cambiarPagina(event, ${i})">${i}</a>
        </li>`;
    }

    ul.innerHTML += `<li class="page-item ${paginaActual === totalPaginas ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="cambiarPagina(event, ${paginaActual + 1})">Siguiente</a>
    </li>`;
}

function cambiarPagina(e, nuevaPagina) {
    e.preventDefault();
    const totalPaginas = Math.ceil(filasActivas.length / filasPorPagina);
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas) {
        paginaActual = nuevaPagina;
        renderizarTabla();
        renderizarPaginacion();
    }
}

// =========================================================
// MODAL VER DETALLES
// =========================================================
window.abrirModalVer = function (metodo, moneda, simbolo, monedaDigital, simboloDigital, ref, desc, banco, estado, cuotasAplicadas) {
    document.getElementById('ver_metodo').innerText = metodo || 'Sin especificar';

    let textoMoneda = '';
    if (monedaDigital && monedaDigital !== 'None') {
        textoMoneda = monedaDigital;
        if (simboloDigital && simboloDigital !== 'None') textoMoneda += ` (${simboloDigital})`;
    } else if (moneda && moneda !== 'None') {
        textoMoneda = moneda;
        if (simbolo && simbolo !== 'None') textoMoneda += ` (${simbolo})`;
    } else {
        textoMoneda = 'No aplica';
    }
    document.getElementById('ver_moneda').innerText = textoMoneda;
    document.getElementById('ver_ref').innerText = (ref && ref !== 'None') ? ref : 'N/A';
    document.getElementById('ver_desc').innerText = (desc && desc !== 'None') ? desc : 'Sin notas registradas.';

    const elCuotas = document.getElementById('ver_cuotas');
    if (elCuotas) {
        elCuotas.innerText = (cuotasAplicadas && cuotasAplicadas !== 'None') ? cuotasAplicadas : 'Abono / Inicial';
    }

    const elementoEstado = document.getElementById('ver_estado');
    if (estado === 'anulado') {
        elementoEstado.innerText = 'Pago Anulado';
        elementoEstado.className = 'text-danger fw-bold';
    } else {
        elementoEstado.innerText = 'Procesado';
        elementoEstado.className = 'text-success fw-bold';
    }

    const contBanco = document.getElementById('contenedor_banco');
    if (banco && banco !== 'None' && banco !== '') {
        document.getElementById('ver_banco').innerHTML = '<i class="bi bi-bank2 me-1"></i>' + banco;
        contBanco.style.setProperty('display', 'flex', 'important');
    } else {
        contBanco.style.setProperty('display', 'none', 'important');
    }

    const modalElement = document.getElementById('modalVerPago');
    const bsModal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
    bsModal.show();
};

// =========================================================
// ABRIR COMPROBANTE PDF
// =========================================================
window.imprimirRecibo = function (idPago) {
    if (configuracion.urlFacturaBase) {
        const url = configuracion.urlFacturaBase.replace('/0', '/' + idPago);
        window.open(url, '_blank', 'noopener,noreferrer');
    }
};