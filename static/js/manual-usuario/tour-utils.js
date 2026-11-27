/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo: tour-utils.js
 * Utilidades para detección de elementos en el DOM, cálculo geométrico del spotlight,
 * posicionamiento inteligente del tooltip con prevención de desbordamiento y accesibilidad.
 */

export class TourUtils {
    /**
     * Resuelve un selector o función para obtener el elemento objetivo
     * @param {string|Function|HTMLElement} target
     * @returns {HTMLElement|null}
     */
    static getElement(target) {
        if (!target) return null;
        if (typeof target === 'function') {
            try { return target(); } catch (e) { return null; }
        }
        if (typeof target === 'string') {
            return document.querySelector(target);
        }
        if (target instanceof HTMLElement) {
            return target;
        }
        return null;
    }

    /**
     * Comprueba si un elemento está verdaderamente visible en el DOM
     * @param {HTMLElement} el
     * @returns {boolean}
     */
    static isElementVisible(el) {
        if (!el || !el.isConnected) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return false;
        }
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    /**
     * Desplaza suavemente la ventana para centrar el elemento objetivo,
     * respetando el margen del navbar pegajoso superior (sticky navbar)
     * @param {HTMLElement} el
     * @returns {Promise<void>}
     */
    static async scrollIntoViewIfNeeded(el) {
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const navbarHeight = 75; // Espacio de seguridad para el navbar sticky de AutoMall
        const viewportHeight = window.innerHeight;
        const viewportWidth = window.innerWidth;

        const isFullyVisible = (
            rect.top >= navbarHeight + 20 &&
            rect.bottom <= viewportHeight - 20 &&
            rect.left >= 10 &&
            rect.right <= viewportWidth - 10
        );

        if (!isFullyVisible) {
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            el.scrollIntoView({
                behavior: prefersReducedMotion ? 'auto' : 'smooth',
                block: 'center',
                inline: 'nearest'
            });

            // Pequeña espera para que concluya la animación de scroll
            await new Promise(resolve => setTimeout(resolve, prefersReducedMotion ? 50 : 320));
        }
    }

    /**
     * Calcula la posición (top, left) óptima del tooltip y clase de flecha direccional
     * detectando colisiones con los bordes de la pantalla
     * @param {HTMLElement} targetEl Elemento enfocado
     * @param {HTMLElement} tooltipEl Tooltip flotante
     * @param {string} preferredPlacement 'bottom' | 'top' | 'right' | 'left' | 'center'
     * @returns {{ top: number, left: number, placementClass: string }}
     */
    static computeTooltipPosition(targetEl, tooltipEl, preferredPlacement = 'bottom') {
        const spacing = 16;
        const navHeight = 70;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        const tWidth = tooltipEl.offsetWidth || 380;
        const tHeight = tooltipEl.offsetHeight || 220;

        // Si no hay elemento o es placement 'center', centramos en pantalla
        if (!targetEl || preferredPlacement === 'center') {
            return {
                top: Math.max(navHeight + 20, (vh - tHeight) / 2),
                left: Math.max(16, (vw - tWidth) / 2),
                placementClass: 'placement-center'
            };
        }

        const rect = targetEl.getBoundingClientRect();
        let placement = preferredPlacement;

        // Detección de colisión vertical y alternancia inteligente (flip)
        if (placement === 'bottom' && (rect.bottom + spacing + tHeight > vh - 10)) {
            if (rect.top - spacing - tHeight > navHeight) {
                placement = 'top';
            }
        } else if (placement === 'top' && (rect.top - spacing - tHeight < navHeight)) {
            if (rect.bottom + spacing + tHeight < vh - 10) {
                placement = 'bottom';
            }
        }

        // Detección de colisión horizontal
        if (placement === 'right' && (rect.right + spacing + tWidth > vw - 12)) {
            if (rect.left - spacing - tWidth > 12) {
                placement = 'left';
            } else {
                placement = 'bottom';
            }
        } else if (placement === 'left' && (rect.left - spacing - tWidth < 12)) {
            if (rect.right + spacing + tWidth < vw - 12) {
                placement = 'right';
            } else {
                placement = 'bottom';
            }
        }

        let top = 0;
        let left = 0;

        switch (placement) {
            case 'top':
                top = rect.top - tHeight - spacing;
                left = rect.left + (rect.width - tWidth) / 2;
                break;
            case 'right':
                top = rect.top + (rect.height - tHeight) / 2;
                left = rect.right + spacing;
                break;
            case 'left':
                top = rect.top + (rect.height - tHeight) / 2;
                left = rect.left - tWidth - spacing;
                break;
            case 'bottom':
            default:
                placement = 'bottom';
                top = rect.bottom + spacing;
                left = rect.left + (rect.width - tWidth) / 2;
                break;
        }

        // Restricción dentro de los márgenes seguros de pantalla (clamp)
        left = Math.max(12, Math.min(left, vw - tWidth - 12));
        top = Math.max(navHeight + 10, Math.min(top, vh - tHeight - 12));

        return {
            top,
            left,
            placementClass: `placement-${placement}`
        };
    }

    /**
     * Obtiene el rectángulo geométrico con relleno suave (padding) para el Spotlight
     * @param {HTMLElement} el
     * @returns {{ top: number, left: number, width: number, height: number }}
     */
    static getSpotlightRect(el) {
        if (!el) {
            // Posición neutra en centro de pantalla si no hay elemento
            return {
                top: window.innerHeight / 2,
                left: window.innerWidth / 2,
                width: 0,
                height: 0
            };
        }
        const rect = el.getBoundingClientRect();
        const padding = 6;
        return {
            top: Math.max(0, rect.top - padding),
            left: Math.max(0, rect.left - padding),
            width: rect.width + (padding * 2),
            height: rect.height + (padding * 2)
        };
    }
}

