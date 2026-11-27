import os
from models.db import ConexionBD
from datetime import date 
from mysql.connector import Error
from models.bitacora import Bitacora

class Vehiculo:
    @staticmethod
    def guardar_con_documentos(v_data, d_data, a_data, c_data, filenames, id_usuario_sesion):
        try:
            # ASIGNACIÓN AUTOMÁTICA: Fecha publicación = Fecha ingreso
            c_data['fecha_pub'] = d_data['fecha_ingreso']
            Vehiculo.__validar_campos(v_data, c_data)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion() 
        cursor = conexion.cursor()
        try:
            sql_doc = """INSERT INTO documentacion (
                original_totalPropiedad, experticia_transito, certificado_origen, 
                carnet_circulacion, reserva_dominio, garantia_vehiculo, 
                certificado_garantia, manual_vehiculoGarantia, finiquito, 
                resguardo, seguro, factura_compra, fecha_ingreso, otro_documento
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            
            cursor.execute(sql_doc, (
                d_data['original_totalPropiedad'], d_data['experticia_transito'], d_data['certificado_origen'],
                d_data['carnet_circulacion'], d_data['reserva_dominio'], d_data['garantia_vehiculo'],
                d_data['certificado_garantia'], d_data['manual_vehiculoGarantia'], d_data['finiquito'],
                d_data['resguardo'], d_data['seguro'], d_data['factura_compra'], 
                d_data['fecha_ingreso'], d_data['otro_documento']
            ))
            cod_documento = cursor.lastrowid

            sql_acc = "INSERT INTO accesorio (copia_llaves, repuesto, triangulo) VALUES (%s,%s,%s)"
            cursor.execute(sql_acc, (a_data['copia_llaves'], a_data['repuesto'], a_data['triangulo']))
            cod_accesorio = cursor.lastrowid

            sql_veh = """INSERT INTO vehiculo (placa, color, anio, kilometraje, cod_tipo, estado, 
                         cod_modelo, cedula_propietario, cod_documento, cod_accesorio) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            placa_limpia = v_data['placa'].strip().upper()
            cursor.execute(sql_veh, (
                placa_limpia, v_data['color'], v_data['anio'], v_data['kilometraje'], 
                v_data['cod_tipo'], v_data['estado'], v_data['modelo'], v_data['cedula'], 
                cod_documento, cod_accesorio
            ))

            Vehiculo.__registrar_historial(placa_limpia, v_data['estado'], "Ingreso inicial al sistema.", cursor)

            sql_cat = "INSERT INTO catalogo (estado, precio, descripcion, fecha_publicacion, placa) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_cat, (c_data['estado'], c_data['precio'], c_data['descripcion'], c_data['fecha_pub'], placa_limpia))

            # Inserción de todas las imágenes en la tabla imagen
            sql_img = "INSERT INTO imagen (URL, placa) VALUES (%s, %s)"
            for fname in filenames:
                cursor.execute(sql_img, (f"uploads/{fname}", placa_limpia))

            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=2)
            
            conexion.commit()
            return True
        except Error as e:
            conexion.rollback()
            if e.errno == 1062:
                raise Exception(f"La placa {v_data['placa']} ya se encuentra registrada.")
            raise Exception(f"Error de base de datos: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(placa_original, v_data, d_data, a_data, c_data, id_usuario_sesion, nuevas_imagenes=None, imagenes_eliminar=None):
        try:
            c_data['fecha_pub'] = d_data['fecha_ingreso']
            Vehiculo.__validar_campos(v_data, c_data)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("SELECT cod_documento, cod_accesorio FROM vehiculo WHERE placa = %s", (placa_original,))
            ids = cursor.fetchone()
            if not ids: return False
            cod_doc = ids['cod_documento']
            cod_acc = ids['cod_accesorio']

            # 1. Documentación
            sql_doc = """UPDATE documentacion SET 
                original_totalPropiedad=%s, experticia_transito=%s, certificado_origen=%s, 
                carnet_circulacion=%s, reserva_dominio=%s, garantia_vehiculo=%s, 
                certificado_garantia=%s, manual_vehiculoGarantia=%s, finiquito=%s, 
                resguardo=%s, seguro=%s, factura_compra=%s, fecha_ingreso=%s, otro_documento=%s
                WHERE cod_documento=%s"""
            cursor.execute(sql_doc, list(d_data.values()) + [cod_doc])

            # 2. Accesorios
            sql_acc = "UPDATE accesorio SET copia_llaves=%s, repuesto=%s, triangulo=%s WHERE cod_accesorio=%s"
            cursor.execute(sql_acc, (a_data['copia_llaves'], a_data['repuesto'], a_data['triangulo'], cod_acc))

            # 3. Datos del Vehículo
            sql_veh = """UPDATE vehiculo SET placa=%s, color=%s, anio=%s, kilometraje=%s, cod_tipo=%s, 
                         estado=%s, cod_modelo=%s, cedula_propietario=%s WHERE placa=%s"""
            placa_nueva = v_data['placa'].strip().upper()
            cursor.execute(sql_veh, (placa_nueva, v_data['color'], v_data['anio'], v_data['kilometraje'], 
                                   v_data['cod_tipo'], v_data['estado'], v_data['modelo'], v_data['cedula'], placa_original))
            

            # 4. Catálogo
            sql_cat = "UPDATE catalogo SET precio=%s, descripcion=%s, fecha_publicacion=%s, placa=%s WHERE placa=%s"
            cursor.execute(sql_cat, (c_data['precio'], c_data['descripcion'], c_data['fecha_pub'], placa_nueva, placa_original))

            # 5. Si la placa cambió, actualizar las imágenes que ya tenía
            if placa_nueva != placa_original:
                cursor.execute("UPDATE imagen SET placa=%s WHERE placa=%s", (placa_nueva, placa_original))

            # 6. Eliminar las imágenes seleccionadas usando su URL
            if imagenes_eliminar:
                for url_foto in imagenes_eliminar:
                    if url_foto:
                        # Borrar de la base de datos
                        cursor.execute("DELETE FROM imagen WHERE URL = %s", (url_foto,))
                        # Borrar archivo del disco
                        archivo_fisico = os.path.join('static', url_foto)
                        if os.path.exists(archivo_fisico):
                            try:
                                os.remove(archivo_fisico)
                            except Exception:
                                pass

            # 7. Insertar nuevas imágenes subidas
            if nuevas_imagenes:
                sql_img = "INSERT INTO imagen (URL, placa) VALUES (%s, %s)"
                for fname in nuevas_imagenes:
                    cursor.execute(sql_img, (f"uploads/{fname}", placa_nueva))

            # 8. Bitácora
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=2)

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conexion.commit()
            return True
        except Exception as e:
            conexion.rollback()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(placa, id_usuario_sesion):
        """ELIMINADO LÓGICO"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            sql = "UPDATE vehiculo SET estado = 'Inactivo' WHERE placa = %s"
            cursor.execute(sql, (placa,))
            
            # Historial de estado interno
            Vehiculo.__registrar_historial(placa, 'Inactivo', "Eliminado lógicamente.", cursor)
            
            # 8. REGISTRO EN BITÁCORA DEL SISTEMA (Módulo 2: Vehículos, Acción 3: Eliminar)
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=2)
            
            conexion.commit()
            return True
        except Exception:
            conexion.rollback()
            return False
        finally:
            cursor.close()
            conexion.close()

    # ==========================================
    #   MÉTODOS DE CONSULTA (LECTURA)
    # ==========================================

    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Consulta base
        sql = """SELECT v.*, ma.nombre_marca, mo.nombre_modelo, i.URL as imagen_url,
                        d.*, a.*, p.razon_social as nombre_propietario
                 FROM vehiculo v
                 JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
                 JOIN marca ma ON mo.cod_marca = ma.cod_marca
                 JOIN documentacion d ON v.cod_documento = d.cod_documento
                 JOIN accesorio a ON v.cod_accesorio = a.cod_accesorio
                 JOIN propietario p ON v.cedula_propietario = p.cedula_propietario
                 LEFT JOIN imagen i ON v.placa = i.placa 
                 WHERE v.estado != 'Inactivo' 
                 ORDER BY v.placa DESC"""
        cursor.execute(sql)
        filas = cursor.fetchall()
        conexion.close()

        # Agrupar por vehículo para que aparezca 1 sola vez en la lista
        vehiculos_dict = {}
        for f in filas:
            placa = f['placa']
            if placa not in vehiculos_dict:
                veh = dict(f)
                veh['imagenes_lista'] = []
                if f.get('imagen_url'):
                    veh['imagenes_lista'].append(f['imagen_url'])
                vehiculos_dict[placa] = veh
            else:
                # Si vienen más fotos para la misma placa, se agregan a la galería
                url_foto = f.get('imagen_url')
                if url_foto and url_foto not in vehiculos_dict[placa]['imagenes_lista']:
                    vehiculos_dict[placa]['imagenes_lista'].append(url_foto)
        
        # La primera foto seleccionada queda fija como foto de portada
        for v in vehiculos_dict.values():
            v['imagen_url'] = v['imagenes_lista'][0] if v['imagenes_lista'] else None

        return list(vehiculos_dict.values())

    @staticmethod
    def obtener_por_placa(placa):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """SELECT v.*, d.*, a.*, c.precio, c.descripcion as descripcion_catalogo, c.fecha_publicacion
                 FROM vehiculo v
                 JOIN documentacion d ON v.cod_documento = d.cod_documento
                 JOIN accesorio a ON v.cod_accesorio = a.cod_accesorio
                 LEFT JOIN catalogo c ON v.placa = c.placa
                 WHERE v.placa = %s AND v.estado != 'Inactivo'"""
        cursor.execute(sql, (placa,))
        vehiculo = cursor.fetchone()

        if vehiculo:
            # Seleccionamos URL directamente de la tabla imagen
            cursor.execute("SELECT URL FROM imagen WHERE placa = %s", (placa,))
            fotos = cursor.fetchall()
            vehiculo['imagenes'] = fotos  # Lista de dicts: [{'URL': 'uploads/...'}, ...]
            vehiculo['imagen_url'] = fotos[0]['URL'] if fotos else None

        conexion.close()
        return vehiculo

    @staticmethod
    def buscar_por_placa(placa):
        """Búsqueda específica para ventas/catálogo (Solo disponibles)"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = """SELECT v.placa, m.nombre_marca AS marca, mo.nombre_modelo AS modelo, v.anio, v.color, 
                        tv.nombre_tipo AS tipo, c.precio, c.estado
                 FROM vehiculo v
                 INNER JOIN catalogo c ON v.placa = c.placa
                 INNER JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
                 INNER JOIN marca m ON mo.cod_marca = m.cod_marca
                 INNER JOIN tipo_vehiculo tv ON v.cod_tipo = tv.cod_tipo 
                 WHERE v.placa = %s AND v.estado = 'Disponible' LIMIT 1"""
        cursor.execute(sql, (placa.strip().upper(),))
        vehiculo = cursor.fetchone()
        conexion.close()
        if vehiculo:
            vehiculo['precio'] = float(vehiculo['precio'])
            return {'exito': True, 'vehiculo': vehiculo}
        return None

    @staticmethod
    def obtener_historial_completo():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.callproc('sp_obtener_historial_vehiculos')
            res = []
            for result in cursor.stored_results():
                res = result.fetchall()
            
            return res
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_vehiculos_activos():
        return Vehiculo.__consulta_simple_filtro("Disponible")

    @staticmethod
    def obtener_vehiculos_disponibles():
        return Vehiculo.__consulta_simple_filtro("Disponible")

    @staticmethod
    def obtener_tipos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT cod_tipo, nombre_tipo FROM tipo_vehiculo")
        res = cursor.fetchall()
        conexion.close()
        return res

    # ==========================================
    #   MÉTODOS PRIVADOS (ENCAPSULAMIENTO)
    # ==========================================

    @staticmethod
    def __validar_campos(v_data, c_data):
        """Privado: Valida que los datos sean lógicos antes de guardarlos."""
        # Validar Placa
        if not v_data.get('placa') or len(v_data['placa'].strip()) < 5:
            raise ValueError("La placa debe tener al menos 5 caracteres.")
        
        # Validar Año
        anio_actual = date.today().year
        if not (1900 <= int(v_data['anio']) <= anio_actual + 1):
            raise ValueError(f"El año es inválido (Rango: 1900 - {anio_actual + 1}).")
        
        # Validar Kilometraje
        if int(v_data['kilometraje']) < 0:
            raise ValueError("El kilometraje no puede ser un número negativo.")
        
        # Validar Precio
        if float(c_data['precio']) <= 0:
            raise ValueError("El precio debe ser un monto mayor a cero.")
        
        # Validar campos vacíos esenciales
        if not v_data.get('cedula') or not v_data.get('modelo'):
            raise ValueError("La cédula del propietario y el modelo son obligatorios.")

    @staticmethod
    def __registrar_historial(placa, estado, observaciones, cursor):
        sql = "INSERT INTO historia_estado_vehiculo (placa, estado, fecha_cambio, observaciones) VALUES (%s, %s, NOW(), %s)"
        cursor.execute(sql, (placa, estado, observaciones))

    @staticmethod
    def __consulta_simple_filtro(estado):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = """SELECT v.placa, mo.nombre_modelo as modelo, v.color 
                 FROM vehiculo v JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
                 WHERE v.estado = %s ORDER BY v.placa"""
        cursor.execute(sql, (estado,))
        res = cursor.fetchall()
        conexion.close()
        return res