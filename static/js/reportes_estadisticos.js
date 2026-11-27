document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('selector-reporte');
    const btnGenerar = document.getElementById('btn-generar');
    const filtrosContainer = document.getElementById('filtros-container');
    const kpiContainer = document.getElementById('kpi-container');
    const chartsContainer = document.getElementById('charts-container');
    const tablaDetalleContainer = document.getElementById('tabla-detalle-container');
    const tablaDetalle = document.getElementById('tabla-detalle');
    const exportButtons = document.querySelectorAll('.exportar-opcion');


    let moduloActual = selector.value;
    let chartsInstances = [];


    const filtrosPorModulo = {
        ventas: [
            { nombre: 'placa', tipo: 'text', label: 'Placa' },
            { nombre: 'fecha_desde', tipo: 'date', label: 'Fecha desde' },
            { nombre: 'fecha_hasta', tipo: 'date', label: 'Fecha hasta' },
            {
                nombre: 'tipo_venta',
                tipo: 'select',
                label: 'Tipo de venta',
                opciones: ['', 'contado', 'credito', 'crédito']
            },
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'pendiente', 'procesada', 'anulada']
            },
            { nombre: 'cedula_usuario', tipo: 'text', label: 'Cédula usuario' },
            { nombre: 'min_precio', tipo: 'number', label: 'Precio mínimo' },
            { nombre: 'max_precio', tipo: 'number', label: 'Precio máximo' },
            {
                nombre: 'con_poder',
                tipo: 'select',
                label: '¿Con poder?',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Sí' },
                    { valor: '0', texto: 'No' }
                ]
            },
            {
                nombre: 'con_traspaso',
                tipo: 'select',
                label: '¿Con traspaso?',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Sí' },
                    { valor: '0', texto: 'No' }
                ]
            }
        ],
        vehiculos: [
            { nombre: 'placa', tipo: 'text', label: 'Placa' },
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'disponible', 'vendido', 'mantenimiento', 'servicio']
            },
            {
                nombre: 'cod_tipo',
                tipo: 'select',
                label: 'Tipo de vehículo',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Sedan' },
                    { valor: '2', texto: 'Pick-up' },
                    { valor: '3', texto: 'Coupe' },
                    { valor: '4', texto: 'Suv' }
                ]
            },
            {
                nombre: 'cod_modelo',
                tipo: 'select',
                label: 'Modelo',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Hilux' },
                    { valor: '2', texto: 'tt' },
                    { valor: '3', texto: 'aveo' },
                    { valor: '4', texto: 'optra' },
                    { valor: '5', texto: 'spark' },
                    { valor: '6', texto: 'silverado' },
                    { valor: '7', texto: 'fiesta' },
                    { valor: '8', texto: 'fusion' },
                    { valor: '9', texto: 'triton' },
                    { valor: '10', texto: 'balita' },
                    { valor: '11', texto: 'civic' },
                    { valor: '12', texto: 'crv' },
                    { valor: '13', texto: 'pilot' },
                    { valor: '14', texto: 'acorrd' },
                    { valor: '15', texto: 'delsol' }
                ]
            },
            { nombre: 'anio_desde', tipo: 'number', label: 'Año desde' },
            { nombre: 'anio_hasta', tipo: 'number', label: 'Año hasta' },
            { nombre: 'min_kilometraje', tipo: 'number', label: 'Kilometraje mínimo' },
            { nombre: 'max_kilometraje', tipo: 'number', label: 'Kilometraje máximo' },
            { nombre: 'cedula_propietario', tipo: 'number', label: 'Cédula propietario' },
            { nombre: 'cod_documento', tipo: 'number', label: 'Cód. documento' },
            { nombre: 'cod_accesorio', tipo: 'number', label: 'Cód. accesorio' }
        ],
        mantenimiento: [
            { nombre: 'placa', tipo: 'text', label: 'Placa' },
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'Pendiente', 'Activo', 'Finalizado', 'Inactivo']
            },
            {
                nombre: 'tipo',
                tipo: 'select',
                label: 'Tipo',
                opciones: ['', 'Preventivo', 'Correctivo']
            },
            { nombre: 'cod_mantenimiento', tipo: 'number', label: 'Cód. mantenimiento' },
            { nombre: 'cod_taller', tipo: 'number', label: 'Cód. taller' },
            { nombre: 'fecha_solicitud_desde', tipo: 'date', label: 'Fecha solicitud desde' },
            { nombre: 'fecha_solicitud_hasta', tipo: 'date', label: 'Fecha solicitud hasta' },
            { nombre: 'min_costo_base', tipo: 'number', label: 'Costo base mínimo' },
            { nombre: 'max_costo_base', tipo: 'number', label: 'Costo base máximo' },
            { nombre: 'min_costo_final', tipo: 'number', label: 'Costo final mínimo' },
            { nombre: 'max_costo_final', tipo: 'number', label: 'Costo final máximo' },
            {
                nombre: 'con_observaciones',
                tipo: 'select',
                label: '¿Con observaciones?',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Sí' },
                    { valor: '0', texto: 'No' }
                ]
            },
            {
                nombre: 'con_fecha_completada',
                tipo: 'select',
                label: '¿Completado?',
                opciones: [
                    { valor: '', texto: 'Todos' },
                    { valor: '1', texto: 'Sí' },
                    { valor: '0', texto: 'No' }
                ]
            }
        ],
        servicios: [
            { nombre: 'placa', tipo: 'text', label: 'Placa' },
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'Activo', 'Finalizado', 'Inactivo']
            },
            { nombre: 'cod_servicios', tipo: 'number', label: 'Cód. servicio' },
            { nombre: 'fecha_realizacion_desde', tipo: 'date', label: 'Fecha realización desde' },
            { nombre: 'fecha_realizacion_hasta', tipo: 'date', label: 'Fecha realización hasta' },
            { nombre: 'min_costo_base', tipo: 'number', label: 'Costo base mínimo' },
            { nombre: 'max_costo_base', tipo: 'number', label: 'Costo base máximo' },
            { nombre: 'min_costo_final', tipo: 'number', label: 'Costo final mínimo' },
            { nombre: 'max_costo_final', tipo: 'number', label: 'Costo final máximo' }
        ],
        citas: [
            { nombre: 'placa', tipo: 'text', label: 'Placa' },
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'Pendiente', 'Atendida', 'Cancelada']
            },
            { nombre: 'cod_catalogo', tipo: 'number', label: 'Cód. catálogo' },
            { nombre: 'cedula_usuario', tipo: 'text', label: 'Cédula usuario' },
            { nombre: 'fecha_desde', tipo: 'date', label: 'Fecha desde' },
            { nombre: 'fecha_hasta', tipo: 'date', label: 'Fecha hasta' },
            { nombre: 'hora_desde', tipo: 'time', label: 'Hora desde' },
            { nombre: 'hora_hasta', tipo: 'time', label: 'Hora hasta' }
        ],
        compras_insumos: [
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado',
                opciones: ['', 'Confirmada', 'Pendiente']
            },
            { nombre: 'cod_compras', tipo: 'number', label: 'Cód. compra' },
            { nombre: 'cod_insumo', tipo: 'number', label: 'Cód. insumo' },
            { nombre: 'rif_cedula_proveedor', tipo: 'number', label: 'RIF/Cédula proveedor' },
            { nombre: 'fecha_compra_desde', tipo: 'date', label: 'Fecha compra desde' },
            { nombre: 'fecha_compra_hasta', tipo: 'date', label: 'Fecha compra hasta' },
            { nombre: 'min_cantidad', tipo: 'number', label: 'Cantidad mínima' },
            { nombre: 'max_cantidad', tipo: 'number', label: 'Cantidad máxima' },
            { nombre: 'min_precio', tipo: 'number', label: 'Precio mínimo' },
            { nombre: 'max_precio', tipo: 'number', label: 'Precio máximo' }
        ],
        pagos: [
            {
                nombre: 'estado',
                tipo: 'select',
                label: 'Estado de cuenta',
                opciones: ['', 'Pendiente', 'pagado', 'Anulada']
            },
            { nombre: 'cod_cuentas', tipo: 'number', label: 'Cód. cuenta' },
            { nombre: 'cod_venta', tipo: 'number', label: 'Cód. venta' },
            { nombre: 'fecha_emision_desde', tipo: 'date', label: 'Fecha emisión desde' },
            { nombre: 'fecha_emision_hasta', tipo: 'date', label: 'Fecha emisión hasta' },
            { nombre: 'fecha_vencimiento_desde', tipo: 'date', label: 'Fecha vencimiento desde' },
            { nombre: 'fecha_vencimiento_hasta', tipo: 'date', label: 'Fecha vencimiento hasta' },
            { nombre: 'min_deuda_total', tipo: 'number', label: 'Deuda total mínima' },
            { nombre: 'max_deuda_total', tipo: 'number', label: 'Deuda total máxima' },
            { nombre: 'min_deuda', tipo: 'number', label: 'Deuda mínima' },
            { nombre: 'max_deuda', tipo: 'number', label: 'Deuda máxima' }
        ]
    };


    function renderFiltros(modulo) {
        filtrosContainer.innerHTML = '';
        const filtros = filtrosPorModulo[modulo] || [];


        if (!filtros.length) {
            filtrosContainer.innerHTML = `
                <p class="text-muted mb-0">
                    Este módulo no tiene filtros configurados.
                </p>
            `;
            return;
        }


        const row = document.createElement('div');
        row.className = 'row g-3';


        filtros.forEach(filtro => {
            const col = document.createElement('div');
            col.className = 'col-md-3';


            const label = document.createElement('label');
            label.className = 'form-label fw-bold';
            label.htmlFor = `filtro-${filtro.nombre}`;
            label.textContent = filtro.label;


            let input;


            if (filtro.tipo === 'select') {
                input = document.createElement('select');
                input.className = 'form-select';


                filtro.opciones.forEach(opcion => {
                    const option = document.createElement('option');


                    if (typeof opcion === 'object') {
                        option.value = opcion.valor;
                        option.textContent = opcion.texto;
                    } else {
                        option.value = opcion;
                        option.textContent = opcion === '' ? 'Todos' : opcion;
                    }


                    input.appendChild(option);
                });


            } else {
                input = document.createElement('input');
                input.type = filtro.tipo;
                input.className = 'form-control';
            }


            input.id = `filtro-${filtro.nombre}`;
            input.name = filtro.nombre;


            col.appendChild(label);
            col.appendChild(input);
            row.appendChild(col);
        });


        filtrosContainer.appendChild(row);
    }


    function obtenerParametros() {
        const filtros = filtrosPorModulo[moduloActual] || [];
        const params = {};


        filtros.forEach(filtro => {
            const input = document.getElementById(`filtro-${filtro.nombre}`);


            if (input && input.value !== '' && input.value !== null) {
                params[filtro.nombre] = input.value;
            }
        });


        return params;
    }


    function destruirGraficos() {
        chartsInstances.forEach(info => {
            try {
                info.chart.destroy();
            } catch (error) {
                console.warn('No se pudo destruir un gráfico anterior:', error);
            }
        });


        chartsInstances = [];
    }


    function crearLoader() {
        return `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="text-muted mb-0 fw-semibold">
                    Generando estadísticas y analizando los registros...
                </p>
            </div>
        `;
    }


    function renderKPIs(kpis) {
        kpiContainer.innerHTML = '';


        (kpis || []).forEach(kpi => {
            const col = document.createElement('div');
            col.className = 'col-md-3 mb-3';


            col.innerHTML = `
                <div class="card shadow-sm border-start border-4 border-${kpi.color} h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h6 class="text-muted mb-1">${kpi.titulo}</h6>
                                <h3 class="fw-bold mb-0">${kpi.valor}</h3>
                            </div>
                            <div class="ms-3">
                                <i class="bi ${kpi.icono} fs-1 text-${kpi.color}"></i>
                            </div>
                        </div>
                    </div>
                </div>
            `;


            kpiContainer.appendChild(col);
        });
    }


    function formatoMoneda(valor) {
        return '$' + Number(valor || 0).toLocaleString('es-VE', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }


    function formatoEntero(valor) {
        return Math.round(Number(valor || 0)).toLocaleString('es-VE');
    }


    function obtenerConfiguracionEjesY(grafico, chartType) {
        if (chartType !== 'area' && chartType !== 'line' && chartType !== 'bar') {
            return {};
        }


        if (grafico.id === 'ventas-area') {
            return [
                {
                    seriesName: 'Cantidad',
                    title: {
                        text: 'Cantidad de ventas'
                    },
                    min: 0,
                    forceNiceScale: true,
                    tickAmount: 5,
                    labels: {
                        formatter: value => formatoEntero(value)
                    }
                },
                {
                    seriesName: 'Monto',
                    opposite: true,
                    title: {
                        text: 'Monto total ($)'
                    },
                    min: 0,
                    forceNiceScale: true,
                    tickAmount: 5,
                    labels: {
                        formatter: value => formatoMoneda(value)
                    }
                }
            ];
        }


        if (grafico.id === 'vehiculos-area-anio') {
            return {
                title: {
                    text: 'Cantidad de vehículos'
                },
                min: 0,
                forceNiceScale: true,
                tickAmount: 5,
                decimalsInFloat: 0,
                labels: {
                    formatter: value => formatoEntero(value)
                }
            };
        }


        if (grafico.id === 'mant-area-mes') {
            return {
                title: {
                    text: 'Cantidad de mantenimientos'
                },
                min: 0,
                forceNiceScale: true,
                tickAmount: 5,
                decimalsInFloat: 0,
                labels: {
                    formatter: value => formatoEntero(value)
                }
            };
        }


        if (grafico.id === 'citas-area-mes') {
            return {
                title: {
                    text: 'Cantidad de citas'
                },
                min: 0,
                forceNiceScale: true,
                tickAmount: 5,
                decimalsInFloat: 0,
                labels: {
                    formatter: value => formatoEntero(value)
                }
            };
        }


        if (grafico.id === 'compras-area-mes') {
            return [
                {
                    seriesName: 'Cantidad',
                    title: {
                        text: 'Cantidad de compras'
                    },
                    min: 0,
                    forceNiceScale: true,
                    tickAmount: 5,
                    decimalsInFloat: 0,
                    labels: {
                        formatter: value => formatoEntero(value)
                    }
                },
                {
                    seriesName: 'Monto',
                    opposite: true,
                    title: {
                        text: 'Monto total ($)'
                    },
                    min: 0,
                    forceNiceScale: true,
                    tickAmount: 5,
                    labels: {
                        formatter: value => formatoMoneda(value)
                    }
                }
            ];
        }


        if (grafico.id === 'pagos-area-mes') {
            return {
                title: {
                    text: 'Monto abonado ($)'
                },
                min: 0,
                forceNiceScale: true,
                tickAmount: 5,
                labels: {
                    formatter: value => formatoMoneda(value)
                }
            };
        }


        if (grafico.id === 'servicios-area-mes') {
            return {
                title: {
                    text: 'Cantidad de servicios'
                },
                min: 0,
                forceNiceScale: true,
                tickAmount: 5,
                decimalsInFloat: 0,
                labels: {
                    formatter: value => formatoEntero(value)
                }
            };
        }


        return {
            min: 0,
            forceNiceScale: true,
            tickAmount: 5,
            labels: {
                formatter: value => formatoEntero(value)
            }
        };
    }


    function obtenerTooltipFormatter(grafico) {
        const idsMoneda = [
            'ventas-area',
            'compras-area-mes',
            'pagos-area-mes',
            'pagos-barra-cuentas'
        ];


        return value => {
            if (idsMoneda.includes(grafico.id)) {
                return formatoMoneda(value);
            }


            return formatoEntero(value);
        };
    }


    function renderGraficos(graficos) {
        chartsContainer.innerHTML = '';


        (graficos || []).forEach(grafico => {
            const col = document.createElement('div');
            col.className = grafico.colSpan || 'col-md-6';


            const card = document.createElement('div');
            card.className = 'card shadow-sm mb-3 h-100';


            card.innerHTML = `
                <div class="card-header bg-light fw-bold">
                    <i class="bi bi-graph-up"></i> ${grafico.titulo}
                </div>
                <div class="card-body">
                    <div id="${grafico.id}"></div>
                </div>
            `;


            col.appendChild(card);
            chartsContainer.appendChild(col);


            const container = document.getElementById(grafico.id);


            if (!container) {
                console.warn('No se encontró el contenedor del gráfico:', grafico.id);
                return;
            }


            const labels = Array.isArray(grafico.labels) ? grafico.labels : [];
            const datasets = Array.isArray(grafico.datasets) ? grafico.datasets : [];
            const firstData = (
                datasets[0] &&
                Array.isArray(datasets[0].data)
            ) ? datasets[0].data : [];


            if (!labels.length || !firstData.length) {
                container.innerHTML = `
                    <p class="text-muted text-center mb-0">
                        Sin datos para esta gráfica con los filtros seleccionados.
                    </p>
                `;
                return;
            }


            let chartType = grafico.tipo;


            if (chartType === 'doughnut') {
                chartType = 'donut';
            }


            let seriesConfig;


            if (chartType === 'pie' || chartType === 'donut') {
                seriesConfig = firstData.map(valor => Number(valor) || 0);
            } else {
                seriesConfig = datasets.map(dataset => ({
                    name: dataset.name || 'Serie',
                    data: (dataset.data || []).map(valor => Number(valor) || 0)
                }));
            }


            const options = {
                series: seriesConfig,


                chart: {
                    type: chartType,
                    height: 310,
                    toolbar: {
                        show: true
                    },
                    animations: {
                        enabled: true,
                        easing: 'easeOutBack',
                        speed: 1200,
                        animateGradually: {
                            enabled: true,
                            delay: 180
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 700
                        }
                    }
                },


                labels: labels,


                colors: [
                    '#0d6efd',
                    '#198754',
                    '#0dcaf0',
                    '#ffc107',
                    '#dc3545',
                    '#6f42c1',
                    '#fd7e14',
                    '#20c997'
                ],


                xaxis: (
                    chartType === 'bar' ||
                    chartType === 'line' ||
                    chartType === 'area'
                ) ? {
                    categories: labels,
                    title: {
                        text: grafico.id.includes('area')
                            ? 'Período'
                            : ''
                    }
                } : {},


                yaxis: obtenerConfiguracionEjesY(grafico, chartType),


                dataLabels: {
                    enabled: chartType === 'pie' || chartType === 'donut'
                },


                plotOptions: chartType === 'bar'
                    ? {
                        bar: {
                            borderRadius: 6,
                            columnWidth: '58%'
                        }
                    }
                    : chartType === 'donut'
                        ? {
                            pie: {
                                donut: {
                                    size: '62%'
                                }
                            }
                        }
                        : {},


                stroke: {
                    width: chartType === 'line' || chartType === 'area' ? 3 : 1,
                    curve: chartType === 'line' || chartType === 'area'
                        ? 'smooth'
                        : 'straight'
                },


                fill: chartType === 'area'
                    ? {
                        type: 'gradient',
                        gradient: {
                            shade: 'light',
                            type: 'vertical',
                            shadeIntensity: 0.6,
                            opacityFrom: 0.35,
                            opacityTo: 0.05,
                            stops: [0, 60, 100]
                        }
                    }
                    : {
                        opacity: 0.92
                    },


                legend: {
                    position: 'bottom'
                },


                tooltip: {
                    shared: chartType === 'line' || chartType === 'area',
                    intersect: false,
                    y: {
                        formatter: obtenerTooltipFormatter(grafico)
                    }
                },


                noData: {
                    text: 'Sin datos disponibles',
                    align: 'center',
                    verticalAlign: 'middle'
                }
            };


            try {
                const chart = new ApexCharts(container, options);
                chart.render();


                chartsInstances.push({
                    id: grafico.id,
                    chart: chart,
                    tipo: chartType,
                    seriesOriginal: seriesConfig
                });
            } catch (error) {
                console.error(`Error al renderizar el gráfico ${grafico.id}:`, error);


                container.innerHTML = `
                    <p class="text-danger text-center mb-0">
                        No fue posible renderizar esta gráfica.
                    </p>
                `;
            }
        });
    }


    function renderTablaDetalle(detalle) {
        if (!detalle || !detalle.columnas || !detalle.filas) {
            tablaDetalleContainer.style.display = 'none';
            return;
        }


        tablaDetalle.innerHTML = '';


        const thead = document.createElement('thead');
        thead.className = 'table-light';


        const trHeader = document.createElement('tr');


        detalle.columnas.forEach(columna => {
            const th = document.createElement('th');
            th.textContent = columna;
            trHeader.appendChild(th);
        });


        thead.appendChild(trHeader);
        tablaDetalle.appendChild(thead);


        const tbody = document.createElement('tbody');


        detalle.filas.forEach(fila => {
            const tr = document.createElement('tr');


            fila.forEach(celda => {
                const td = document.createElement('td');
                td.textContent = celda;
                tr.appendChild(td);
            });


            tbody.appendChild(tr);
        });


        tablaDetalle.appendChild(tbody);
        tablaDetalleContainer.style.display = 'block';
    }


    selector.addEventListener('change', () => {
        moduloActual = selector.value;
        renderFiltros(moduloActual);
        kpiContainer.innerHTML = '';
        chartsContainer.innerHTML = '';
        tablaDetalleContainer.style.display = 'none';
        destruirGraficos();
    });


    btnGenerar.addEventListener('click', async () => {
        kpiContainer.innerHTML = crearLoader();
        chartsContainer.innerHTML = crearLoader();
        tablaDetalleContainer.style.display = 'none';
        destruirGraficos();


        const parametros = obtenerParametros();


        try {
            const queryString = new URLSearchParams(parametros).toString();
            
            const response = await fetch(`/api/reportes/${moduloActual}?${queryString}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });


            const datos = await response.json();


            if (datos.error) {
                kpiContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Error: ${datos.error}
                    </div>
                `;
                chartsContainer.innerHTML = '';
                return;
            }


            renderKPIs(datos.kpis);
            renderGraficos(datos.graficos);
            renderTablaDetalle(datos.detalle_tabla);


        } catch (error) {
            console.error('Error al generar estadísticas:', error);
            kpiContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error de conexión. Intente nuevamente.
                </div>
            `;
            chartsContainer.innerHTML = '';
        }
    });


    exportButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const formato = btn.getAttribute('data-formato');
            
            const parametros = obtenerParametros();
            parametros.formato = formato;
            const queryString = new URLSearchParams(parametros).toString();
            
            window.open(`/api/reportes/${moduloActual}/exportar?${queryString}`, '_blank');
        });
    });


    renderFiltros(moduloActual);
});