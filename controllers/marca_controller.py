from flask import Blueprint, render_template, request, jsonify, session, url_for
from models.marca import Marca
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

marca_bp = Blueprint('marcas', __name__)

@marca_bp.route('/marcas/registro', methods=['GET', 'POST'])
@requiere_permiso('Vehiculos', 'p_crear')
def registro_marca():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            nombre = request.form['nombre_marca'].strip()
            estado = request.form.get('estado', 'Activo')
            
            # Guardamos la marca
            Marca.guardar(nombre, estado, id_usuario)

            # Buscamos la marca recién creada para obtener su ID generado
            marcas_todas = Marca.obtener_todas()
            nueva_marca = next((m for m in marcas_todas if m['nombre_marca'].lower() == nombre.lower()), None)
            cod_marca = nueva_marca['cod_marca'] if nueva_marca else None

            # Notificación a Super Usuario [1] y Administrador [2]
            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Nueva Marca Registrada",
                    "mensaje": f"Se ha registrado la marca '{nombre}' en el catálogo.",
                    "url_destino": "/marcas/registro",
                    "modulo": "vehiculos"
                }
            )

            # Devolvemos JSON con id y nombre para agregarlo dinámicamente al selector
            return jsonify({
                "status": "success", 
                "message": "Marca registrada con éxito",
                "cod_marca": cod_marca,
                "nombre_marca": nombre
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    marcas = Marca.obtener_todas()
    return render_template('vehiculos/marca_registro.html', marcas=marcas)

@marca_bp.route('/marcas/editar/<int:id>', methods=['POST'])
@requiere_permiso('Vehiculos', 'p_actualizar')
def editar_marca(id):
    try:
        id_usuario = session.get('cedula_usuario')
        nombre = request.form['nombre_marca']
        estado = request.form['estado']
        
        Marca.actualizar(id, nombre, estado, id_usuario)

        # Notificación a Super Usuario [1] y Administrador [2]
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Marca Actualizada",
                "mensaje": f"Se ha actualizado la información de la marca '{nombre}'.",
                "url_destino": "/marcas/registro",
                "modulo": "vehiculos"
            }
        )

        return jsonify({"status": "success", "message": "Marca actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@marca_bp.route('/marcas/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Vehiculos', 'p_eliminar')
def eliminar_marca(id):
    try:
        id_usuario = session.get('cedula_usuario')
        
        marca_obj = Marca.obtener_por_id(id) if hasattr(Marca, 'obtener_por_id') else None
        nombre_marca = marca_obj.nombre if marca_obj and hasattr(marca_obj, 'nombre') else f"ID {id}"

        Marca.eliminar(id, id_usuario)

        # Notificación a Super Usuario [1] y Administrador [2]
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Marca Eliminada",
                "mensaje": f"La marca '{nombre_marca}' ha sido eliminada del sistema.",
                "url_destino": "/marcas/registro",
                "modulo": "vehiculos"
            }
        )

        return jsonify({"status": "success", "message": "Marca eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400