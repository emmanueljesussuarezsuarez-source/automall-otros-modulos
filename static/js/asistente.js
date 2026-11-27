(function () {
    'use strict';

    const chatMessages  = document.getElementById('chatMessages');
    const userInput     = document.getElementById('userInput');
    const sendBtn       = document.getElementById('sendBtn');
    const quickPrompts  = document.getElementById('quickPrompts');

    // Configuración inyectada desde el template
    const config        = window.ASISTENTE_CONFIG || {};
    const nombreUsuario = config.nombreUsuario || 'usuario';
    const urlMensaje    = config.urlMensaje || '/asistente/mensaje';

    // ============================================
    // 1. Render de mensajes
    // ============================================
    function agregarMensaje(texto, tipo = 'bot', hora = null) {
        const horaFinal = hora || new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

        const row = document.createElement('div');
        row.className = `msg-row ${tipo}`;
        row.innerHTML = `
            <div class="msg-avatar">
                <i class="bi bi-${tipo === 'bot' ? 'robot' : 'person-fill'}"></i>
            </div>
            <div class="msg-bubble">
                ${texto}
                <span class="msg-time">${horaFinal}</span>
            </div>
        `;
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function mostrarEscribiendo() {
        const row = document.createElement('div');
        row.className = 'msg-row bot typing';
        row.id = 'typingIndicator';
        row.innerHTML = `
            <div class="msg-avatar"><i class="bi bi-robot"></i></div>
            <div class="msg-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function quitarEscribiendo() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    // ============================================
    // 2. Enviar mensaje
    // ============================================
    async function enviarMensaje(textoForzado = null) {
        const texto = (textoForzado || userInput.value).trim();
        if (!texto) return;

        // Mensaje del usuario
        agregarMensaje(escapeHtml(texto), 'user');
        userInput.value = '';
        userInput.style.height = 'auto';

        // Ocultar sugerencias tras el primer mensaje
        if (quickPrompts) quickPrompts.style.display = 'none';

        // Bloquear input mientras responde
        userInput.disabled = true;
        sendBtn.disabled = true;

        mostrarEscribiendo();

        try {
            const res = await fetch(urlMensaje, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: texto })
            });
            const data = await res.json();

            // Simular "pensando..." para que se vea natural
            setTimeout(() => {
                quitarEscribiendo();
                agregarMensaje(data.respuesta || 'No obtuve respuesta.', 'bot', data.timestamp);
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }, 600);

        } catch (err) {
            console.error(err);
            quitarEscribiendo();
            agregarMensaje('Lo siento, tuve un problema de conexión. Intenta de nuevo.', 'bot');
            userInput.disabled = false;
            sendBtn.disabled = false;
        }
    }

    // ============================================
    // 3. Helpers
    // ============================================
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function enviarSugerencia(texto) {
        enviarMensaje(texto);
    }

    function limpiarChat() {
        chatMessages.innerHTML = '';
        if (quickPrompts) quickPrompts.style.display = 'flex';
        iniciarChat();
    }

    // ============================================
    // 4. Inicialización
    // ============================================
    function iniciarChat() {
        agregarMensaje(
            `¡Hola, ${escapeHtml(nombreUsuario)}! 👋 Soy <b>AutoBot</b>, tu asistente de AutoMall. ` +
            `Puedo ayudarte a encontrar un vehículo, agendar una cita o resolver dudas sobre financiamiento. ` +
            `¿En qué te ayudo hoy?`,
            'bot'
        );
    }

    // Autoresize textarea + Enter para enviar
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            enviarMensaje();
        }
    });

    // Arrancar
    document.addEventListener('DOMContentLoaded', () => {
        iniciarChat();
        userInput.focus();
    });

    // ============================================
    // 5. Exponer funciones usadas en atributos onclick del HTML
    // ============================================
    window.enviarMensaje    = enviarMensaje;
    window.enviarSugerencia = enviarSugerencia;
    window.limpiarChat      = limpiarChat;
})();