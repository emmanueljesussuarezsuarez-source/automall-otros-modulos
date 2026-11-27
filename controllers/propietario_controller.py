from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session 
from models.propietario import Propietario
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

propietario_bp = Blueprint('propietarios', __name__)

# RUTA 1: VISTA DE REGISTRO
@propietario_bp.route('/propietarios/registro', methods=['GET', 'POST'])
@requiere_permiso('Propietario', 'p_crear')
def registro():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario') 
            cedula = request.form['cedula']
            razon_social = request.form['razon_social']

            Propietario.guardar(
                cedula, 
                razon_social,
                request.form.get('telefono', ''),
                request.form.get('correo', ''),
                request.form.get('direccion', ''),
                request.form.get('tipo', 'Natural'),
                request.form.get('estado', 'Activo'),  # <-- Con .get() no fallará si no viene en el form
                id_usuario
            )

            # Notificación a Super Usuario [1] y Administrador [2]
            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Nuevo Propietario Registrado",
                    "mensaje": f"Se ha registrado al propietario {razon_social} (C.I./RIF: {cedula}).",
                    "url_destino": "/propietarios/lista",
                    "modulo": "propietarios"
                }
            )

            return jsonify({"status": "success", "message": "Propietario registrado con éxito"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    return render_template('usuarios/propietario_registro.html')

# RUTA 2: VISTA DE LISTADO
@propietario_bp.route('/propietarios/lista')
@requiere_permiso('Propietario', 'p_leer')
def lista():
    propietarios = Propietario.obtener_todos()
    return render_template('usuarios/propietario_lista.html', propietarios=propietarios)

# RUTA 3: ACTUALIZAR
@propietario_bp.route('/propietarios/actualizar', methods=['POST'])
@requiere_permiso('Propietario', 'p_actualizar')
def actualizar():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            cedula_original = request.form['cedula_original']
            razon_social = request.form['razon_social']

            Propietario.actualizar(
                cedula_original, 
                razon_social,
                request.form['telefono'],
                request.form['correo'],
                request.form['direccion'],
                request.form['tipo'],
                request.form['estado'],
                id_usuario
            )

            # Notificación a Super Usuario [1] y Administrador [2]
            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Propietario Actualizado",
                    "mensaje": f"Se actualizaron los datos del propietario {razon_social} (C.I./RIF: {cedula_original}).",
                    "url_destino": "/propietarios/lista",
                    "modulo": "propietarios"
                }
            )

            return jsonify({"status": "success", "message": "Datos del propietario actualizados correctamente"}), 200
        except Exception as e:
            print(f"Error detectado: {e}") 
            return jsonify({"status": "error", "message": f"Error al actualizar: {str(e)}"}), 400

# RUTA PARA ELIMINAR
@propietario_bp.route('/propietarios/eliminar/<string:cedula>', methods=['POST']) 
@requiere_permiso('Propietario', 'p_eliminar') 
def eliminar(cedula):
    try:
        id_usuario = session.get('cedula_usuario')

        if Propietario.eliminar(cedula, id_usuario):
            # Notificación a Super Usuario [1] y Administrador [2]
            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Propietario Inactivado/Eliminado",
                    "mensaje": f"El propietario con C.I./RIF {cedula} ha sido inactivado/eliminado del sistema.",
                    "url_destino": "/propietarios/lista",
                    "modulo": "propietarios"
                }
            )

            return jsonify({"status": "success", "message": "Propietario inactivado correctamente"}), 200
        else:
            return jsonify({"status": "error", "message": "No se pudo eliminar"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@propietario_bp.route('/propietarios/vehiculos/<string:cedula>')
@requiere_permiso('Propietario', 'p_leer')
def api_ver_vehiculos_propietario(cedula):
    vehiculos = Propietario.obtener_flota_por_propietario(cedula)
    return jsonify(vehiculos)