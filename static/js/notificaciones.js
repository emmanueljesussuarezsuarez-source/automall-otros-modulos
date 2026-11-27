document.addEventListener('DOMContentLoaded', function () {
    const badgeEl = document.getElementById('notif-badge');
    const dropdownListEl = document.getElementById('notif-dropdown-list');

    if (!badgeEl || !dropdownListEl) return;

    let filtroActual = 'no_leidas'; // 'no_leidas' o 'todas'

    function cargarNotificaciones() {
        fetch('/api/notificaciones?filtro=' + filtroActual)
            .then(res => res.json())
            .then(data => {
                const totalNoLeidas = data.total || 0;
                const notifs = data.notificaciones || [];

                // Actualizar Badge y Animación de la Campana
                const bellIcon = document.querySelector('#navNotificaciones i');
                if (totalNoLeidas > 0) {
                    badgeEl.textContent = totalNoLeidas > 99 ? '99+' : totalNoLeidas;
                    badgeEl.classList.remove('d-none');
                    if (bellIcon) {
                        bellIcon.classList.add('bell-ring-once');
                    }
                } else {
                    badgeEl.textContent = '0';
                    badgeEl.classList.add('d-none');
                    if (bellIcon) {
                        bellIcon.classList.remove('bell-ring-once', 'bell-vibrate');
                    }
                }

                // Renderizar Lista Dropdown con pestañas (Pendientes / Historial)
                let html = `
                    <div class="dropdown-header py-2 px-3 bg-light border-bottom">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="fw-bold text-dark"><i class="bi bi-bell me-1"></i>Notificaciones</span>
                            ${totalNoLeidas > 0 ? `<button id="btn-marcar-todas" class="btn btn-sm btn-link p-0 text-decoration-none" style="font-size: 0.78rem;">Marcar leídas</button>` : ''}
                        </div>
                        <div class="btn-group btn-group-sm w-100" role="group">
                            <button type="button" id="btn-filtro-pendientes" class="btn ${filtroActual === 'no_leidas' ? 'btn-primary' : 'btn-outline-secondary'} btn-sm py-0" style="font-size: 0.75rem;">
                                Pendientes (${totalNoLeidas})
                            </button>
                            <button type="button" id="btn-filtro-historial" class="btn ${filtroActual === 'todas' ? 'btn-primary' : 'btn-outline-secondary'} btn-sm py-0" style="font-size: 0.75rem;">
                                Historial
                            </button>
                        </div>
                    </div>
                    <div class="notif-scroll-container" style="max-height: 320px; overflow-y: auto;">
                `;

                if (notifs.length === 0) {
                    html += `
                        <div class="text-center text-muted py-4">
                            <i class="bi bi-check-circle fs-3 text-secondary d-block mb-1"></i>
                            <span style="font-size: 0.85rem;">${filtroActual === 'no_leidas' ? 'Sin notificaciones pendientes' : 'Sin notificaciones en el historial'}</span>
                        </div>
                    `;
                } else {
                    notifs.forEach(n => {
                        const url = n.url_destino && n.url_destino !== '#' ? n.url_destino : 'javascript:void(0);';
                        const leidaClass = n.leida ? 'bg-light text-muted opacity-75' : '';
                        const checkIcon = n.leida ? '<i class="bi bi-check2-all text-muted ms-1" title="Leída"></i>' : '<span class="badge bg-primary rounded-circle p-1 me-1" style="font-size: 0.4rem;"> </span>';

                        html += `
                            <a href="${url}" class="dropdown-item notif-item py-2 px-3 border-bottom text-wrap ${leidaClass}" data-id="${n.id}" data-url="${url}">
                                <div class="d-flex w-100 justify-content-between align-items-center mb-1">
                                    <div class="d-flex align-items-center">
                                        ${checkIcon}
                                        <strong class="${n.leida ? 'text-secondary' : 'text-primary'}" style="font-size: 0.88rem;">${escapeHtml(n.titulo)}</strong>
                                    </div>
                                    <small class="text-muted" style="font-size: 0.72rem;">${escapeHtml(n.fecha_creacion.split(' ')[1] || '')}</small>
                                </div>
                                <p class="mb-1 text-secondary" style="font-size: 0.82rem; line-height: 1.25;">${escapeHtml(n.mensaje)}</p>
                            </a>
                        `;
                    });
                }

                html += `</div>`;
                dropdownListEl.innerHTML = html;

                // Event Listeners: Filtros Pendientes vs Historial
                const btnPendientes = document.getElementById('btn-filtro-pendientes');
                const btnHistorial = document.getElementById('btn-filtro-historial');

                if (btnPendientes) {
                    btnPendientes.addEventListener('click', function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        filtroActual = 'no_leidas';
                        cargarNotificaciones();
                    });
                }

                if (btnHistorial) {
                    btnHistorial.addEventListener('click', function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        filtroActual = 'todas';
                        cargarNotificaciones();
                    });
                }

                // Event Listener: Marcar todas
                const btnTodas = document.getElementById('btn-marcar-todas');
                if (btnTodas) {
                    btnTodas.addEventListener('click', function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        fetch('/api/notificaciones/marcar-todas-leidas', { method: 'POST' })
                            .then(() => cargarNotificaciones());
                    });
                }

                // Event Listener: Clic en notificación individual
                document.querySelectorAll('.notif-item').forEach(item => {
                    item.addEventListener('click', function (e) {
                        const id = this.getAttribute('data-id');
                        const targetUrl = this.getAttribute('data-url');

                        if (id) {
                            fetch(`/api/notificaciones/marcar-leida/${id}`, { method: 'POST' })
                                .then(() => {
                                    if (targetUrl && targetUrl !== 'javascript:void(0);') {
                                        window.location.href = targetUrl;
                                    } else {
                                        cargarNotificaciones();
                                    }
                                })
                                .catch(() => {
                                    if (targetUrl && targetUrl !== 'javascript:void(0);') {
                                        window.location.href = targetUrl;
                                    }
                                });
                        }
                    });
                });
            })
            .catch(err => console.error("Error al cargar notificaciones:", err));
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Cargar al inicio y refrescar cada 30 segundos
    cargarNotificaciones();
    setInterval(cargarNotificaciones, 30000);
});
