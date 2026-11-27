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

    // 4. MODAL GALERÍA DE FOTOS (TABLA)
    const modalGaleria = document.getElementById('modalGaleriaFotos');
    if (modalGaleria) {
        modalGaleria.addEventListener('show.bs.modal', function(event) {
            const triggerEl = event.relatedTarget;
            if (!triggerEl) return;
            const placa = triggerEl.getAttribute('data-placa') || '';
            const vehiculo = triggerEl.getAttribute('data-vehiculo') || '';
            const fotosJson = triggerEl.getAttribute('data-fotos') || '[]';

            let fotos = [];
            try { fotos = JSON.parse(fotosJson); } catch (e) { fotos = []; }

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

            if (contador) contador.textContent = `Total: ${fotos.length} fotografía(s)`;

            const carruselEl = document.getElementById('carruselVehiculo');
            if (carruselEl) {
                const prev = carruselEl.querySelector('.carousel-control-prev');
                const next = carruselEl.querySelector('.carousel-control-next');
                if (prev && next) {
                    prev.style.display = fotos.length > 1 ? 'flex' : 'none';
                    next.style.display = fotos.length > 1 ? 'flex' : 'none';
                }
            }

            fotos.forEach((foto, idx) => {
                let ruta = foto.startsWith('http') || foto.startsWith('/') ? foto : `/static/${foto}`;
                if (carruselItems) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `carousel-item ${idx === 0 ? 'active' : ''}`;
                    itemDiv.innerHTML = `
                        <div style="width: 100%; height: 500px; background-color: #0d1117; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                            <img src="${ruta}" style="width: 100%; height: 100%; object-fit: cover; display: block;" alt="Foto ${idx + 1}">
                        </div>
                    `;
                    carruselItems.appendChild(itemDiv);
                }

                if (fotos.length > 1 && miniaturasCont) {
                    const mini = document.createElement('img');
                    mini.src = ruta;
                    mini.className = `rounded ${idx === 0 ? 'border border-2 border-primary shadow-sm' : 'opacity-50 border border-secondary'}`;
                    mini.style.width = '64px';
                    mini.style.height = '46px';
                    mini.style.objectFit = 'cover';
                    mini.style.cursor = 'pointer';
                    mini.onclick = () => {
                        bootstrap.Carousel.getOrCreateInstance(document.getElementById('carruselVehiculo')).to(idx);
                    };
                    miniaturasCont.appendChild(mini);
                }
            });
        });
    }

    // 5. MODAL DETALLES EXPEDIENTE
    const modalDetalles = document.getElementById('modalDetalles');
    if (modalDetalles) {
        modalDetalles.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            if (!button) return;
            const raw = button.getAttribute('data-vehiculo');
            if (!raw) return;
            const v = JSON.parse(raw);

            const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setTxt('det-placa', v.placa || '');
            setTxt('det-vehiculo', `${v.nombre_marca || ''} ${v.nombre_modelo || ''}`);
            setTxt('det-anio', v.anio || '');
            setTxt('det-estado', v.estado || '');
            setTxt('det-fecha', v.fecha_ingreso ? String(v.fecha_ingreso).substring(0, 10) : 'No registrada');
            setTxt('det-prov', v.nombre_propietario || '');
            setTxt('det-obs', v.otro_documento || v.descripcion || 'Sin observaciones.');
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
    // 7. MODAL DETALLE DE VENTA CON CARRUSEL DE FOTOS Y DESCRIPCIÓN
    // =========================================================================
    const modalDetalleVenta = document.getElementById('modalDetalleVenta');
    if (modalDetalleVenta) {
        modalDetalleVenta.addEventListener('show.bs.modal', function(event) {
            const btn = event.relatedTarget;
            if (!btn) return;

            // Extraer datos usando los atributos data directos
            const marca = btn.getAttribute('data-marca') || 'Vehículo';
            const modelo = btn.getAttribute('data-modelo') || '';
            const anio = btn.getAttribute('data-anio') || '';
            const precio = btn.getAttribute('data-precio') || '0';
            const estado = btn.getAttribute('data-estado') || 'Disponible';
            const descripcion = btn.getAttribute('data-descripcion') || 'No se registraron observaciones adicionales para este vehículo.';
            const placa = btn.getAttribute('data-placa') || '';
            const km = btn.getAttribute('data-kilometraje') || '';
            const transmision = btn.getAttribute('data-transmision') || '';
            const combustible = btn.getAttribute('data-combustible') || '';
            const fotosRaw = btn.getAttribute('data-fotos') || '[]';

            // Rellenar Textos
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
                precioEl.textContent = '$' + num.toLocaleString('es-ES', { maximumFractionDigits: 0 });
            }

            // Especificaciones
            const specsEl = document.getElementById('modal-v-specs');
            if (specsEl) {
                let html = '';
                if (placa) html += `<div class="col-6"><span class="badge bg-light text-dark border">Placa: ${placa}</span></div>`;
                if (km) html += `<div class="col-6"><span class="badge bg-light text-dark border"><i class="bi bi-speedometer2 me-1"></i>${km} km</span></div>`;
                if (transmision) html += `<div class="col-6"><span class="badge bg-light text-dark border">${transmision}</span></div>`;
                if (combustible) html += `<div class="col-6"><span class="badge bg-light text-dark border">${combustible}</span></div>`;
                specsEl.innerHTML = html;
            }

            // Carrusel de Fotos
            const carruselItems = document.getElementById('modal-carrusel-items');
            const miniaturasCont = document.getElementById('modal-v-miniaturas');
            const contadorTexto = document.getElementById('modal-v-contador-texto');
            const btnPrev = document.getElementById('carrusel-btn-prev');
            const btnNext = document.getElementById('carrusel-btn-next');

            if (carruselItems) carruselItems.innerHTML = '';
            if (miniaturasCont) miniaturasCont.innerHTML = '';

            let fotos = [];
            try {
                const parsed = JSON.parse(fotosRaw);
                if (Array.isArray(parsed)) {
                    fotos = parsed.filter(f => f && typeof f === 'string');
                } else if (typeof parsed === 'string') {
                    fotos = [parsed];
                }
            } catch (e) {
                if (fotosRaw && fotosRaw !== '[]') fotos = [fotosRaw];
            }

            if (fotos.length === 0) {
                if (carruselItems) {
                    carruselItems.innerHTML = `
                        <div class="carousel-item active h-100 d-flex flex-column align-items-center justify-content-center text-muted p-5" style="min-height: 440px;">
                            <i class="bi bi-image" style="font-size: 4rem; opacity: 0.4;"></i>
                            <p class="mt-3 text-white-50">Sin fotografías registradas</p>
                        </div>
                    `;
                }
                if (contadorTexto) contadorTexto.textContent = '0 fotos';
                if (btnPrev) btnPrev.style.display = 'none';
                if (btnNext) btnNext.style.display = 'none';
                if (miniaturasCont) miniaturasCont.style.display = 'none';
                return;
            }

            if (contadorTexto) contadorTexto.textContent = `Foto 1 de ${fotos.length}`;
            if (btnPrev) btnPrev.style.display = fotos.length > 1 ? 'flex' : 'none';
            if (btnNext) btnNext.style.display = fotos.length > 1 ? 'flex' : 'none';
            if (miniaturasCont) miniaturasCont.style.display = fotos.length > 1 ? 'flex' : 'none';

            fotos.forEach((foto, idx) => {
                let ruta = foto.startsWith('http') || foto.startsWith('/') ? foto : `/static/${foto}`;

                if (carruselItems) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = `carousel-item ${idx === 0 ? 'active' : ''} h-100`;
                    itemDiv.innerHTML = `
                        <div class="w-100 h-100 d-flex align-items-center justify-content-center overflow-hidden" style="min-height: 440px; max-height: 580px; background: #0b0f19;">
                            <img src="${ruta}" 
                                 alt="Foto ${idx + 1}" 
                                 class="w-100 h-100" 
                                 style="object-fit: cover; display: block;"
                                 onerror="this.src='https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1200';">
                        </div>
                    `;
                    carruselItems.appendChild(itemDiv);
                }

                if (fotos.length > 1 && miniaturasCont) {
                    const mini = document.createElement('img');
                    mini.src = ruta;
                    mini.className = `rounded ${idx === 0 ? 'border border-2 border-primary shadow' : 'opacity-50 border border-secondary'}`;
                    mini.style.width = '62px';
                    mini.style.height = '42px';
                    mini.style.objectFit = 'cover';
                    mini.style.cursor = 'pointer';
                    mini.style.transition = 'all 0.2s ease';

                    mini.onclick = function() {
                        const carruselEl = document.getElementById('carruselDetalleVenta');
                        if (carruselEl && window.bootstrap) {
                            bootstrap.Carousel.getOrCreateInstance(carruselEl).to(idx);
                        }
                    };
                    miniaturasCont.appendChild(mini);
                }
            });

            // Sincronizar contador y miniaturas al pasar fotos
            const carruselEl = document.getElementById('carruselDetalleVenta');
            if (carruselEl) {
                carruselEl.addEventListener('slid.bs.carousel', function(e) {
                    if (contadorTexto) {
                        contadorTexto.textContent = `Foto ${e.to + 1} de ${fotos.length}`;
                    }
                    if (miniaturasCont) {
                        const minis = miniaturasCont.querySelectorAll('img');
                        minis.forEach((m, i) => {
                            if (i === e.to) {
                                m.className = 'rounded border border-2 border-primary shadow';
                                m.style.opacity = '1';
                            } else {
                                m.className = 'rounded opacity-50 border border-secondary';
                            }
                        });
                    }
                });
            }
        });
    }
});