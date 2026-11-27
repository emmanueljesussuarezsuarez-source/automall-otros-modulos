document.addEventListener('DOMContentLoaded', function () {
    const selector = document.getElementById('selector-reporte');
    const inputDesde = document.getElementById('fecha_desde');
    const inputHasta = document.getElementById('fecha_hasta');
    const btnGenerar = document.getElementById('btn-generar');
    const kpiContainer = document.getElementById('kpi-container');
    const chartsContainer = document.getElementById('charts-container');
    const botonesExportar = document.querySelectorAll('.dropdown-item[data-formato]');

    let chartsInstances = [];

    async function cargarReporte() {
        const modulo = selector.value;
        const fechaDesde = inputDesde.value;
        const fechaHasta = inputHasta.value;

        let queryParams = new URLSearchParams();
        if (fechaDesde) queryParams.append('fecha_desde', fechaDesde);
        if (fechaHasta) queryParams.append('fecha_hasta', fechaHasta);

        try {
            const res = await fetch(`/api/reportes/${modulo}?${queryParams.toString()}`);
            const datos = await res.json();

            if (!datos.status) {
                alert(datos.error || 'Error al cargar los datos del reporte');
                return;
            }

            // Destruir gráficos previos
            chartsInstances.forEach(c => c.destroy());
            chartsInstances = [];
            chartsContainer.innerHTML = '';
            kpiContainer.innerHTML = '';

            // Renderizar Tarjetas KPI
            if (datos.kpis && datos.kpis.length > 0) {
                datos.kpis.forEach(kpi => {
                    kpiContainer.innerHTML += `
                        <div class="col-md-${12 / datos.kpis.length}">
                            <div class="card border-start border-4 border-${kpi.color || 'primary'} shadow-sm">
                                <div class="card-body d-flex align-items-center justify-content-between">
                                    <div>
                                        <h6 class="text-muted mb-1">${kpi.titulo}</h6>
                                        <h3 class="fw-bold mb-0">${kpi.valor}</h3>
                                    </div>
                                    <i class="bi ${kpi.icono || 'bi-bar-chart'} fs-1 text-${kpi.color || 'primary'} opacity-50"></i>
                                </div>
                            </div>
                        </div>`;
                });
            }

            // Renderizar las 5 Gráficas
            if (datos.graficos && datos.graficos.length > 0) {
                datos.graficos.forEach(g => {
                    const col = document.createElement('div');
                    col.className = 'col-md-6 mb-4';
                    col.innerHTML = `
                        <div class="card shadow-sm h-100">
                            <div class="card-header bg-white fw-bold text-secondary border-bottom-0 pt-3">${g.titulo}</div>
                            <div class="card-body"><div id="${g.id}"></div></div>
                        </div>`;
                    chartsContainer.appendChild(col);

                    let seriesConfig;
                    if (g.tipo === 'pie' || g.tipo === 'doughnut') {
                        seriesConfig = g.datasets[0].data;
                    } else {
                        seriesConfig = g.datasets.map(d => ({
                            name: d.name || g.titulo,
                            data: d.data
                        }));
                    }

                    const opciones = {
                        series: seriesConfig,
                        chart: {
                            type: g.tipo,
                            height: 320,
                            toolbar: { show: false }
                        },
                        labels: g.labels || [],
                        colors: ['#20639B', '#F6D55C', '#ED553B', '#3CAEA3', '#173F5F', '#8E44AD'],
                        legend: { position: 'bottom' },
                        dataLabels: { enabled: true }
                    };

                    const chart = new ApexCharts(document.querySelector(`#${g.id}`), opciones);
                    chart.render();
                    chartsInstances.push(chart);
                });
            }

        } catch (error) {
            console.error('Error al solicitar estadísticas:', error);
        }
    }

    btnGenerar.addEventListener('click', cargarReporte);

    botonesExportar.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const formato = this.getAttribute('data-formato');
            const modulo = selector.value;
            const fechaDesde = inputDesde.value;
            const fechaHasta = inputHasta.value;

            let queryParams = new URLSearchParams({ formato: formato });
            if (fechaDesde) queryParams.append('fecha_desde', fechaDesde);
            if (fechaHasta) queryParams.append('fecha_hasta', fechaHasta);

            window.location.href = `/api/reportes/${modulo}/exportar?${queryParams.toString()}`;
        });
    });

    cargarReporte();
});