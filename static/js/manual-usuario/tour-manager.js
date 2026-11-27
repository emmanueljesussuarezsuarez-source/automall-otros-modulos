/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo: tour-manager.js
 * Motor central de visitas guiadas interactivas.
 * Gestiona el ciclo de vida, subtours, spotlight dinámico, atajos de teclado y limpieza de eventos.
 */

import { TourUtils } from './tour-utils.js';
import { TourStorage } from './tour-storage.js';
import { TourSteps } from './tour-steps.js';

export class TourManager {
    constructor() {
        this.containerEl = document.getElementById('tourOverlayContainer');
        this.spotlightEl = document.getElementById('tourSpotlight');
        this.tooltipEl = document.getElementById('tourTooltip');
        this.arrowEl = document.getElementById('tourTooltipArrow');
        this.moduleBadgeEl = document.getElementById('tourModuleBadge');
        this.stepBadgeEl = document.getElementById('tourStepBadge');
        this.titleEl = document.getElementById('tourTooltipTitle');
        this.contentEl = document.getElementById('tourTooltipContent');
        this.progressBarEl = document.getElementById('tourProgressBar');

        this.btnPrev = document.getElementById('btnTourPrev');
        this.btnNext = document.getElementById('btnTourNext');
        this.btnFinish = document.getElementById('btnTourFinish');
        this.btnSkip = document.getElementById('btnTourSkip');
        this.btnRestart = document.getElementById('btnTourRestart');
        this.btnClose = document.getElementById('btnTourClose');

        this.activeModuleKey = null;
        this.activeSubtourId = 'general';
        this.currentStepIndex = 0;
        this.steps = [];
        this.isRunning = false;
        this.previousActiveElement = null;

        // Bound handlers para remover listeners sin fugas de memoria
        this.handleKeyDown = this.onKeyDown.bind(this);
        this.handleResize = this.onResize.bind(this);

        this.initEventListeners();
    }

    /**
     * Vincula los botones de control del tooltip
     */
    initEventListeners() {
        if (!this.containerEl) return;

        if (this.btnNext) {
            this.btnNext.addEventListener('click', () => this.nextStep());
        }
        if (this.btnPrev) {
            this.btnPrev.addEventListener('click', () => this.prevStep());
        }
        if (this.btnFinish) {
            this.btnFinish.addEventListener('click', () => this.finishTour());
        }
        if (this.btnSkip) {
            this.btnSkip.addEventListener('click', () => this.closeTour(true));
        }
        if (this.btnRestart) {
            this.btnRestart.addEventListener('click', () => this.restartTour());
        }
        if (this.btnClose) {
            this.btnClose.addEventListener('click', () => this.closeTour(true));
        }
    }

    /**
     * Inicia una visita guiada para un módulo y subtour determinado
     * @param {string} moduleKey Clave del módulo (ej: 'taller')
     * @param {string} subtourId Identificador del subtour ('general', 'registro', 'edicion')
     * @param {number} startStep Índice del paso inicial (0 por defecto)
     */
    async startTour(moduleKey, subtourId = 'general', startStep = 0) {
        if (!this.containerEl || !this.spotlightEl || !this.tooltipEl) {
            console.error('[AutoMall TourManager] Los elementos de overlay no existen en el DOM.');
            return false;
        }

        if (!TourSteps.isAvailable(moduleKey, subtourId)) {
            console.warn(`[AutoMall TourManager] La visita para '${moduleKey}:${subtourId}' no está disponible.`);
            return false;
        }

        // Obtener pasos filtrados por condiciones activas de permisos
        const availableSteps = TourSteps.getSteps(moduleKey, subtourId);
        if (!availableSteps || availableSteps.length === 0) {
            console.warn(`[AutoMall TourManager] No hay pasos aplicables para '${moduleKey}:${subtourId}'.`);
            return false;
        }

        this.activeModuleKey = moduleKey;
        this.activeSubtourId = subtourId || 'general';
        this.steps = availableSteps;
        this.currentStepIndex = Math.max(0, Math.min(startStep, this.steps.length - 1));
        this.isRunning = true;
        this.previousActiveElement = document.activeElement;

        // Configurar badge con el título específico del subtour
        const modDef = TourSteps.getModule(moduleKey);
        const subTitle = TourSteps.getSubtourTitle(moduleKey, subtourId);
        if (this.moduleBadgeEl) {
            this.moduleBadgeEl.innerHTML = `<i class="bi ${modDef?.icono || 'bi-compass'}"></i> ${subTitle}`;
        }

        // Mostrar contenedor
        this.containerEl.style.display = 'block';
        this.containerEl.setAttribute('aria-hidden', 'false');

        // Escuchadores de eventos globales
        window.addEventListener('keydown', this.handleKeyDown, true);
        window.addEventListener('resize', this.handleResize);

        // Renderizar paso solicitado
        await this.renderStep(this.currentStepIndex);
        return true;
    }

    /**
     * Renderiza el paso actual, posiciona el spotlight y el tooltip
     * @param {number} index
     */
    async renderStep(index) {
        if (!this.isRunning || index < 0 || index >= this.steps.length) return;

        this.currentStepIndex = index;
        const step = this.steps[index];
        const totalSteps = this.steps.length;

        // Ejecutar acción opcional previa
        if (typeof step.action === 'function') {
            try {
                await step.action();
            } catch (e) {
                console.warn('[AutoMall TourManager] Error ejecutando acción previa del paso:', e);
            }
        }

        // Localizar elemento objetivo (con reintento breve para esperar animaciones de modales o DataTables)
        let targetEl = TourUtils.getElement(step.target);
        if (!targetEl && step.target) {
            for (let retry = 0; retry < 6; retry++) {
                await new Promise(r => setTimeout(r, 60));
                targetEl = TourUtils.getElement(step.target);
                if (targetEl && TourUtils.isElementVisible(targetEl)) break;
            }
        }

        // Scroll suave hacia el elemento objetivo
        if (targetEl) {
            await TourUtils.scrollIntoViewIfNeeded(targetEl);
        }

        // Posicionar el Spotlight en torno al elemento
        const sRect = TourUtils.getSpotlightRect(targetEl);
        this.spotlightEl.style.top = `${sRect.top}px`;
        this.spotlightEl.style.left = `${sRect.left}px`;
        this.spotlightEl.style.width = `${sRect.width}px`;
        this.spotlightEl.style.height = `${sRect.height}px`;

        // Actualizar textos e indicadores
        if (this.titleEl) this.titleEl.textContent = step.title;
        if (this.contentEl) this.contentEl.textContent = step.content;
        if (this.stepBadgeEl) this.stepBadgeEl.textContent = `Paso ${index + 1} de ${totalSteps}`;

        // Barra de progreso
        if (this.progressBarEl) {
            const percent = Math.round(((index + 1) / totalSteps) * 100);
            this.progressBarEl.style.width = `${percent}%`;
        }

        // Botones de acción
        const isFirst = (index === 0);
        const isLast = (index === totalSteps - 1);

        if (this.btnPrev) {
            this.btnPrev.disabled = isFirst;
        }

        if (this.btnRestart) {
            this.btnRestart.style.display = isFirst ? 'none' : 'inline-flex';
        }

        if (this.btnNext && this.btnFinish) {
            if (isLast) {
                this.btnNext.style.display = 'none';
                this.btnFinish.style.display = 'inline-flex';
                this.btnFinish.textContent = step.finishLabel || 'Finalizar';
                this.btnFinish.focus();
            } else {
                this.btnNext.style.display = 'inline-flex';
                this.btnFinish.style.display = 'none';
                this.btnNext.focus();
            }
        }

        // Posicionar Tooltip Flotante
        const pos = TourUtils.computeTooltipPosition(targetEl, this.tooltipEl, step.placement || 'bottom');
        this.tooltipEl.style.top = `${pos.top}px`;
        this.tooltipEl.style.left = `${pos.left}px`;

        // Limpiar clases de colocación anteriores y aplicar la nueva
        this.tooltipEl.className = 'tour-tooltip tour-visible ' + pos.placementClass;

        // Guardar progreso técnico parcial en localStorage
        TourStorage.saveProgress(this.activeModuleKey, this.activeSubtourId, index + 1, totalSteps, false);
    }

    /**
     * Avanza al siguiente paso
     */
    async nextStep() {
        if (!this.isRunning) return;
        const currentStep = this.steps[this.currentStepIndex];

        if (currentStep && typeof currentStep.onComplete === 'function') {
            try { await currentStep.onComplete(); } catch (e) { }
        }

        if (this.currentStepIndex < this.steps.length - 1) {
            await this.renderStep(this.currentStepIndex + 1);
        } else {
            this.finishTour();
        }
    }

    /**
     * Retrocede al paso anterior
     */
    async prevStep() {
        if (!this.isRunning || this.currentStepIndex <= 0) return;
        await this.renderStep(this.currentStepIndex - 1);
    }

    /**
     * Reinicia el recorrido desde el primer paso
     */
    async restartTour() {
        if (!this.isRunning) return;
        await this.renderStep(0);
    }

    /**
     * Cierra la visita guiada y restaura el estado
     * @param {boolean} saveProgress
     */
    closeTour(saveProgress = true) {
        if (!this.isRunning) return;

        if (saveProgress && this.activeModuleKey) {
            TourStorage.saveProgress(
                this.activeModuleKey,
                this.activeSubtourId,
                this.currentStepIndex + 1,
                this.steps.length,
                false
            );
        }

        this.cleanup();
    }

    /**
     * Finaliza exitosamente el recorrido y marca el subtour como completado
     */
    finishTour() {
        if (!this.isRunning) return;

        if (this.activeModuleKey) {
            TourStorage.saveProgress(
                this.activeModuleKey,
                this.activeSubtourId,
                this.steps.length,
                this.steps.length,
                true // Estado: completado
            );
        }

        const subTitle = TourSteps.getSubtourTitle(this.activeModuleKey, this.activeSubtourId);
        this.cleanup();

        // Notificación de felicitaciones
        if (window.AutoMallCentroAyuda && window.AutoMallCentroAyuda.modal) {
            window.AutoMallCentroAyuda.modal.mostrarAviso(`¡Completaste con éxito la guía "${subTitle}"!`);
        }
    }

    /**
     * Manejador de teclado accesible (Escape, Flechas y Enter)
     * @param {KeyboardEvent} e
     */
    onKeyDown(e) {
        if (!this.isRunning) return;

        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            this.closeTour(true);
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            this.nextStep();
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            this.prevStep();
        }
    }

    /**
     * Reposiciona el spotlight y tooltip al redimensionar la ventana
     */
    onResize() {
        if (!this.isRunning) return;
        clearTimeout(this._resizeTimeout);
        this._resizeTimeout = setTimeout(() => {
            if (this.isRunning) {
                this.renderStep(this.currentStepIndex);
            }
        }, 120);
    }

    /**
     * Limpieza completa de eventos, cierre seguro de modales y restauración de foco
     */
    cleanup() {
        this.isRunning = false;

        // Cierre preventivo de cualquier modal que haya sido abierto durante el tour
        if (typeof bootstrap !== 'undefined') {
            document.querySelectorAll('.modal.show').forEach(m => {
                try {
                    bootstrap.Modal.getInstance(m)?.hide();
                } catch (e) { }
            });
        }

        if (this.containerEl) {
            this.containerEl.style.display = 'none';
            this.containerEl.setAttribute('aria-hidden', 'true');
        }

        if (this.tooltipEl) {
            this.tooltipEl.classList.remove('tour-visible');
        }

        window.removeEventListener('keydown', this.handleKeyDown, true);
        window.removeEventListener('resize', this.handleResize);

        // Restaurar foco al elemento activo previo
        if (this.previousActiveElement && typeof this.previousActiveElement.focus === 'function') {
            try { this.previousActiveElement.focus(); } catch (e) { }
        }
    }
}
