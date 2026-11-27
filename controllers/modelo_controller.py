from flask import Blueprint, render_template, request, jsonify, session, url_for
from models.modelo import Modelo
from models.marca import Marca
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

modelo_bp = Blueprint('modelos', __name__)

@modelo_bp.route('/modelos/registro', methods=['GET', 'POST'])
@requiere_permiso('Vehiculos', 'p_crear')
def registro_modelo():
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')
            nombre = request.form['nombre_modelo'].strip()
            estado = request.form.get('estado', 'Activo')
            cod_marca = request.form['cod_marca'] 
            
            # Guardamos el modelo
            Modelo.guardar(nombre, estado, cod_marca, id_usuario)

            # Buscamos el ID del modelo recién insertado para la marca seleccionada
            modelos_marca = Modelo.obtener_por_marca(cod_marca)
            nuevo = next((m for m in modelos_marca if m['nombre_modelo'].lower() == nombre.lower()), None)
            cod_modelo = nuevo['cod_modelo'] if nuevo else None

            # Notificación a Super Usuario [1] y Administrador [2]
            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Nuevo Modelo Registrado",
                    "mensaje": f"Se ha registrado el modelo '{nombre}' en el catálogo.",
                    "url_destino": "/modelos/registro",
                    "modulo": "vehiculos"
                }
            )

            # Devolvemos JSON con los datos para actualizar el select en tiempo real
            return jsonify({
                "status": "success", 
                "message": "Modelo registrado con éxito",
                "cod_modelo": cod_modelo,
                "nombre_modelo": nombre,
                "cod_marca": cod_marca
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    modelos = Modelo.obtener_todas()
    marcas = Marca.obtener_activas() 
    return render_template('vehiculos/modelo_registro.html', modelos=modelos, marcas=marcas)

@modelo_bp.route('/modelos/editar/<int:id>', methods=['POST'])
@requiere_permiso('Vehiculos', 'p_actualizar') 
def editar_modelo(id):
    try:
        id_usuario = session.get('cedula_usuario')
        nombre = request.form['nombre_modelo']
        estado = request.form['estado']
        cod_marca = request.form['cod_marca']
        
        Modelo.actualizar(id, nombre, estado, cod_marca, id_usuario)

        # Notificación a Super Usuario [1] y Administrador [2]
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Modelo Actualizado",
                "mensaje": f"Se ha actualizado la información del modelo '{nombre}'.",
                "url_destino": "/modelos/registro",
                "modulo": "vehiculos"
            }
        )

        return jsonify({"status": "success", "message": "Modelo actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@modelo_bp.route('/modelos/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('Vehiculos', 'p_eliminar')
def eliminar_modelo(id):
    try:
        id_usuario = session.get('cedula_usuario')

        modelo_obj = Modelo.obtener_por_id(id) if hasattr(Modelo, 'obtener_por_id') else None
        nombre_modelo = modelo_obj.nombre if modelo_obj and hasattr(modelo_obj, 'nombre') else f"ID {id}"

        Modelo.eliminar(id, id_usuario)

        # Notificación a Super Usuario [1] y Administrador [2]
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Modelo Eliminado",
                "mensaje": f"El modelo '{nombre_modelo}' ha sido eliminado del catálogo.",
                "url_destino": "/modelos/registro",
                "modulo": "vehiculos"
            }
        )

        return jsonify({"status": "success", "message": "Modelo eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400