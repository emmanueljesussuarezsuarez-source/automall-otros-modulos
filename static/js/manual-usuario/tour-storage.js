/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo: tour-storage.js
 * Persistencia segura en localStorage respetando privacidad y seguridad:
 * - NO almacena nombres, contraseñas, cédulas, tokens ni datos sensibles de negocio.
 * - Almacena únicamente el progreso técnico (módulo, subtour, paso y estado).
 */

const STORAGE_KEY_PREFIX = 'automall_tour_v1_';

export class TourStorage {
    /**
     * Clave técnica base para el almacenamiento de tours
     */
    static getStorageKey() {
        return `${STORAGE_KEY_PREFIX}progress`;
    }

    /**
     * Construye la clave compuesta módulo:subtour
     */
    static buildKey(moduleKey, subtourId = 'general') {
        return `${moduleKey}:${subtourId || 'general'}`;
    }

    /**
     * Carga el diccionario completo de progresos de tours
     * @returns {Object}
     */
    static getAllProgress() {
        try {
            const raw = localStorage.getItem(this.getStorageKey());
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            console.warn('[AutoMall TourStorage] Error al leer localStorage:', e);
            return {};
        }
    }

    /**
     * Obtiene el progreso específico de un módulo y subtour
     * @param {string} moduleKey Clave del módulo (ej: 'taller')
     * @param {string} subtourId Identificador del subtour ('general', 'registro', 'edicion')
     * @returns {{ status: 'not_started'|'in_progress'|'completed', lastStep: number, totalSteps: number, updatedAt: number }}
     */
    static getProgress(moduleKey, subtourId = 'general') {
        if (!moduleKey) return { status: 'not_started', lastStep: 0, totalSteps: 0, updatedAt: 0 };
        const all = this.getAllProgress();
        const key = this.buildKey(moduleKey, subtourId);
        return all[key] || { status: 'not_started', lastStep: 0, totalSteps: 0, updatedAt: 0 };
    }

    /**
     * Guarda el progreso de una visita guiada
     * @param {string} moduleKey Clave del módulo
     * @param {string} subtourId Identificador del subtour
     * @param {number} currentStep Índice del paso actual
     * @param {number} totalSteps Total de pasos
     * @param {boolean} isCompleted Si la visita fue finalizada exitosamente
     */
    static saveProgress(moduleKey, subtourId = 'general', currentStep = 1, totalSteps = 1, isCompleted = false) {
        if (!moduleKey) return;
        try {
            const all = this.getAllProgress();
            const key = this.buildKey(moduleKey, subtourId);
            all[key] = {
                status: isCompleted ? 'completed' : 'in_progress',
                lastStep: currentStep,
                totalSteps: totalSteps,
                updatedAt: Date.now()
            };
            localStorage.setItem(this.getStorageKey(), JSON.stringify(all));
        } catch (e) {
            console.warn('[AutoMall TourStorage] Error al guardar progreso:', e);
        }
    }

    /**
     * Reinicia el progreso de un módulo o subtour
     * @param {string} moduleKey
     * @param {string} subtourId
     */
    static resetProgress(moduleKey, subtourId = 'general') {
        if (!moduleKey) return;
        try {
            const all = this.getAllProgress();
            const key = this.buildKey(moduleKey, subtourId);
            if (all[key]) {
                delete all[key];
                localStorage.setItem(this.getStorageKey(), JSON.stringify(all));
            }
        } catch (e) {
            console.warn('[AutoMall TourStorage] Error al reiniciar progreso:', e);
        }
    }

    /**
     * Gestión de solicitudes de visita entre páginas (transitoria en sessionStorage)
     * Permite que al seleccionar un recorrido desde el modal, al navegar a la página
     * de destino se inicie automáticamente el tour solicitado, pero NUNCA en navegación habitual.
     */
    static setPendingTour(moduleKey, subtourId = 'general', stepIndex = 0, targetUrl = '') {
        try {
            const payload = {
                moduleKey,
                subtourId: subtourId || 'general',
                stepIndex,
                targetUrl: targetUrl || '',
                timestamp: Date.now()
            };
            sessionStorage.setItem('automall_pending_tour', JSON.stringify(payload));
        } catch (e) {
            console.warn('[AutoMall TourStorage] Error al establecer tour pendiente:', e);
        }
    }

    /**
     * Obtiene y consume (elimina) la solicitud transitoria de tour pendiente
     * @returns {{ moduleKey: string, subtourId: string, stepIndex: number, targetUrl?: string }|null}
     */
    static consumePendingTour() {
        try {
            const raw = sessionStorage.getItem('automall_pending_tour');
            if (!raw) return null;
            sessionStorage.removeItem('automall_pending_tour');
            const data = JSON.parse(raw);
            // Máximo 1 minuto de vigencia para evitar activaciones desfasadas
            if (Date.now() - data.timestamp > 60000) {
                return null;
            }
            return data;
        } catch (e) {
            sessionStorage.removeItem('automall_pending_tour');
            return null;
        }
    }
}
