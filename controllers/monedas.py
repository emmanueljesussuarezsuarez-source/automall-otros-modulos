from flask import Blueprint, render_template, request, jsonify, session

from models.monedas import Moneda
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager


moneda_bp = Blueprint('moneda_crud', __name__)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@moneda_bp.route('/monedas/gestion', methods=['GET'])
@requiere_permiso('Monedas', 'p_leer')
def gestion_monedas():

    monedas = Moneda.obtener_todos()
    monedas_digitales = Moneda.obtener_todas_digitales()

    return render_template(
        'monedas/gestion.html',
        monedas=monedas,
        monedas_digitales=monedas_digitales
    )


# ============================================================
# MONEDA
# ============================================================

@moneda_bp.route('/monedas/crear', methods=['POST'])
@requiere_permiso('Monedas', 'p_crear')
def crear_moneda():
    try:
        id_usuario = session.get('cedula_usuario')

        nombre = request.form.get('nombre_moneda', '').strip()
        simbolo = request.form.get('simbolo', '').strip()
        estado = request.form.get('estado', 'Activo')

        Moneda.guardar(
            nombre,
            simbolo,
            estado,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Nueva Moneda",
            mensaje=f"Se ha registrado la moneda '{nombre}' en el sistema.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda registrada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@moneda_bp.route('/monedas/editar/<int:id>', methods=['POST'])
@requiere_permiso('Monedas', 'p_actualizar')
def editar_moneda(id):
    try:
        id_usuario = session.get('cedula_usuario')

        nombre = request.form.get('nombre_moneda', '').strip()
        simbolo = request.form.get('simbolo', '').strip()
        estado = request.form.get('estado', 'Activo')

        Moneda.actualizar(
            id,
            nombre,
            simbolo,
            estado,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Moneda Actualizada",
            mensaje=f"Se han actualizado los datos de la moneda '{nombre}'.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda actualizada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@moneda_bp.route('/monedas/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Monedas', 'p_eliminar')
def eliminar_moneda(id):
    try:
        id_usuario = session.get('cedula_usuario')

        Moneda.eliminar(
            id,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Moneda Desactivada",
            mensaje=f"La moneda con ID #{id} ha sido marcada como Inactiva.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda desactivada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


# ============================================================
# MONEDA DIGITAL
# ============================================================

@moneda_bp.route('/monedas-digitales/crear', methods=['POST'])
@requiere_permiso('Monedas', 'p_crear')
def crear_moneda_digital():
    try:
        id_usuario = session.get('cedula_usuario')

        nombre = request.form.get('nombre_digital', '').strip()
        simbolo = request.form.get('simbolo_digital', '').strip()

       
        estado = int(request.form.get('estado_digital', 1))

        Moneda.guardar_digital(
            nombre,
            simbolo,
            estado,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Nueva Moneda Digital",
            mensaje=f"Se ha registrado la moneda digital '{nombre}'.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda digital registrada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@moneda_bp.route('/monedas-digitales/editar/<int:id>', methods=['POST'])
@requiere_permiso('Monedas', 'p_actualizar')
def editar_moneda_digital(id):
    try:
        id_usuario = session.get('cedula_usuario')

        nombre = request.form.get('nombre_digital', '').strip()
        simbolo = request.form.get('simbolo_digital', '').strip()
        estado = int(request.form.get('estado_digital', 1))

        Moneda.actualizar_digital(
            id,
            nombre,
            simbolo,
            estado,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Moneda Digital Actualizada",
            mensaje=f"Se han actualizado los datos de la moneda digital '{nombre}'.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda digital actualizada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@moneda_bp.route('/monedas-digitales/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Monedas', 'p_eliminar')
def eliminar_moneda_digital(id):
    try:
        id_usuario = session.get('cedula_usuario')

        Moneda.eliminar_digital(
            id,
            id_usuario
        )

        NotificacionManager.crear(
            titulo="Moneda Digital Desactivada",
            mensaje=f"La moneda digital con ID #{id} ha sido marcada como Inactiva.",
            url_destino="/monedas/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )

        return jsonify({
            "status": "success",
            "message": "Moneda digital desactivada correctamente."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400