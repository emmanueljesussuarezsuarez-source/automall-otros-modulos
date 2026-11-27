/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo principal: manual-usuario.js (ES6 Module)
 * Orquestador principal del sistema de ayuda y motor de visitas guiadas.
 */

import { TourManager } from './tour-manager.js';
import { AyudaModal } from './ayuda-modal.js';
import { TourStorage } from './tour-storage.js';
import { TourSteps } from './tour-steps.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Instanciar motor de visitas guiadas
    const tourManager = new TourManager();

    // 2. Instanciar modal del Centro de Ayuda comunicándolo con el motor de tours
    const ayudaModal = new AyudaModal(tourManager);

    // 3. Exponer en el objeto global para acceso y depuración controlada
    window.AutoMallManual = {
        tourManager,
        ayudaModal,
        storage: TourStorage,
        steps: TourSteps
    };

    // 4. Comprobar si el usuario solicitó explícitamente iniciar una visita desde otra página
    const pending = TourStorage.consumePendingTour();
    if (pending && pending.moduleKey && TourSteps.isAvailable(pending.moduleKey, pending.subtourId)) {
        const modDef = TourSteps.getModule(pending.moduleKey);
        const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
        const subtourDef = modDef?.subtours ? modDef.subtours[pending.subtourId] : null;
        const expectedPath = ((subtourDef && subtourDef.ruta) || modDef?.ruta || '').replace(/\/$/, '') || '/';
        const targetPath = (pending.targetUrl || '').replace(/\/$/, '') || '';

        // Se inicia si la ruta actual coincide exactamente o es el prefijo del módulo o URL destino
        const matchesExpected = currentPath === expectedPath || (expectedPath !== '/' && currentPath.startsWith(expectedPath));
        const matchesTarget = targetPath && (currentPath === targetPath || (targetPath !== '/' && currentPath.startsWith(targetPath)));

        if (matchesExpected || matchesTarget) {
            setTimeout(() => {
                tourManager.startTour(pending.moduleKey, pending.subtourId || 'general', pending.stepIndex || 0);
            }, 450); // Margen para asegurar renderizado completo de tablas o componentes
        }
    }
});
