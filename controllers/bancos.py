from flask import Blueprint, render_template, request, jsonify, session
from models.bancos import Banco
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

bancos_bp = Blueprint('bancos_crud', __name__)

@bancos_bp.route('/bancos/gestion', methods=['GET', 'POST'])
@requiere_permiso('Bancos', 'p_crear') 
def gestion_bancos():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            nombre = request.form.get('nombre_banco')
            estado = request.form.get('estado', 'Activo')
            
           
            Banco.guardar(nombre, estado, id_usuario)
            
            
            NotificacionManager.crear(
                titulo="Nuevo Banco",
                mensaje=f"Se ha registrado el banco '{nombre}' en el sistema.",
                url_destino="/bancos/gestion",
                tipo_destino="ROL",
                roles=[1, 2], 
                modulo="configuracion"
            )
          
            
            return jsonify({"status": "success", "message": "Banco registrado con éxito"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    
    bancos = Banco.obtener_todos()
    return render_template('bancos/gestion.html', bancos=bancos)

@bancos_bp.route('/bancos/editar/<int:id>', methods=['POST'])
@requiere_permiso('Bancos', 'p_actualizar') 
def editar_banco(id):
    try:
        id_usuario = session.get('cedula_usuario')
        nombre = request.form.get('nombre_banco')
        estado = request.form.get('estado')
        
       
        Banco.actualizar(id, nombre, estado, id_usuario)
        
       
        NotificacionManager.crear(
            titulo="Banco Actualizado",
            mensaje=f"Se han modificado los datos del banco '{nombre}' (ID: #{id}).",
            url_destino="/bancos/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Banco actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@bancos_bp.route('/bancos/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Bancos', 'p_eliminar')
def eliminar_banco(id):
    try:
        id_usuario = session.get('cedula_usuario')
    
        
        Banco.eliminar(id, id_usuario)
        
       
        NotificacionManager.crear(
            titulo="Banco Desactivado",
            mensaje=f"El banco con ID #{id} ha sido marcado como Inactivo.",
            url_destino="/bancos/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Banco desactivado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400