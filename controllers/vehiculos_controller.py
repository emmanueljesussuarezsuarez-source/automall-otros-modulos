import os
from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify, session 
from models.vehiculo import Vehiculo    
from models.modelo import Modelo      
from models.marca import Marca      
from models.propietario import Propietario 
from werkzeug.utils import secure_filename
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

vehiculos_bp = Blueprint('vehiculos', __name__)

@vehiculos_bp.route('/vehiculos-lista')
@requiere_permiso('Vehiculos', 'p_leer')
def lista():
    vehiculos = Vehiculo.obtener_todos()
    return render_template('vehiculos/lista.html', vehiculos=vehiculos)

@vehiculos_bp.route('/vehiculos-registrar', methods=['GET', 'POST'])
@requiere_permiso('Vehiculos', 'p_crear')
def registro():
    if request.method == 'POST':
        try:
            # Obtener ID del usuario de la sesión
            id_usuario = session.get('cedula_usuario')

            # 1. Manejo de Múltiples Imágenes sin límite
            files = request.files.getlist('imagenes')
            filenames = []
            upload_path = os.path.join('static/uploads')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            for file in files:
                if file and file.filename != '':
                    fname = secure_filename(file.filename)
                    # Evita sobreescritura si suben imágenes con el mismo nombre
                    import time
                    unique_filename = f"{int(time.time()*1000)}_{fname}"
                    file.save(os.path.join(upload_path, unique_filename))
                    filenames.append(unique_filename)
            
            # 2. Datos Documentación
            doc_fields = ['original_totalPropiedad', 'experticia_transito', 'certificado_origen', 'carnet_circulacion', 'reserva_dominio', 'garantia_vehiculo', 'certificado_garantia', 'manual_vehiculoGarantia', 'finiquito', 'resguardo', 'seguro', 'factura_compra']
            d_data = {f: (1 if request.form.get(f) else 0) for f in doc_fields}
            d_data['fecha_ingreso'] = request.form.get('fecha_ingreso')
            d_data['otro_documento'] = request.form.get('otro_documento')

            # 3. Datos Accesorios
            a_data = {
                'copia_llaves': 1 if request.form.get('copia_llaves') else 0,
                'repuesto': 1 if request.form.get('repuesto') else 0,
                'triangulo': 1 if request.form.get('triangulo') else 0
            }

            # 4. Datos Vehículo
            placa = request.form['placa']
            v_data = {
                'placa': placa,
                'color': request.form['color'],
                'anio': request.form['anio'],
                'kilometraje': request.form['kilometraje'],
                'cod_tipo': request.form['tipo'],
                'estado': request.form['estado'],
                'modelo': request.form['modelo'],
                'cedula': request.form['cedula']
            }

            # 5. Datos Catálogo 
            c_data = {
                'precio': request.form['precio'],
                'descripcion': request.form['descripcion_catalogo'],
                'estado': 'Activo'
            }
            
            if Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, filenames, id_usuario):
                # Notificación a Staff (Super Usuario [1], Administrador [2], Vendedor [3], Jefe de Patio [5])
                NotificacionManager.crear_multiple(
                    notificacion_staff={
                        "roles": [1, 2, 3, 5],
                        "titulo": "Nuevo Vehículo Registrado",
                        "mensaje": f"Se ha ingresado el vehículo con placa {placa} al inventario.",
                        "url_destino": "/vehiculos-lista",
                        "modulo": "vehiculos"
                    }
                )

                return jsonify({"status": "success", "message": "¡Vehículo y Catálogo registrados con éxito!"}), 200
            else:
                return jsonify({"status": "error", "message": "Error al registrar en la base de datos."}), 400

        except Exception as e:
            print(f"Error en controlador: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    return render_template('vehiculos/registro.html', 
                           marcas=Marca.obtener_todas(), 
                           modelos=Modelo.obtener_todas(), 
                           propietarios=Propietario.obtener_todos(),
                           tipos=Vehiculo.obtener_tipos())

@vehiculos_bp.route('/vehiculos-editar/<placa>', methods=['GET', 'POST'])
@requiere_permiso('Vehiculos', 'p_actualizar')
def editar(placa):
    vehiculo = Vehiculo.obtener_por_placa(placa)
    
    if request.method == 'POST':
        try:
            id_usuario = session.get('cedula_usuario')

            # 1. Guardar nuevas imágenes si el usuario seleccionó alguna
            files = request.files.getlist('nuevas_imagenes')
            nuevas_imagenes = []
            upload_path = os.path.join('static/uploads')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            import time
            for file in files:
                if file and file.filename != '':
                    fname = secure_filename(file.filename)
                    unique_filename = f"{int(time.time()*1000)}_{fname}"
                    file.save(os.path.join(upload_path, unique_filename))
                    nuevas_imagenes.append(unique_filename)

            # 2. Lista de IDs de imágenes a eliminar (enviadas por el frontend)
            imagenes_eliminar = request.form.getlist('imagenes_eliminar')

            # 3. Documentación
            doc_fields = ['original_totalPropiedad', 'experticia_transito', 'certificado_origen', 'carnet_circulacion', 'reserva_dominio', 'garantia_vehiculo', 'certificado_garantia', 'manual_vehiculoGarantia', 'finiquito', 'resguardo', 'seguro', 'factura_compra']
            d_data = {f: (1 if request.form.get(f) else 0) for f in doc_fields}
            d_data['fecha_ingreso'] = request.form['fecha_ingreso']
            d_data['otro_documento'] = request.form.get('otro_documento', '')

            # 4. Accesorios
            a_data = {
                'copia_llaves': 1 if request.form.get('copia_llaves') else 0,
                'repuesto': 1 if request.form.get('repuesto') else 0,
                'triangulo': 1 if request.form.get('triangulo') else 0
            }
            
            nuevo_estado = request.form.get('estado', 'Disponible')
            estado_anterior = vehiculo.get('estado') if isinstance(vehiculo, dict) else getattr(vehiculo, 'estado', None)

            # 5. Vehículo
            v_data = {
                'placa': request.form['placa'], 
                'color': request.form['color'], 
                'anio': request.form['anio'],
                'kilometraje': request.form['kilometraje'], 
                'cod_tipo': request.form['tipo'], 
                'estado': nuevo_estado,
                'modelo': request.form['modelo'], 
                'cedula': request.form['cedula']
            }

            # 6. Catálogo
            c_data = {
                'precio': request.form['precio'], 
                'descripcion': request.form['descripcion_catalogo']
            }

            if Vehiculo.actualizar(placa, v_data, d_data, a_data, c_data, id_usuario, nuevas_imagenes, imagenes_eliminar):
                hubo_cambio_estado = (estado_anterior is not None) and (str(estado_anterior).lower() != str(nuevo_estado).lower())

                if hubo_cambio_estado:
                    roles_destino = [1, 2, 3, 5]
                    titulo_notif = "Cambio de Estado de Vehículo"
                    msg_notif = f"El vehículo {placa} cambió de estado: '{estado_anterior}' ➔ '{nuevo_estado}'."
                else:
                    roles_destino = [1, 2]
                    titulo_notif = "Vehículo Actualizado"
                    msg_notif = f"Se actualizaron la información o expedientes del vehículo {placa}."

                NotificacionManager.crear_multiple(
                    notificacion_staff={
                        "roles": roles_destino,
                        "titulo": titulo_notif,
                        "mensaje": msg_notif,
                        "url_destino": "/vehiculos-lista",
                        "modulo": "vehiculos"
                    }
                )

                return jsonify({"status": "success", "message": "¡Vehículo actualizado correctamente!"}), 200
            else:
                return jsonify({"status": "error", "message": "No se pudo actualizar en la base de datos."}), 400

        except Exception as e:
            print(f"Error en controlador editar: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400
        
    return render_template('vehiculos/editar_vehiculo.html', 
                           v=vehiculo, 
                           marcas=Marca.obtener_todas(), 
                           modelos=Modelo.obtener_todas(), 
                           propietarios=Propietario.obtener_todos(),
                           tipos=Vehiculo.obtener_tipos())

@vehiculos_bp.route('/vehiculos-eliminar/<placa>', methods=['POST'])
@requiere_permiso('Vehiculos', 'p_eliminar')
def eliminar(placa):
    try:
        id_usuario = session.get('cedula_usuario')
        
        Vehiculo.eliminar(placa, id_usuario)

        # Notificación a Super Usuario [1] y Administrador [2]
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Vehículo Eliminado",
                "mensaje": f"El vehículo con placa {placa} fue eliminado del inventario.",
                "url_destino": "/vehiculos-lista",
                "modulo": "vehiculos"
            }
        )

        flash("Vehículo eliminado correctamente", "success") 
    except Exception as e:
        flash(f"No se pudo eliminar el vehículo: {str(e)}", "error")
    return redirect(url_for('vehiculos.lista'))

@vehiculos_bp.route('/vehiculos-historial')
@requiere_permiso('Vehiculos', 'p_leer')
def historial():
    logs = Vehiculo.obtener_historial_completo()
    return render_template('vehiculos/historial_lista.html', logs=logs)