from flask import Blueprint, jsonify, session, request
from utils.notificaciones_manager import NotificacionManager

notificaciones_bp = Blueprint('notificaciones', __name__, url_prefix='/api/notificaciones')

@notificaciones_bp.route('', methods=['GET'])
def obtener_notificaciones():
    """Retorna la lista de notificaciones no leídas para la sesión activa."""
    if 'usuario_nombre' not in session and 'cedula_usuario' not in session:
        return jsonify({'total': 0, 'notificaciones': []})

    id_usuario = session.get('cedula_usuario') or session.get('id_usuario') or session.get('usuario_nombre')
    cod_rol = session.get('cod_rol')
    id_cliente = session.get('cedula_usuario')

    filtro = request.args.get('filtro', 'no_leidas')

    no_leidas = NotificacionManager.obtener_no_leidas_usuario(
        id_usuario=id_usuario,
        cod_rol=cod_rol,
        id_cliente=id_cliente
    )

    if filtro == 'todas':
        lista = NotificacionManager.obtener_historial_usuario(
            id_usuario=id_usuario,
            cod_rol=cod_rol,
            id_cliente=id_cliente
        )
    else:
        lista = no_leidas

    return jsonify({
        'total': len(no_leidas),
        'notificaciones': lista
    })

@notificaciones_bp.route('/marcar-leida/<string:id_notificacion>', methods=['POST'])
def marcar_leida(id_notificacion):
    """Marca una notificación específica como leída para la sesión actual."""
    id_usuario = session.get('cedula_usuario') or session.get('id_usuario') or session.get('usuario_nombre')
    if not id_usuario:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    exito = NotificacionManager.marcar_como_leida(id_notificacion, id_usuario)
    return jsonify({'success': exito})

@notificaciones_bp.route('/marcar-todas-leidas', methods=['POST'])
def marcar_todas_leidas():
    """Marca todas las notificaciones pendientes como leídas."""
    id_usuario = session.get('cedula_usuario') or session.get('id_usuario') or session.get('usuario_nombre')
    cod_rol = session.get('cod_rol')
    id_cliente = session.get('cedula_usuario')

    if not id_usuario:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    exito = NotificacionManager.marcar_todas_leidas(id_usuario, cod_rol, id_cliente)
    return jsonify({'success': exito})
