from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import random

asistente_bp = Blueprint('asistente', __name__, url_prefix='/asistente')


@asistente_bp.route('/chat')
def chat():
    """Vista principal del chat con el asistente."""
    nombre = session.get('usuario_nombre', 'amigo')
    return render_template('asistente/chat.html', nombre=nombre)


@asistente_bp.route('/mensaje', methods=['POST'])
def mensaje():
    """
    Endpoint que recibe el mensaje del usuario y devuelve la respuesta del 'asistente'.
    Aquí luego puedes integrar un LLM real (OpenAI, Gemini, etc.).
    """
    data = request.get_json(silent=True) or {}
    texto = (data.get('mensaje') or '').strip().lower()

    if not texto:
        return jsonify({"respuesta": "No te escuché bien, ¿puedes repetirlo?"})

    # --- Lógica fake pero útil: responder según palabras clave ---
    respuesta = generar_respuesta(texto)

    return jsonify({
        "respuesta": respuesta,
        "timestamp": datetime.now().strftime('%H:%M')
    })


def generar_respuesta(texto):
    """Genera una respuesta basada en palabras clave (fácil de reemplazar por IA real)."""
    if any(p in texto for p in ['hola', 'buenas', 'saludos', 'hey']):
        return "¡Hola! 👋 Soy AutoBot, tu asistente de AutoMall. Puedo ayudarte a encontrar un vehículo, agendar una cita o darte información sobre financiamiento. ¿Qué necesitas?"

    if any(p in texto for p in ['precio', 'costo', 'cuánto', 'vale']):
        return "Los precios varían según el modelo y año. Puedes ver el catálogo completo en la sección <b>Catálogo</b>. ¿Hay algún modelo en específico que te interese?"

    if any(p in texto for p in ['camioneta', 'suv', 'familiar']):
        return "Para uso familiar te recomendaría una SUV como la <b>Toyota Fortuner</b> o la <b>Changan CS75</b>. Ambas tienen buen espacio, seguridad y rendimiento. ¿Quieres ver opciones disponibles?"

    if any(p in texto for p in ['sedan', 'sedán', 'corolla', 'auto pequeño']):
        return "Los sedanes son ideales para ciudad. Te sugiero el <b>Toyota Corolla</b> o el <b>Honda Civic</b>: bajo consumo y mantenimiento económico. ¿Te muestro los que tenemos en stock?"

    if any(p in texto for p in ['crédito', 'credito', 'financiamiento', 'financiar', 'cuotas']):
        return "Manejamos financiamiento hasta en <b>48 cuotas</b> con inicial desde el 20%. ¿Quieres que te pase con un asesor para revisar tu caso?"

    if any(p in texto for p in ['cita', 'agendar', 'visita', 'probar']):
        return "¡Perfecto! Puedes agendar una cita directamente desde el menú <b>Citas → Agendar</b>. ¿Prefieres prueba de manejo o solo ver el vehículo?"

    if any(p in texto for p in ['garantía', 'garantia']):
        return "Todos nuestros vehículos incluyen <b>garantía de 1 año</b> en motor y caja, y 6 meses en sistemas eléctricos. ¿Necesitas saber algo más?"

    if any(p in texto for p in ['ubicación', 'ubicacion', 'dónde', 'donde', 'dirección']):
        return "Estamos ubicados en la <b>Avenida Principal, Torre AutoMall, Piso 1</b>. Atendemos de lunes a sábado, de 8am a 6pm. ¿Quieres que te envíe la ubicación?"

    if any(p in texto for p in ['gracias', 'ok', 'perfecto', 'bueno']):
        return "¡Con gusto! Si necesitas algo más, aquí estoy. 🚗"

    if any(p in texto for p in ['adiós', 'adios', 'chao', 'bye']):
        return "¡Hasta luego! Vuelve cuando quieras. 👋"

    # Respuesta genérica si no reconoce nada
    opciones = [
        "Interesante. ¿Podrías darme más detalles para ayudarte mejor?",
        "No estoy seguro de eso. ¿Te gustaría que te ayude con información sobre modelos, precios o citas?",
        "Cuéntame un poco más, ¿buscas comprar, financiar o agendar una cita?",
    ]
    return random.choice(opciones)