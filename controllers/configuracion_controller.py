import os 
from flask import Blueprint, render_template, request, jsonify, session
from models.modulos import Modulo
from models.acciones import Accion
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

config_bp = Blueprint('config_crud', __name__)

@config_bp.route('/configuracion/modulos-acciones', methods=['GET'])
@requiere_permiso('Modulos', 'p_leer') 
def gestion_configuracion():
    modulos = Modulo.obtener_todos()
    acciones = Accion.obtener_todas()
    return render_template('permisos/modulos_acciones.html', modulos=modulos, acciones=acciones)

# ================= RUTAS DE MÓDULOS =================
@config_bp.route('/modulos/crear', methods=['POST'])
@requiere_permiso('Modulos', 'p_crear')
def crear_modulo():
    try:
        nombre_modulo = request.form.get('nombre_modulo')
        
        
        nombre_normalizado = nombre_modulo.lower().replace(" ", "_")
        nombre_archivo = f"{nombre_normalizado}.py"
        
        
        ruta_modelo = os.path.join('models', nombre_archivo)
        ruta_controlador = os.path.join('controllers', nombre_archivo)
        
       
        faltan_archivos = []
        if not os.path.exists(ruta_modelo):
            faltan_archivos.append(f"models/{nombre_archivo}")
        if not os.path.exists(ruta_controlador):
            faltan_archivos.append(f"controllers/{nombre_archivo}")
            
        
        if faltan_archivos:
            archivos_str = " y ".join(faltan_archivos)
            return jsonify({
                "status": "error", 
                "message": f"No se puede registrar el módulo. Faltan los siguientes archivos físicos en el sistema: {archivos_str}."
            }), 400
        
        Modulo.guardar(nombre_modulo, request.form.get('estatus', 1), session.get('cedula_usuario'))
        
       
        NotificacionManager.crear(
            titulo="Nuevo Módulo Creado",
            mensaje=f"Se ha registrado exitosamente el módulo '{nombre_modulo}'.",
            url_destino="/configuracion/modulos-acciones",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
        
        return jsonify({"status": "success", "message": "Módulo registrado con éxito"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@config_bp.route('/modulos/editar/<int:id>', methods=['POST'])
def editar_modulo(id):
    try:
        nombre_modulo = request.form.get('nombre_modulo')
        Modulo.actualizar(id, nombre_modulo, request.form.get('estatus'), session.get('cedula_usuario'))
        
        
        NotificacionManager.crear(
            titulo="Módulo Actualizado",
            mensaje=f"Se ha modificado la configuración del módulo '{nombre_modulo}'.",
            url_destino="/configuracion/modulos-acciones",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
        
        
        return jsonify({"status": "success", "message": "Módulo actualizado"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@config_bp.route('/modulos/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Modulos', 'p_eliminar')
def eliminar_modulo(id):
    Modulo.eliminar(id, session.get('cedula_usuario'))
    
   
    NotificacionManager.crear(
        titulo="Módulo Desactivado",
        mensaje=f"El módulo con ID #{id} ha sido desactivado del sistema.",
        url_destino="/configuracion/modulos-acciones",
        tipo_destino="ROL",
        roles=[1, 2],
        modulo="configuracion"
    )
    
    
    return jsonify({"status": "success", "message": "Módulo desactivado"}), 200


# ================= RUTAS DE ACCIONES =================
@config_bp.route('/acciones/crear', methods=['POST'])
@requiere_permiso('Acciones', 'p_crear')
def crear_accion():
    try:
        nombre_accion = request.form.get('nom_accion')
        Accion.guardar(nombre_accion, request.form.get('estatus', 1), session.get('cedula_usuario'))
        
       
        NotificacionManager.crear(
            titulo="Nueva Acción Creada",
            mensaje=f"Se ha registrado la acción '{nombre_accion}' en el sistema.",
            url_destino="/configuracion/modulos-acciones",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Acción registrada con éxito"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@config_bp.route('/acciones/editar/<int:id>', methods=['POST'])
@requiere_permiso('Acciones', 'p_actualizar')
def editar_accion(id):
    try:
        nombre_accion = request.form.get('nom_accion')
        Accion.actualizar(id, nombre_accion, request.form.get('estatus'), session.get('cedula_usuario'))
        
        
        NotificacionManager.crear(
            titulo="Acción Actualizada",
            mensaje=f"Se han guardado los cambios para la acción '{nombre_accion}'.",
            url_destino="/configuracion/modulos-acciones",
            tipo_destino="ROL",
            roles=[1, 2],
            modulo="configuracion"
        )
       
        
        return jsonify({"status": "success", "message": "Acción actualizada"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@config_bp.route('/acciones/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Acciones', 'p_eliminar')
def eliminar_accion(id):
    Accion.eliminar(id, session.get('cedula_usuario'))
    
   
    NotificacionManager.crear(
        titulo="Acción Desactivada",
        mensaje=f"La acción con ID #{id} ha sido desactivada del sistema.",
        url_destino="/configuracion/modulos-acciones",
        tipo_destino="ROL",
        roles=[1, 2],
        modulo="configuracion"
    )
   
    
    return jsonify({"status": "success", "message": "Acción desactivada"}), 200