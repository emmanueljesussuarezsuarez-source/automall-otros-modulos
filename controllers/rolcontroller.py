from flask import Blueprint, render_template, request, jsonify, session
from models.rol import Rol
from utils.permisos import requiere_permiso


from utils.notificaciones_manager import NotificacionManager

roles_bp = Blueprint('roles_crud', __name__)

@roles_bp.route('/roles/gestion', methods=['GET', 'POST'])

@requiere_permiso('Roles', 'p_crear') 
def gestion_roles():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            nombre = request.form.get('nombre_rol')
            descripcion = request.form.get('descripcion_rol', '')
            estatus = request.form.get('estatus', 1) 
            
            
            Rol.guardar(nombre, descripcion, estatus, id_usuario)
            
           
            NotificacionManager.crear(
                titulo="Nuevo Rol Creado",
                mensaje=f"Se ha registrado el nuevo rol '{nombre}' en el sistema.",
                url_destino="/roles/gestion",
                tipo_destino="ROL",
                roles=[1, 2], 
                modulo="roles"
            )
           
            
            return jsonify({"status": "success", "message": "Rol registrado con éxito"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    roles = Rol.obtener_todos()
    return render_template('permisos/roles_gestion.html', roles=roles)

@roles_bp.route('/roles/editar/<int:id>', methods=['POST'])
@requiere_permiso('Roles', 'p_actualizar') 
def editar_rol(id):
    try:
        id_usuario = session.get('cedula_usuario')
        nombre = request.form.get('nombre_rol')
        descripcion = request.form.get('descripcion_rol', '')
        estatus = request.form.get('estatus')
        
       
        Rol.actualizar(id, nombre, descripcion, estatus, id_usuario)
        
       
        NotificacionManager.crear(
            titulo="Rol Actualizado",
            mensaje=f"Se han actualizado los datos del rol '{nombre}' (ID: #{id}).",
            url_destino="/roles/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="roles"
        )
        
        
        return jsonify({"status": "success", "message": "Rol actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@roles_bp.route('/roles/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Roles', 'p_eliminar')
def eliminar_rol(id):
    try:
        id_usuario = session.get('cedula_usuario')
    
        
        Rol.eliminar(id, id_usuario)
        
       
        NotificacionManager.crear(
            titulo="Rol Desactivado",
            mensaje=f"El rol con ID #{id} ha sido desactivado/eliminado del sistema.",
            url_destino="/roles/gestion",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="roles"
        )
       
        
        return jsonify({"status": "success", "message": "Rol desactivado/eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400