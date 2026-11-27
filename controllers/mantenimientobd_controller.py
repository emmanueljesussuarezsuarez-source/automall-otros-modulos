from flask import Blueprint, render_template, jsonify, request, send_file, session
from utils.decorators import login_required
from models.mantenimiento import Mantenimiento


from utils.notificaciones_manager import NotificacionManager

mantenimiento_bp = Blueprint('mantenimiento', __name__)

@mantenimiento_bp.route('/mantenimiento')
@login_required
def vista_mantenimiento():
    return render_template('mantenimiento/mant_bd.html')

@mantenimiento_bp.route('/api/backup/<db_name>', methods=['GET'])
@login_required
def respaldar_bd(db_name):

    cedula = session.get('cedula_usuario')
    resultado = Mantenimiento.generar_respaldo(db_name, cedula)
    
    if not resultado["status"]:
        return jsonify({"status": "error", "message": resultado["message"]}), resultado["code"]
    
   
    NotificacionManager.crear(
        titulo="Respaldo Generado",
        mensaje=f"Se ha generado un nuevo respaldo de la base de datos '{db_name}' (Usuario: {cedula}).",
        url_destino="/mantenimiento",
        tipo_destino="ROL",
        roles=[1, 2], 
        modulo="mantenimiento"
    )
    
    
    return send_file(
        resultado["filepath"], 
        as_attachment=True, 
        download_name=resultado["filename"]
    )

@mantenimiento_bp.route('/api/restore/<db_name>', methods=['POST'])
@login_required
def restaurar_bd(db_name):
    if 'backup_file' not in request.files:
        return jsonify({"status": "error", "message": "No se subió ningún archivo"}), 400

    archivo_subido = request.files['backup_file']
    cedula = session.get('cedula_usuario')
    resultado = Mantenimiento.restaurar_respaldo(db_name, archivo_subido, cedula)
    
    if not resultado["status"]:
        return jsonify({"status": "error", "message": resultado["message"]}), resultado["code"]
        
    
    NotificacionManager.crear(
        titulo="Alerta: Base de Datos Restaurada",
        mensaje=f"¡Atención! La base de datos '{db_name}' ha sido restaurada desde un respaldo por el usuario {cedula}.",
        url_destino="/mantenimiento",
        tipo_destino="ROL",
        roles=[1, 2], 
        modulo="mantenimiento"
    )
   
        
    return jsonify({"status": "success", "message": resultado["message"]})