from flask import Blueprint, render_template, request, jsonify, session
from models.metodo import MetodoPago
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

metodos_pago_bp = Blueprint('metodos_pago_crud', __name__)

@metodos_pago_bp.route('/metodos-pago/gestion', methods=['GET', 'POST'])
@requiere_permiso('Metodo', 'p_crear') 
def gestion_metodos():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            nombre = request.form.get('nombre_metodo')
            requiere_ref = request.form.get('requiere_referencia', 0) 
            estado = request.form.get('estado', 'Activo')
            
           
            MetodoPago.guardar(nombre, requiere_ref, estado, id_usuario)
            
            
            NotificacionManager.crear(
                titulo="Nuevo Método de Pago",
                mensaje=f"Se ha registrado el método '{nombre}' en el sistema.",
                url_destino="/metodos-pago/gestion",
                tipo_destino="ROL",
                roles=[1, 2], 
                modulo="configuracion"
            )
           
            
            return jsonify({"status": "success", "message": "Método de pago registrado con éxito"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    
    metodos = MetodoPago.obtener_todos()
    return render_template('metodos_pago/gestion.html', metodos=metodos)

@metodos_pago_bp.route('/metodos-pago/editar/<int:id>', methods=['POST'])
@requiere_permiso('Metodo', 'p_actualizar') 
def editar_metodo(id):
    try:
        id_usuario = session.get('cedula_usuario')
        nombre = request.form.get('nombre_metodo')
        requiere_ref = request.form.get('requiere_referencia', 0)
        estado = request.form.get('estado')
        
        
        MetodoPago.actualizar(id, nombre, requiere_ref, estado, id_usuario)
        
        
        NotificacionManager.crear(
            titulo="Método de Pago Actualizado",
            mensaje=f"Se han modificado los datos del método '{nombre}' (ID: #{id}).",
            url_destino="/metodos-pago/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Método actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@metodos_pago_bp.route('/metodos-pago/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Metodo', 'p_eliminar')
def eliminar_metodo(id):
    try:
        id_usuario = session.get('cedula_usuario')
    
        
        MetodoPago.eliminar(id, id_usuario)
        
       
        NotificacionManager.crear(
            titulo="Método de Pago Desactivado",
            mensaje=f"El método con ID #{id} ha sido marcado como Inactivo.",
            url_destino="/metodos-pago/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Método desactivado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400