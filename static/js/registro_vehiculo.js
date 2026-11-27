// =========================================================================
// DATATABLES (Solo se inicializa si las tablas existen en la página actual)
// =========================================================================
if (window.jQuery) {
    $(document).ready(function() {
        const configBase = {
            responsive: true,
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
            language: {
                "lengthMenu": "Mostrar _MENU_ registros",
                "zeroRecords": "No se encontraron resultados",
                "info": "Mostrando _START_ a _END_ de _TOTAL_ registros",
                "infoEmpty": "Mostrando 0 a 0 de 0 registros",
                "infoFiltered": "(filtrado de un total de _MAX_ registros)",
                "search": "Buscar:",
                "paginate": {
                    "first": "Primero",
                    "last": "Último",
                    "next": "Siguiente",
                    "previous": "Anterior"
                }
            }
        };

        const $tablasConAcciones = $('#tablaVehiculos, #tablaCatalogo');
        if ($tablasConAcciones.length && $.fn.DataTable) {
            $tablasConAcciones.DataTable({
                ...configBase,
                columnDefs: [{ orderable: false, targets: [0, 6] }]
            });
        }

        if ($('#tablaHistorial').length && $.fn.DataTable) {
            $('#tablaHistorial').DataTable({
                ...configBase,
                order: [[0, 'desc']]
            });
        }
    });
}

// Función Global para confirmar eliminación
function confirmarEliminar(placa) {
    if (!window.Swal) return;
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Eliminarás el vehículo con placa " + placa + ". Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminarlo',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.getElementById('form-eliminar-' + placa);
            if (form) form.submit();
        }
    });
}

// Función Global para marcar foto para eliminar en Editar
function marcarParaEliminar(urlFoto, cardId) {
    if (!window.Swal) return;
    Swal.fire({
        title: '¿Quitar foto?',
        text: "Esta fotografía se eliminará al presionar 'Guardar Cambios'.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, quitar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            const tarjeta = document.getElementById(cardId);
            if (tarjeta) tarjeta.remove();

            const contenedor = document.getElementById('contenedor-fotos-eliminadas');
            if (contenedor) {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'imagenes_eliminar';
                hiddenInput.value = urlFoto;
                contenedor.appendChild(hiddenInput);
            }

            const restantes = document.querySelectorAll('.item-foto-actual');
            if (restantes.length === 0) {
                const galeria = document.getElementById('galeria-fotos-actuales');
                if (galeria) {
                    galeria.innerHTML = '<p class="text-muted small mb-0 ps-1" id="sin-fotos-msg">No hay fotografías guardadas.</p>';
                }
            }
        }
    });
}

// 1. Lógica para asignar la Marca según el Modelo
function seleccionarMarca(selectElem) {
    const opcion = selectElem.options[selectElem.selectedIndex];
    const marcaId = opcion.getAttribute('data-marca');
    const selectMarca = document.getElementById('select-marca');

    if (marcaId && selectMarca) {
        selectMarca.value = String(marcaId);
        for (let i = 0; i < selectMarca.options.length; i++) {
            if (String(selectMarca.options[i].value).trim() === String(marcaId).trim()) {
                selectMarca.selectedIndex = i;
                break;
            }
        }
    } else {
        selectMarca.selectedIndex = 0;
    }
}

// 2. Previsualización de Fotos del Vehículo
function previsualizarFotos(input) {
    const contenedor = document.getElementById('preview-imagenes');
    contenedor.innerHTML = '';

    if (!input.files || input.files.length === 0) {
        contenedor.innerHTML = '<span class="text-muted small my-auto ps-2">No hay fotografías seleccionadas aún.</span>';
        return;
    }

    Array.from(input.files).forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const card = document.createElement('div');
            card.className = 'position-relative border rounded shadow-sm bg-white p-1 text-center';
            card.style.width = '110px';
            card.style.display = 'inline-block';
            card.innerHTML = `
                <div style="width: 100%; height: 75px; overflow: hidden; border-radius: 4px; background: #eee;">
                    <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                <span class="badge bg-dark position-absolute top-0 start-0 m-1" style="font-size: 0.65rem;">#${index + 1}</span>
                <div class="text-truncate small text-muted mt-1 px-1" style="font-size: 0.7rem;" title="${file.name}">${file.name}</div>
            `;
            contenedor.appendChild(card);
        };
        reader.readAsDataURL(file);
    });
}

// =========================================================================
// EVENTOS PRINCIPALES DE LA APLICACIÓN
// =========================================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log("Automall: registro_vehiculo.js cargado correctamente.");

    // 1. MARCA AUTOMÁTICA SEGÚN MODELO
    const selectMarca = document.getElementById('select-marca');
    const selectModelo = document.getElementById('select-modelo');

    function actualizarMarcaPorModelo() {
        if (!selectModelo || !selectMarca) return;
        const opcion = selectModelo.options[selectModelo.selectedIndex];
        if (!opcion) return;

        const marcaId = opcion.getAttribute('data-marca');
        if (marcaId !== null && marcaId !== undefined && marcaId !== "") {
            let asignado = false;
            for (let i = 0; i < selectMarca.options.length; i++) {
                if (String(selectMarca.options[i].value).trim() === String(marcaId).trim()) {
                    selectMarca.selectedIndex = i;
                    asignado = true;
                    break;
                }
            }
            if (!asignado) selectMarca.value = String(marcaId);
        } else {
            selectMarca.selectedIndex = 0;
        }
    }

    if (selectModelo && selectMarca) {
        selectModelo.addEventListener('change', actualizarMarcaPorModelo);
        if (selectModelo.value) actualizarMarcaPorModelo();
    }

    // 2. PREVISUALIZACIÓN DE FOTOS EN REGISTRO
    const inputImagenes = document.getElementById('input-imagenes');
    const previewContainer = document.getElementById('preview-imagenes');

    if (inputImagenes && previewContainer) {
        inputImagenes.addEventListener('change', function() {
            previewContainer.innerHTML = ''; 
            if (!this.files || this.files.length === 0) {
                previewContainer.innerHTML = '<span class="text-muted small my-auto ps-2" id="texto-sin-fotos">No hay fotografías seleccionadas aún.</span>';
                return;
            }

            Array.from(this.files).forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const card = document.createElement('div');
                    card.className = 'position-relative border rounded shadow-sm bg-white p-1 text-center';
                    card.style.width = '110px';
                    card.style.display = 'inline-block';
                    card.innerHTML = `
                        <div style="width: 100%; height: 75px; overflow: hidden; border-radius: 4px; background: #eee;">
                            <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <span class="badge bg-dark position-absolute top-0 start-0 m-1" style="font-size: 0.65rem;">#${index + 1}</span>
                        <div class="text-truncate small text-muted mt-1 px-1" style="font-size: 0.7rem;" title="${file.name}">${file.name}</div>
                    `;
                    previewContainer.appendChild(card);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    // 3. PREVISUALIZACIÓN DE NUEVAS FOTOS EN EDITAR
    const inputNuevasFotos = document.getElementById('input-nuevas-fotos');
    const previewNuevasFotos = document.getElementById('preview-nuevas-fotos');

    if (inputNuevasFotos && previewNuevasFotos) {
        inputNuevasFotos.addEventListener('change', function() {
            previewNuevasFotos.innerHTML = '';
            if (!this.files || this.files.length === 0) {
                previewNuevasFotos.style.display = 'none';
                return;
            }
            previewNuevasFotos.style.display = 'flex';
            Array.from(this.files).forEach((file) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const card = document.createElement('div');
                    card.className = 'position-relative border rounded shadow-sm bg-white p-1 text-center';
                    card.style.width = '110px';
                    card.innerHTML = `
                        <div style="width: 100%; height: 75px; overflow: hidden; border-radius: 4px; background: #eee;">
                            <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <span class="badge bg-success position-absolute top-0 start-0 m-1" style="font-size: 0.65rem;">+Nueva</span>
                        <div class="text-truncate small text-muted mt-1 px-1" style="font-size: 0.7rem;" title="${file.name}">${file.name}</div>
                    `;
                    previewNuevasFotos.appendChild(card);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    // =========================================================================
    // 4. MODAL GALERÍA DE FOTOS (TABLA DE VEHÍCULOS)
    // =========================================================================
    const modalGaleria = document.getElementById('modalGaleriaFotos');
    if (modalGaleria) {
        modalGaleria.addEventListener('show.bs.modal', function(event) {
            const triggerEl = event.relatedTarget;
            if (!triggerEl) return;
            const placa = triggerEl.getAttribute('data-placa') || '';
            const vehiculo = triggerEl.getAttribute('data-vehiculo') || '';
            const fotosJson = triggerEl.getAttribute('data-fotos') || '[]';

            let fotos = [];
            try { 
                const parsed = JSON.parse(fotosJson);
                fotos = Array.isArray(parsed) ? parsed : (parsed ? [parsed] : []);
            } catch (e) { 
                fotos = []; 
            }

            fotos = fotos.map(f => (typeof f === 'object' && f !== null ? (f.ruta || f.url || Object.values(f)[0] || '') : f)).filter(Boolean);

            const galTitulo = document.getElementById('galeriaTitulo');
            if (galTitulo) {
                galTitulo.innerHTML = `<i class="bi bi-images me-2"></i>Fotos: <strong>${vehiculo}</strong> <span class="badge bg-light text-dark ms-2">${placa}</span>`;
            }

            const carruselItems = document.getElementById('carrusel-items');
            const miniaturasCont = document.getElementById('galeria-miniaturas');
            const contador = document.getElementById('galeria-contador');

            if (carruselItems) carruselItems.innerHTML = '';
            if (miniaturasCont) miniaturasCont.innerHTML = '';

            if (fotos.length === 0) {
                if (carruselItems) {
                    carruselItems.innerHTML = `
                        <div class="carousel-item active text-center p-5 text-white" style="height: 480px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <i class="bi bi-image text-muted" style="font-size: 4rem;"></i>
                            <p class="mt-3 text-muted">No hay fotografías disponibles para este vehículo.</p>
                        </div>
                    `;
                }
                if (contador) contador.textContent = "0 fotos";
                return;
            }

            // Contador inicial
            if (contador) contador.textContent = `Foto 1 de ${fotos.length} (Total: ${fotos.length})`;

            const carruselEl = document.getElementById('carruselVehiculo');
            if (carruselEl) {
                const prev = carruselEl.querySelector('.carousel-control-prev');
                const next = carruselEl.querySelector('.carousel-control-next');
                if (prev && next) {
                    prev.style.display = fotos.length > 1 ? 'flex' : 'none';
                    next.style.display = fotos.length > 1 ? 'flex' : 'none';
                }
            }

            // Insertar diapositivas y miniaturas
            fotos.forEach((foto, idx) => {
                let ruta = (typeof foto === 'string' && (foto.startsWith('http') || foto.startsWith('/'))) ? foto : `/static/${foto}`;
                
                if (carruselItems) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `carousel-item ${idx === 0 ? 'active' : ''}`;
                    itemDiv.innerHTML = `
                        <div style="width: 100%; height: 500px; background-color: #0d1117; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                            <img src="${ruta}" style="width: 100%; height: 100%; object-fit: contain; display: block;" alt="Foto ${idx + 1}">
                        </div>
                    `;
                    carruselItems.appendChild(itemDiv);
                }

                if (fotos.length > 1 && miniaturasCont) {
                    const mini = document.createElement('img');
                    mini.src = ruta;
                    mini.className = `rounded ${idx === 0 ? 'border border-3 border-primary shadow' : 'opacity-50 border border-secondary'}`;
                    mini.style.width = '64px';
                    mini.style.height = '46px';
                    mini.style.objectFit = 'cover';
                    mini.style.cursor = 'pointer';
                    mini.style.transition = 'all 0.25s ease';

                    mini.onclick = () => {
                        const el = document.getElementById('carruselVehiculo');
                        if (el && window.bootstrap) {
                            bootstrap.Carousel.getOrCreateInstance(el).to(idx);
                        }
                    };
                    miniaturasCont.appendChild(mini);
                }
            });

            // Reiniciar a la primera foto al abrir
            const carruselElInst = document.getElementById('carruselVehiculo');
            if (carruselElInst && window.bootstrap) {
                bootstrap.Carousel.getOrCreateInstance(carruselElInst).to(0);
            }
        });

        // ACTUALIZAR MINIATURA ACTIVA Y CONTADOR AL PASAR DE FOTO CON LAS FLECHAS
        const carruselVehiculoEl = document.getElementById('carruselVehiculo');
        if (carruselVehiculoEl) {
            carruselVehiculoEl.addEventListener('slid.bs.carousel', function(e) {
                const items = carruselVehiculoEl.querySelectorAll('.carousel-item');
                const contador = document.getElementById('galeria-contador');
                if (contador && items.length > 0) {
                    contador.textContent = `Foto ${e.to + 1} de ${items.length} (Total: ${items.length})`;
                }

                // Resaltar la miniatura que corresponde a la foto actual
                const miniaturas = document.querySelectorAll('#galeria-miniaturas img');
                miniaturas.forEach((m, i) => {
                    if (i === e.to) {
                        m.className = 'rounded border border-3 border-primary shadow';
                        m.style.opacity = '1';
                        m.style.transform = 'scale(1.1)';
                    } else {
                        m.className = 'rounded opacity-50 border border-secondary';
                        m.style.opacity = '0.5';
                        m.style.transform = 'scale(1)';
                    }
                });
            });
        }
    }

    // =========================================================================
    // 5. MODAL DETALLES EXPEDIENTE (CHECKLIST CON ✓ VERDES Y ✕ ROJAS)
    // =========================================================================
    const modalDetalles = document.getElementById('modalDetalles');
    if (modalDetalles) {
        modalDetalles.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            if (!button) return;
            const raw = button.getAttribute('data-vehiculo');
            if (!raw) return;
            
            let v = {};
            try { v = JSON.parse(raw); } catch (e) { v = {}; }

            // Datos Generales
            const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setTxt('det-placa', v.placa || '');
            setTxt('det-vehiculo', `${v.nombre_marca || ''} ${v.nombre_modelo || ''}`);
            setTxt('det-anio', v.anio || '');
            setTxt('det-estado', v.estado || '');
            setTxt('det-fecha', v.fecha_ingreso ? String(v.fecha_ingreso).substring(0, 10) : 'No registrada');
            setTxt('det-prov', v.nombre_propietario || '');
            setTxt('det-obs', v.otro_documento || v.descripcion || 'Sin observaciones.');

            // Helper para comprobar si el campo está activo en la BD
            function estaEntregado(val) {
                if (val === 1 || val === '1' || val === true) return true;
                if (typeof val === 'string') {
                    const s = val.trim().toLowerCase();
                    return s === 'si' || s === 'sí' || s === 'true' || s === 'on' || s === 'entregado';
                }
                return false;
            }

            // Los 12 documentos exactos de tu tabla "documentacion"
            const docsBD = [
                { nombre: 'Título de Propiedad', key: 'original_totalPropiedad' },
                { nombre: 'Experticia de Tránsito', key: 'experticia_transito' },
                { nombre: 'Certificado de Origen', key: 'certificado_origen' },
                { nombre: 'Carnet Circulación', key: 'carnet_circulacion' },
                { nombre: 'Reserva de Dominio', key: 'reserva_dominio' },
                { nombre: 'Garantía Vehículo', key: 'garantia_vehiculo' },
                { nombre: 'Certificado de Garantía', key: 'certificado_garantia' },
                { nombre: 'Manual del Vehículo', key: 'manual_vehiculoGarantia' },
                { nombre: 'Finiquito', key: 'finiquito' },
                { nombre: 'Resguardo', key: 'resguardo' },
                { nombre: 'Seguro / Póliza', key: 'seguro' },
                { nombre: 'Factura Compra', key: 'factura_compra' }
            ];

            // Renderizar la lista con ✓ en verde y ✕ en rojo
            const listaDocs = document.getElementById('det-docs');
            if (listaDocs) {
                listaDocs.innerHTML = '';
                docsBD.forEach(doc => {
                    const entregado = estaEntregado(v[doc.key]);
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center py-2 px-1 border-bottom bg-transparent';
                    
                    if (entregado) {
                        li.innerHTML = `
                            <span class="text-dark fw-medium" style="font-size: 0.9rem;">${doc.nombre}</span>
                            <span class="text-success fw-bold" style="font-size: 1.15rem;">✓</span>
                        `;
                    } else {
                        li.innerHTML = `
                            <span class="text-muted" style="font-size: 0.9rem;">${doc.nombre}</span>
                            <span class="text-danger fw-bold" style="font-size: 1.15rem;">✕</span>
                        `;
                    }
                    listaDocs.appendChild(li);
                });
            }

            // Renderizar los 3 accesorios
            const accCont = document.getElementById('det-accesorios');
            if (accCont) {
                accCont.innerHTML = '';
                const accesoriosBD = [
                    { nombre: 'Copia de Llaves', key: 'copia_llaves' },
                    { nombre: 'Caucho Repuesto', key: 'repuesto' },
                    { nombre: 'Triángulo Seg.', key: 'triangulo' }
                ];

                accesoriosBD.forEach(acc => {
                    const tiene = estaEntregado(v[acc.key]);
                    const span = document.createElement('span');
                    span.className = 'badge rounded-pill px-3 py-2 me-1 mb-1';
                    
                    if (tiene) {
                        span.style.backgroundColor = '#0f5132';
                        span.style.color = '#ffffff';
                        span.innerHTML = `<i class="bi bi-check-circle me-1"></i>${acc.nombre}`;
                    } else {
                        span.className += ' bg-light text-muted border';
                        span.innerHTML = `<i class="bi bi-circle me-1 text-black-50"></i>${acc.nombre}`;
                    }
                    accCont.appendChild(span);
                });
            }
        });
    }

    // 6. MENSAJES FLASH
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        if (window.Swal) {
            Swal.fire({
                title: el.dataset.category === 'success' ? '¡Logrado!' : 'Aviso',
                text: el.dataset.message,
                icon: el.dataset.category === 'success' ? 'success' : (el.dataset.category === 'error' ? 'error' : 'info'),
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#0d6efd'
            });
        }
    });

    // =========================================================================
    // 7. MODAL DETALLE DE VENTA CON CARRUSEL DE FOTOS Y NAVEGACIÓN
    // =========================================================================
    const modalDetalleVenta = document.getElementById('modalDetalleVenta');
    if (modalDetalleVenta) {
        modalDetalleVenta.addEventListener('show.bs.modal', function(event) {
            const btn = event.relatedTarget;
            if (!btn) return;

            const marca = btn.getAttribute('data-marca') || 'Vehículo';
            const modelo = btn.getAttribute('data-modelo') || '';
            const anio = btn.getAttribute('data-anio') || '';
            const precio = btn.getAttribute('data-precio') || '0';
            const estado = btn.getAttribute('data-estado') || 'Disponible';
            const descripcion = btn.getAttribute('data-descripcion') || 'No se registraron observaciones adicionales para este vehículo.';
            const fotosJson = btn.getAttribute('data-fotos') || '[]';

            const setText = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };

            setText('modal-v-marca', marca);
            setText('modal-v-modelo', modelo);
            setText('modal-v-anio', anio ? 'Año ' + anio : '');
            setText('modal-v-estado', estado);
            setText('modal-v-desc', descripcion);

            const precioEl = document.getElementById('modal-v-precio');
            if (precioEl) {
                const num = parseFloat(precio) || 0;
                precioEl.textContent = '$' + num.toLocaleString('es-CO', { maximumFractionDigits: 0 });
            }

            let fotos = [];
            try { 
                const parsed = JSON.parse(fotosJson);
                fotos = Array.isArray(parsed) ? parsed : (parsed ? [parsed] : []);
            } catch (e) { 
                fotos = []; 
            }

            fotos = fotos.map(f => (typeof f === 'object' && f !== null ? (f.ruta || f.url || Object.values(f)[0] || '') : f)).filter(Boolean);

            const carruselItems = document.getElementById('modal-carrusel-items');
            const miniaturasCont = document.getElementById('modal-v-miniaturas');
            const contadorTexto = document.getElementById('modal-v-contador-texto');
            const btnPrev = document.getElementById('carrusel-btn-prev');
            const btnNext = document.getElementById('carrusel-btn-next');

            if (carruselItems) carruselItems.innerHTML = '';
            if (miniaturasCont) miniaturasCont.innerHTML = '';

            if (fotos.length === 0) {
                if (carruselItems) {
                    carruselItems.innerHTML = `
                        <div class="carousel-item active h-100 d-flex flex-column align-items-center justify-content-center text-muted p-5" style="min-height: 520px;">
                            <i class="bi bi-image" style="font-size: 4rem; opacity: 0.3;"></i>
                            <p class="mt-3 text-white-50">Sin fotografías registradas</p>
                        </div>
                    `;
                }
                if (contadorTexto) contadorTexto.textContent = '0 fotos';
                if (btnPrev) btnPrev.style.display = 'none';
                if (btnNext) btnNext.style.display = 'none';
                return;
            }

            if (contadorTexto) contadorTexto.textContent = `Foto 1 de ${fotos.length}`;
            if (btnPrev) btnPrev.style.display = fotos.length > 1 ? 'flex' : 'none';
            if (btnNext) btnNext.style.display = fotos.length > 1 ? 'flex' : 'none';

            fotos.forEach((foto, idx) => {
                let ruta = (foto.startsWith('http') || foto.startsWith('/')) ? foto : `/static/${foto}`;

                if (carruselItems) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `carousel-item ${idx === 0 ? 'active' : ''} h-100`;
                    itemDiv.innerHTML = `
                        <div class="w-100 h-100 d-flex align-items-center justify-content-center" style="min-height: 520px; max-height: 580px; background: #0b0f19;">
                            <img src="${ruta}" 
                                 alt="Foto ${idx + 1}" 
                                 class="w-100 h-100" 
                                 style="object-fit: contain; max-height: 520px; display: block;"
                                 onerror="this.src='https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1200';">
                        </div>
                    `;
                    carruselItems.appendChild(itemDiv);
                }

                if (fotos.length > 1 && miniaturasCont) {
                    const mini = document.createElement('img');
                    mini.src = ruta;
                    mini.className = `rounded ${idx === 0 ? 'border border-2 border-primary shadow' : 'opacity-50 border border-secondary'}`;
                    mini.style.width = '64px';
                    mini.style.height = '44px';
                    mini.style.objectFit = 'cover';
                    mini.style.cursor = 'pointer';
                    mini.onclick = () => {
                        const el = document.getElementById('carruselDetalleVenta');
                        if (el && window.bootstrap) {
                            bootstrap.Carousel.getOrCreateInstance(el).to(idx);
                        }
                    };
                    miniaturasCont.appendChild(mini);
                }
            });

            const carruselEl = document.getElementById('carruselDetalleVenta');
            if (carruselEl && window.bootstrap) {
                bootstrap.Carousel.getOrCreateInstance(carruselEl).to(0);
            }
        });

        const carruselEl = document.getElementById('carruselDetalleVenta');
        if (carruselEl) {
            carruselEl.addEventListener('slid.bs.carousel', function(e) {
                const items = carruselEl.querySelectorAll('.carousel-item');
                const contadorTexto = document.getElementById('modal-v-contador-texto');
                if (contadorTexto && items.length > 0) {
                    contadorTexto.textContent = `Foto ${e.to + 1} de ${items.length}`;
                }
                const miniaturas = document.querySelectorAll('#modal-v-miniaturas img');
                miniaturas.forEach((m, i) => {
                    if (i === e.to) {
                        m.className = 'rounded border border-2 border-primary shadow';
                        m.style.opacity = '1';
                    } else {
                        m.className = 'rounded opacity-50 border border-secondary';
                    }
                });
            });
        }
    }

    // =========================================================================
    // 8. VALIDACIONES IDÉNTICAS DE PROPIETARIO, MARCA Y MODELO EN LOS MODALES
    // =========================================================================

    // ---------------------------------------------------------------------
    // A. VALIDACIÓN IDÉNTICA DE PROPIETARIO (Tomada de propietario.js)
    // ---------------------------------------------------------------------
    const modalPropietario = document.getElementById('modalCrearPropietario');
    const formPropietario = document.getElementById('formNuevoPropietarioModal');
    const selectPropietario = document.getElementById('select-propietario');

    const validarInputPropietario = (input) => {
        const valor = input.value.trim();
        const name = input.name;
        let esValido = true;
        let mensajeError = "";

        if (valor === "") {
            if (input.hasAttribute('required')) {
                esValido = false;
                mensajeError = "Este campo es obligatorio.";
            }
        } else {
            if (name === 'cedula') {
                esValido = /^[0-9]{6,12}$/.test(valor); 
                mensajeError = "Cédula inválida (6 a 12 números).";
            } else if (name === 'razon_social') {
                esValido = /^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]{3,50}$/.test(valor);
                mensajeError = "Solo letras (3 a 50 caracteres).";
            } else if (name === 'telefono') {
                esValido = /^[0-9]{10,15}$/.test(valor);
                mensajeError = "Teléfono inválido (10 a 15 números).";
            } else if (name === 'correo') {
                const regexCorreo = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
                if (valor.length > 50) {
                    esValido = false;
                    mensajeError = "El correo es muy largo (Máximo 50).";
                } else if (!regexCorreo.test(valor)) {
                    esValido = false;
                    mensajeError = "Formato inválido (Solo letras, números, . y -).";
                }
            } else if (name === 'direccion') {
                const regexDir = /^[a-zA-Z0-9ñÑáéíóúÁÉÍÓÚ\s.,#/-]+$/;
                if (valor.length < 5 || valor.length > 100) {
                    esValido = false;
                    mensajeError = "Debe tener entre 5 y 100 caracteres.";
                } else if (!regexDir.test(valor)) {
                    esValido = false;
                    mensajeError = "No se permiten símbolos especiales extraños.";
                }
            }
        }

        // Gestión visual con invalid-feedback de Bootstrap
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.style.fontSize = '0.85em';
            input.parentNode.appendChild(feedback);
        }

        if (esValido) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            feedback.style.display = 'none';
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            feedback.innerText = mensajeError;
            feedback.style.display = 'block';
        }
        return esValido;
    };

    if (modalPropietario) {
        modalPropietario.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('input', () => validarInputPropietario(input));
            input.addEventListener('blur', () => validarInputPropietario(input));
        });
    }

    if (formPropietario) {
        formPropietario.addEventListener('submit', async function(e) {
            e.preventDefault();

            let formValido = true;
            const campos = this.querySelectorAll('input[required], textarea[required], select[required]');
            campos.forEach(campo => {
                if (!validarInputPropietario(campo)) formValido = false;
            });

            if (!formValido) {
                return Swal.fire({
                    icon: 'error',
                    title: 'Datos inválidos',
                    text: 'Por favor, revise los campos marcados en rojo.',
                    confirmButtonColor: '#d33'
                });
            }

            Swal.fire({
                title: 'Registrando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(this.action, { method: 'POST', body: new FormData(this) });
                const result = await response.json();

                if (response.ok && (result.status === 'success' || !result.status)) {
                    if (window.bootstrap) {
                        const inst = bootstrap.Modal.getInstance(modalPropietario) || bootstrap.Modal.getOrCreateInstance(modalPropietario);
                        if (inst) inst.hide();
                    }

                    const cedula = document.getElementById('modal_cedula').value.trim();
                    const razonSocial = document.getElementById('modal_razon_social').value.trim();

                    if (selectPropietario) {
                        let existe = false;
                        for (let opt of selectPropietario.options) {
                            if (opt.value === cedula) { opt.selected = true; existe = true; break; }
                        }
                        if (!existe) {
                            const opt = document.createElement('option');
                            opt.value = cedula;
                            opt.textContent = `${razonSocial} (CI: ${cedula})`;
                            opt.selected = true;
                            selectPropietario.appendChild(opt);
                        }
                    }

                    formPropietario.reset();
                    modalPropietario.querySelectorAll('.is-valid, .is-invalid').forEach(el => el.classList.remove('is-valid', 'is-invalid'));

                    Swal.fire({
                        icon: 'success',
                        title: '¡Registrado!',
                        text: result.message || 'Propietario guardado exitosamente',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: result.message });
                }
            } catch (error) {
                Swal.fire({ icon: 'error', title: 'Error de red', text: 'No se pudo comunicar con el servidor.' });
            }
        });
    }

    // ---------------------------------------------------------------------
    // B. VALIDACIÓN IDÉNTICA DE MARCA (Tomada de marca.js)
    // ---------------------------------------------------------------------
    const modalMarca = document.getElementById('modalCrearMarca');
    const formMarca = document.getElementById('formNuevaMarcaModal');
    const inputNombreMarca = document.getElementById('modal_nombre_marca');
    // selectMarca ya fue declarado al inicio de DOMContentLoaded
    const selectMarcaEnModalModelo = document.getElementById('modal_modelo_cod_marca');

    const validarInputMarca = (input) => {
        const valor = input.value;
        const regexLetras = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/;
        const limite = 20;

        const esValido = regexLetras.test(valor) && valor.length <= limite && valor.length >= 2;

        if (valor.length === 0) {
            input.style.color = '';
            input.style.borderColor = '';
            input.classList.remove('is-valid', 'is-invalid');
        } else if (esValido) {
            input.style.color = 'green';
            input.style.borderColor = 'green';
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.style.color = 'red';
            input.style.borderColor = 'red';
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
        return esValido;
    };

    if (inputNombreMarca) {
        inputNombreMarca.addEventListener('input', () => validarInputMarca(inputNombreMarca));
    }

    if (formMarca) {
        formMarca.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (!validarInputMarca(inputNombreMarca)) {
                return Swal.fire({
                    title: 'Error',
                    text: 'El nombre debe tener entre 2 y 20 caracteres, sin números ni símbolos.',
                    icon: 'error',
                    confirmButtonColor: '#3085d6'
                });
            }

            Swal.fire({
                title: 'Registrando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(this.action, { method: 'POST', body: new FormData(this) });
                const data = await response.json();

                if (data.status === 'success') {
                    if (window.bootstrap) {
                        const inst = bootstrap.Modal.getInstance(modalMarca) || bootstrap.Modal.getOrCreateInstance(modalMarca);
                        if (inst) inst.hide();
                    }

                    const idMarca = data.cod_marca || inputNombreMarca.value.trim();
                    const textoMarca = data.nombre_marca || inputNombreMarca.value.trim();

                    if (selectMarca) {
                        let existe = false;
                        for (let opt of selectMarca.options) {
                            if (opt.text.toLowerCase() === textoMarca.toLowerCase()) { opt.selected = true; existe = true; break; }
                        }
                        if (!existe) {
                            const opt = document.createElement('option');
                            opt.value = idMarca;
                            opt.textContent = textoMarca;
                            opt.selected = true;
                            selectMarca.appendChild(opt);
                        }
                    }

                    if (selectMarcaEnModalModelo) {
                        const optMod = document.createElement('option');
                        optMod.value = idMarca;
                        optMod.textContent = textoMarca;
                        optMod.selected = true;
                        selectMarcaEnModalModelo.appendChild(optMod);
                    }

                    formMarca.reset();
                    inputNombreMarca.style.color = '';
                    inputNombreMarca.style.borderColor = '';
                    inputNombreMarca.classList.remove('is-valid', 'is-invalid');

                    Swal.fire({
                        title: '¡Registrado!',
                        text: data.message,
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({ title: 'Error', text: data.message, icon: 'error', confirmButtonColor: '#3085d6' });
                }
            } catch (error) {
                Swal.fire({ title: 'Error', text: 'No se pudo conectar con el servidor.', icon: 'error', confirmButtonColor: '#3085d6' });
            }
        });
    }

    // ---------------------------------------------------------------------
    // C. VALIDACIÓN IDÉNTICA DE MODELO (Tomada de modelo.js)
    // ---------------------------------------------------------------------
    const modalModelo = document.getElementById('modalCrearModelo');
    const formModelo = document.getElementById('formNuevoModeloModal');
    const inputNombreModelo = document.getElementById('modal_modelo_nombre');
    const selectMarcaEnModelo = document.getElementById('modal_modelo_cod_marca');
    // selectModelo ya fue declarado al inicio de DOMContentLoaded

    const validarInputModelo = (input) => {
        const valor = input.value;
        const regexSoloLetras = /^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]*$/;
        const limite = 20;
        
        const esValido = valor.length >= 2 && valor.length <= limite && regexSoloLetras.test(valor);

        if (valor.length === 0) {
            input.style.color = '';
            input.style.borderColor = '';
            input.classList.remove('is-valid', 'is-invalid');
        } else if (esValido) {
            input.style.color = 'green';
            input.style.borderColor = 'green';
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.style.color = 'red';
            input.style.borderColor = 'red';
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
        return esValido;
    };

    if (inputNombreModelo) {
        inputNombreModelo.addEventListener('input', () => validarInputModelo(inputNombreModelo));
    }

    if (formModelo) {
        formModelo.addEventListener('submit', async function(e) {
            e.preventDefault();

            const codMarca = selectMarcaEnModelo.value;

            if (!validarInputModelo(inputNombreModelo)) {
                return Swal.fire({
                    title: 'Error',
                    text: 'El nombre debe tener entre 2 y 20 caracteres y no contener números ni símbolos.',
                    icon: 'error',
                    confirmButtonColor: '#3085d6'
                });
            }
            if (codMarca === "" || codMarca === "0") {
                return Swal.fire({
                    title: 'Error',
                    text: 'Debe seleccionar una marca válida.',
                    icon: 'error',
                    confirmButtonColor: '#3085d6'
                });
            }

            Swal.fire({
                title: 'Registrando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(this.action, { method: 'POST', body: new FormData(this) });
                const result = await response.json();

                if (result.status === 'success') {
                    if (window.bootstrap) {
                        const inst = bootstrap.Modal.getInstance(modalModelo) || bootstrap.Modal.getOrCreateInstance(modalModelo);
                        if (inst) inst.hide();
                    }

                    const idModelo = result.cod_modelo || inputNombreModelo.value.trim();
                    const textoModelo = result.nombre_modelo || inputNombreModelo.value.trim();
                    const idMarcaAsignada = result.cod_marca || codMarca;
                    const nombreMarcaFinal = selectMarcaEnModelo.options[selectMarcaEnModelo.selectedIndex]?.text || '';

                    if (selectModelo) {
                        let existe = false;
                        for (let opt of selectModelo.options) {
                            if (opt.value == idModelo) { opt.selected = true; existe = true; break; }
                        }
                        if (!existe) {
                            const opt = document.createElement('option');
                            opt.value = idModelo;
                            opt.setAttribute('data-marca', idMarcaAsignada);
                            opt.textContent = `${textoModelo} (${nombreMarcaFinal})`;
                            opt.selected = true;
                            selectModelo.appendChild(opt);
                        }
                        seleccionarMarca(selectModelo);
                    }

                    formModelo.reset();
                    inputNombreModelo.style.color = '';
                    inputNombreModelo.style.borderColor = '';
                    inputNombreModelo.classList.remove('is-valid', 'is-invalid');

                    Swal.fire({
                        title: '¡Excelente!',
                        text: result.message,
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({ title: 'Error', text: result.message, icon: 'error', confirmButtonColor: '#3085d6' });
                }
            } catch (error) {
                Swal.fire({ title: 'Error', text: 'No se pudo conectar con el servidor.', icon: 'error', confirmButtonColor: '#3085d6' });
            }
        });
    }

});