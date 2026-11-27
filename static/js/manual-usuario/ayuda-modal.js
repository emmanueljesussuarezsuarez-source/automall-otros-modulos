/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo: ayuda-modal.js
 * Controla apertura, cierre, búsqueda en tiempo real, categorías y lanzamiento de visitas guiadas y subtours.
 */

import { TourSteps } from './tour-steps.js';
import { TourStorage } from './tour-storage.js';

export class AyudaModal {
    constructor(tourManager = null) {
        this.tourManager = tourManager;
        this.modalEl = document.getElementById('modalCentroAyuda');
        this.inputBuscar = document.getElementById('inputBuscarModulo');
        this.btnLimpiar = document.getElementById('btnLimpiarBusqueda');
        this.btnRestablecer = document.getElementById('btnRestablecerFiltros');
        this.gridEl = document.getElementById('gridModulosAyuda');
        this.emptyEl = document.getElementById('centroAyudaSinResultados');
        this.toastEl = document.getElementById('centroAyudaToast');
        this.toastTextoEl = document.getElementById('centroAyudaToastTexto');
        this.btnAbrir = document.getElementById('btnAbrirCentroAyuda');

        this.categoriaActual = 'todas';
        this.terminoBusqueda = '';
        this.toastTimeout = null;

        if (this.modalEl) {
            this.init();
        }
    }

    init() {
        this.actualizarEstadosTarjetas();
        this.actualizarContadoresCategorias();
        this.registrarEventos();
    }

    /**
     * Refresca los badges de progreso y disponibilidad de cada tarjeta según TourStorage y TourSteps
     */
    actualizarEstadosTarjetas() {
        if (!this.gridEl) return;
        const cards = this.gridEl.querySelectorAll('.centro-ayuda-card');

        cards.forEach(card => {
            const moduleKey = card.getAttribute('data-modulo');
            const metaBadge = card.querySelector('.centro-ayuda-card-meta .centro-ayuda-badge');
            const btnTour = card.querySelector('.centro-ayuda-btn-tour');
            if (!metaBadge || !moduleKey) return;

            const isAvailable = TourSteps.isAvailable(moduleKey, 'general');

            // Actualizar botones de subtour si existen
            const subtourBtns = card.querySelectorAll('.centro-ayuda-subtour-btn');
            let subtoursCompletados = 0;

            subtourBtns.forEach(sBtn => {
                const sId = sBtn.getAttribute('data-subtour') || 'general';
                const sProg = TourStorage.getProgress(moduleKey, sId);

                sBtn.classList.remove('completed', 'in-progress');
                if (sProg.status === 'completed') {
                    sBtn.classList.add('completed');
                    subtoursCompletados++;
                } else if (sProg.status === 'in_progress') {
                    sBtn.classList.add('in-progress');
                }
            });

            if (isAvailable) {
                if (subtourBtns.length > 0) {
                    if (subtoursCompletados === subtourBtns.length) {
                        metaBadge.className = 'centro-ayuda-badge';
                        metaBadge.style.cssText = 'background:#dcfce7; color:#15803d; border:1px solid #bbf7d0;';
                        metaBadge.innerHTML = '<i class="bi bi-check-circle-fill"></i> Todo completado';
                    } else if (subtoursCompletados > 0) {
                        metaBadge.className = 'centro-ayuda-badge badge-prioritario';
                        metaBadge.style.cssText = '';
                        metaBadge.innerHTML = `<i class="bi bi-pie-chart-fill"></i> ${subtoursCompletados}/${subtourBtns.length} completados`;
                    } else {
                        metaBadge.className = 'centro-ayuda-badge badge-prioritario';
                        metaBadge.style.cssText = '';
                        metaBadge.innerHTML = `<i class="bi bi-stars"></i> ${subtourBtns.length} Recorridos`;
                    }
                    if (btnTour) btnTour.innerHTML = '<i class="bi bi-play-circle"></i> Iniciar visita';
                } else {
                    const progress = TourStorage.getProgress(moduleKey, 'general');
                    if (progress.status === 'completed') {
                        metaBadge.className = 'centro-ayuda-badge';
                        metaBadge.style.cssText = 'background:#dcfce7; color:#15803d; border:1px solid #bbf7d0;';
                        metaBadge.innerHTML = '<i class="bi bi-check-circle-fill"></i> Completada';
                    } else if (progress.status === 'in_progress') {
                        metaBadge.className = 'centro-ayuda-badge badge-prioritario';
                        metaBadge.style.cssText = '';
                        metaBadge.innerHTML = `<i class="bi bi-clock-history"></i> En curso (${progress.lastStep}/${progress.totalSteps})`;
                    } else {
                        metaBadge.className = 'centro-ayuda-badge badge-prioritario';
                        metaBadge.style.cssText = '';
                        metaBadge.innerHTML = '<i class="bi bi-stars"></i> Visita disponible';
                    }
                }
            } else {
                metaBadge.className = 'centro-ayuda-badge badge-fase';
                metaBadge.style.cssText = '';
                metaBadge.innerHTML = '<i class="bi bi-hourglass-split"></i> Próximamente';
                if (btnTour) {
                    btnTour.style.opacity = '0.85';
                    btnTour.title = 'Guía en preparación para la siguiente fase';
                }
            }
        });
    }

    /**
     * Registra listeners de interacción
     */
    registrarEventos() {
        // 1. Eventos del Modal Bootstrap
        this.modalEl.addEventListener('show.bs.modal', () => {
            this.actualizarEstadosTarjetas();
        });

        this.modalEl.addEventListener('shown.bs.modal', () => {
            if (this.inputBuscar) this.inputBuscar.focus();
        });

        this.modalEl.addEventListener('hidden.bs.modal', () => {
            if (this.btnAbrir) this.btnAbrir.focus();
        });

        // 2. Búsqueda en tiempo real
        if (this.inputBuscar) {
            this.inputBuscar.addEventListener('input', (e) => {
                this.terminoBusqueda = e.target.value.trim().toLowerCase();
                if (this.btnLimpiar) {
                    this.btnLimpiar.style.display = this.terminoBusqueda ? 'block' : 'none';
                }
                this.filtrarModulos();
            });

            this.inputBuscar.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.inputBuscar.value) {
                    e.stopPropagation();
                    this.limpiarBusqueda();
                }
            });
        }

        // 3. Botón limpiar búsqueda
        if (this.btnLimpiar) {
            this.btnLimpiar.addEventListener('click', () => this.limpiarBusqueda());
        }

        // 4. Botón restablecer filtros en estado vacío
        if (this.btnRestablecer) {
            this.btnRestablecer.addEventListener('click', () => this.restablecerTodo());
        }

        // 5. Píldoras de Categoría
        const catButtons = this.modalEl.querySelectorAll('.centro-ayuda-cat-btn');
        catButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                catButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.categoriaActual = btn.getAttribute('data-categoria') || 'todas';
                this.filtrarModulos();
            });
        });

        // 6. Botones de "Iniciar visita" principales de cada tarjeta
        const tourButtons = this.modalEl.querySelectorAll('.centro-ayuda-btn-tour');
        tourButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const moduleKey = btn.getAttribute('data-modulo');
                const subtourId = btn.getAttribute('data-subtour') || 'general';
                const nombreModulo = btn.getAttribute('data-nombre') || 'este módulo';
                const urlModulo = btn.getAttribute('data-url') || '';

                this.gestionarInicioVisita(moduleKey, subtourId, nombreModulo, urlModulo);
            });
        });

        // 7. Botones directos de subtour
        const subtourButtons = this.modalEl.querySelectorAll('.centro-ayuda-subtour-btn');
        subtourButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const moduleKey = btn.getAttribute('data-modulo');
                const subtourId = btn.getAttribute('data-subtour') || 'general';
                const nombreModulo = btn.getAttribute('data-nombre') || 'este módulo';
                const urlModulo = btn.getAttribute('data-url') || '';

                this.gestionarInicioVisita(moduleKey, subtourId, nombreModulo, urlModulo);
            });
        });
    }

    /**
     * Lógica de inicio de visita con soporte para subtours:
     */
    gestionarInicioVisita(moduleKey, subtourId = 'general', nombreModulo = '', urlModulo = '') {
        const isAvailable = TourSteps.isAvailable(moduleKey, subtourId);

        if (!isAvailable) {
            this.mostrarAviso(
                `La visita guiada interactiva para "${nombreModulo}" está en preparación (Fase 3). Puedes usar "Ir" para explorar el módulo.`
            );
            return;
        }

        // Cerrar modal de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            const modalInstance = bootstrap.Modal.getInstance(this.modalEl);
            if (modalInstance) {
                modalInstance.hide();
            }
        }

        // Comprobar si ya estamos en la página del módulo
        const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
        const targetPath = urlModulo.replace(/\/$/, '') || '/';

        const progress = TourStorage.getProgress(moduleKey, subtourId);
        const startStep = (progress.status === 'in_progress' && progress.lastStep > 0) ? progress.lastStep - 1 : 0;

        if (currentPath === targetPath && this.tourManager) {
            // Iniciar inmediatamente en la vista actual
            setTimeout(() => {
                this.tourManager.startTour(moduleKey, subtourId, startStep);
            }, 350);
        } else {
            // Guardar flag transitorio y navegar
            TourStorage.setPendingTour(moduleKey, subtourId, startStep, urlModulo);
            window.location.href = urlModulo;
        }
    }

    /**
     * Calcula dinámicamente los módulos visibles para el usuario por categoría
     */
    actualizarContadoresCategorias() {
        if (!this.gridEl) return;
        const cards = Array.from(this.gridEl.querySelectorAll('.centro-ayuda-card'));

        const contadores = {
            todas: cards.length,
            acondicionamiento: 0,
            operaciones: 0,
            ventas: 0,
            usuarios: 0,
            configuracion: 0,
            general: 0
        };

        cards.forEach(card => {
            const cat = card.getAttribute('data-categoria');
            if (contadores[cat] !== undefined) {
                contadores[cat]++;
            }
        });

        const setCounter = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        setCounter('countTodas', contadores.todas);
        setCounter('countAcondicionamiento', contadores.acondicionamiento);
        setCounter('countOperaciones', contadores.operaciones);
        setCounter('countVentas', contadores.ventas);
        setCounter('countUsuarios', contadores.usuarios);
        setCounter('countConfiguracion', contadores.configuracion);
        setCounter('countGeneral', contadores.general);
    }

    filtrarModulos() {
        if (!this.gridEl) return;
        const cards = Array.from(this.gridEl.querySelectorAll('.centro-ayuda-card'));
        let visibles = 0;

        cards.forEach(card => {
            const cat = card.getAttribute('data-categoria');
            const titulo = (card.querySelector('.centro-ayuda-card-title')?.textContent || '').toLowerCase();
            const desc = (card.querySelector('.centro-ayuda-card-desc')?.textContent || '').toLowerCase();
            const catText = (card.querySelector('.centro-ayuda-card-category')?.textContent || '').toLowerCase();

            const coincideCategoria = (this.categoriaActual === 'todas' || this.categoriaActual === cat);
            const coincideTexto = !this.terminoBusqueda || 
                                  titulo.includes(this.terminoBusqueda) || 
                                  desc.includes(this.terminoBusqueda) ||
                                  catText.includes(this.terminoBusqueda);

            if (coincideCategoria && coincideTexto) {
                card.style.display = 'flex';
                visibles++;
            } else {
                card.style.display = 'none';
            }
        });

        if (this.emptyEl) {
            if (visibles === 0) {
                this.emptyEl.classList.add('visible');
            } else {
                this.emptyEl.classList.remove('visible');
            }
        }
    }

    limpiarBusqueda() {
        if (this.inputBuscar) {
            this.inputBuscar.value = '';
            this.terminoBusqueda = '';
            if (this.btnLimpiar) this.btnLimpiar.style.display = 'none';
            this.inputBuscar.focus();
            this.filtrarModulos();
        }
    }

    restablecerTodo() {
        this.limpiarBusqueda();
        this.categoriaActual = 'todas';
        const catButtons = this.modalEl.querySelectorAll('.centro-ayuda-cat-btn');
        catButtons.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-categoria') === 'todas');
        });
        this.filtrarModulos();
    }

    mostrarAviso(mensaje) {
        if (!this.toastEl || !this.toastTextoEl) {
            alert(mensaje);
            return;
        }

        if (this.toastTimeout) {
            clearTimeout(this.toastTimeout);
        }

        this.toastTextoEl.textContent = mensaje;
        this.toastEl.classList.add('show');

        this.toastTimeout = setTimeout(() => {
            this.toastEl.classList.remove('show');
        }, 3800);
    }
}
