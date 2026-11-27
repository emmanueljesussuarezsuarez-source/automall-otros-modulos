from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.permiso import Permiso
from utils.permisos import requiere_superusuario 


from utils.notificaciones_manager import NotificacionManager

permisos_bp = Blueprint('permisos', __name__) 

@permisos_bp.route('/gestionar', methods=['GET', 'POST'])
@requiere_superusuario  
def gestionar():
    if request.method == 'POST':
        id_rol_actual = request.form.get('id_rol_actual')
        
        permisos_marcados = request.form.getlist('permisos_activos') 

        cedula = session.get('cedula_usuario')
        
        resultado = Permiso.sincronizar_permisos(id_rol_actual, permisos_marcados, cedula)
        
        if resultado["status"]:
           
            flash("Matriz de permisos actualizada con éxito para este rol.", "success")
            
            NotificacionManager.crear(
                titulo="Matriz de Permisos Modificada",
                mensaje=f"El usuario {cedula} ha actualizado los permisos para el rol (ID: {id_rol_actual}).",
                url_destino=url_for('permisos.gestionar', cod_rol=id_rol_actual),
                tipo_destino="ROL",
                roles=[1, 2], 
                modulo="permisos"
            )
           
            
        else:
            
            flash(f"Error al procesar la actualización: {resultado['error']}", "error")
            
        return redirect(url_for('permisos.gestionar', cod_rol=id_rol_actual))

    roles = Permiso.obtener_roles()
    id_rol_seleccionado = request.args.get('cod_rol', type=int)
    
    modulos = []
    acciones = []
    permisos_asignados = []
    
    if id_rol_seleccionado:
        modulos = Permiso.obtener_modulos_activos()
        acciones = Permiso.obtener_acciones_activas()
        permisos_asignados = Permiso.obtener_permisos_asignados_rol(id_rol_seleccionado)
        
    return render_template('permisos/gestionar.html', 
                           roles=roles, 
                           modulos=modulos, 
                           acciones=acciones,
                           permisos_asignados=permisos_asignados, 
                           id_rol_seleccionado=id_rol_seleccionado)