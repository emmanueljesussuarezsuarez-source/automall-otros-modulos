document.addEventListener("DOMContentLoaded", function () {
    // Tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    // --- PAGINACIÓN Y FILTRADO DE PAGOS ---
    const registrosPorPagina = 10;
    let paginaActual = 1;

    const inputBuscar = document.getElementById("inputBuscarPlaca");
    const btnLimpiar = document.getElementById("btnLimpiarPlaca");
    const filas = Array.from(document.querySelectorAll(".fila-pago"));
    const filaSinResultados = document.getElementById("filaSinResultados");
    const infoPaginacion = document.getElementById("infoPaginacion");
    const contenedorPaginacion = document.getElementById("contenedorPaginacion");

    // --- FILTRADO DE CUOTAS ---
    const filasCuotas = Array.from(document.querySelectorAll(".fila-cuota-admin"));
    const filtroEstadoCuota = document.getElementById("filtroEstadoCuotaAdmin");

    function obtenerFilasFiltradas() {
        const query = (inputBuscar?.value || "").trim().toUpperCase();
        return filas.filter(fila => {
            const placa = fila.getAttribute("data-placa") || "";
            return placa.includes(query);
        });
    }

    function renderizarTabla() {
        const filasFiltradas = obtenerFilasFiltradas();
        const totalRegistros = filasFiltradas.length;
        const totalPaginas = Math.ceil(totalRegistros / registrosPorPagina) || 1;

        if (paginaActual > totalPaginas) paginaActual = totalPaginas;
        if (paginaActual < 1) paginaActual = 1;

        filas.forEach(f => (f.style.display = "none"));

        if (totalRegistros === 0) {
            filaSinResultados?.classList.remove("d-none");
        } else {
            filaSinResultados?.classList.add("d-none");
            const inicio = (paginaActual - 1) * registrosPorPagina;
            const visibles = filasFiltradas.slice(inicio, inicio + registrosPorPagina);
            visibles.forEach(f => (f.style.display = ""));
        }

        renderizarPaginador(totalRegistros, totalPaginas);
    }

    function filtrarTablaCuotas() {
        if (filasCuotas.length === 0) return;
        const query = (inputBuscar?.value || "").trim().toUpperCase();
        const estadoFiltro = (filtroEstadoCuota?.value || "todas").toLowerCase();

        filasCuotas.forEach(fila => {
            const placa = (fila.getAttribute("data-placa") || "").toUpperCase();
            const estado = (fila.getAttribute("data-estado") || "").toLowerCase();
            const coincidePlaca = placa.includes(query);
            const coincideEstado = estadoFiltro === "todas" || estado === estadoFiltro;
            fila.style.display = (coincidePlaca && coincideEstado) ? "" : "none";
        });
    }

    function renderizarPaginador(totalRegistros, totalPaginas) {
        if (!infoPaginacion || !contenedorPaginacion) return;
        infoPaginacion.innerHTML = `Mostrando página <strong>${paginaActual}</strong> de <strong>${totalPaginas}</strong> (<strong>${totalRegistros}</strong> registros)`;
        contenedorPaginacion.innerHTML = "";

        const liPrev = document.createElement("li");
        liPrev.className = `page-item ${paginaActual === 1 ? "disabled" : ""}`;
        liPrev.innerHTML = `<button class="page-link rounded-2 border-0 bg-light text-dark px-2"><i class="bi bi-chevron-left"></i></button>`;
        liPrev.onclick = () => { if (paginaActual > 1) { paginaActual--; renderizarTabla(); } };
        contenedorPaginacion.appendChild(liPrev);

        for (let i = 1; i <= totalPaginas; i++) {
            const li = document.createElement("li");
            li.className = `page-item ${i === paginaActual ? "active" : ""}`;
            li.innerHTML = `<button class="page-link rounded-2 border-0 ${i === paginaActual ? "bg-primary text-white fw-bold shadow-sm" : "bg-light text-dark"}">${i}</button>`;
            li.onclick = () => { paginaActual = i; renderizarTabla(); };
            contenedorPaginacion.appendChild(li);
        }

        const liNext = document.createElement("li");
        liNext.className = `page-item ${paginaActual === totalPaginas ? "disabled" : ""}`;
        liNext.innerHTML = `<button class="page-link rounded-2 border-0 bg-light text-dark px-2"><i class="bi bi-chevron-right"></i></button>`;
        liNext.onclick = () => { if (paginaActual < totalPaginas) { paginaActual++; renderizarTabla(); } };
        contenedorPaginacion.appendChild(liNext);
    }

    inputBuscar?.addEventListener("input", function () {
        btnLimpiar?.classList.toggle("d-none", this.value.trim() === "");
        paginaActual = 1;
        renderizarTabla();
        filtrarTablaCuotas();
    });

    btnLimpiar?.addEventListener("click", function () {
        if (inputBuscar) inputBuscar.value = "";
        btnLimpiar.classList.add("d-none");
        paginaActual = 1;
        renderizarTabla();
        filtrarTablaCuotas();
    });

    filtroEstadoCuota?.addEventListener("change", filtrarTablaCuotas);

    renderizarTabla();
    filtrarTablaCuotas();

    // --- VALIDACIÓN DE MOTIVO DE ANULACIÓN ---
    const textareaMotivo = document.getElementById("motivo_anulacion");
    if (textareaMotivo) {
        textareaMotivo.addEventListener("input", function () {
            this.value = this.value.replace(/[0-9]/g, "");
        });
    }

    const formAnularPago = document.getElementById("formAnularPago");
    if (formAnularPago) {
        formAnularPago.addEventListener("submit", function () {
            const modalEl = document.getElementById("modalAnularPago");
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();

            if (typeof Swal !== "undefined") {
                Swal.fire({
                    title: "Procesando...",
                    text: "Anulando pago y actualizando el estado de la cuenta y sus cuotas...",
                    allowOutsideClick: false,
                    didOpen: () => { Swal.showLoading(); }
                });
            }
        });
    }
});

function abrirModalAnular(id, placa) {
    document.getElementById("anular_cod_pagos").value = id;
    document.getElementById("anular_placa").value = placa;

    const modalEl = document.getElementById("modalAnularPago");
    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}

function abrirComprobante(idPago) {
    if (window.rutaGenerarFacturaBase) {
        const url = window.rutaGenerarFacturaBase.replace("/0", "/" + idPago);
        window.open(url, "_blank", "noopener,noreferrer");
    } else {
        console.error("Ruta base no definida para generar factura");
    }
}