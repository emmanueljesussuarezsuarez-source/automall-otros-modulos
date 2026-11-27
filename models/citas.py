from models.db import ConexionBD

class CitasModel:

    def __init__(self, cod_citas=None, fecha=None, hora=None, cod_catalogo=None, cedula_usuario=None, estado='Pendiente', activo=1):
        self.__cod_citas = cod_citas
        self.__fecha = fecha
        self.__hora = hora
        self.__cod_catalogo = cod_catalogo
        self.__cedula_usuario = cedula_usuario
        self.__estado = estado
        self.__activo = activo

    @property
    def cod_citas(self): return self.__cod_citas

    @property
    def fecha(self): return self.__fecha

    @property
    def hora(self): return self.__hora

    @property
    def cod_catalogo(self): return self.__cod_catalogo

    @property
    def cedula_usuario(self): return self.__cedula_usuario

    @property
    def estado(self): return self.__estado

    @property
    def activo(self): return self.__activo

    @staticmethod
    def contar_citas_en_horario(fecha, hora, cod_cita_excluir=None):
        if not fecha or not hora:
            return 0

        fecha_limpia = str(fecha).strip()
        hora_str = str(hora).strip()
        hora_busqueda = hora_str[:5] if len(hora_str) >= 5 else hora_str
        
        if cod_cita_excluir:
            sql = """
                SELECT COUNT(*) FROM automall.citas
                WHERE fecha = %s AND hora LIKE %s AND cod_citas != %s AND estado != 'Finalizada' AND activo = 1
            """
            valores = (fecha_limpia, hora_busqueda + "%", int(cod_cita_excluir))
            conexion = ConexionBD.obtener_conexion_seguridad()         
            cursor = conexion.cursor() 
            cursor.execute(sql, valores) 
            resultado = cursor.fetchone()
            cursor.close()
            conexion.close()
            return resultado[0] if resultado else 0
        else:
            #Función SQL fn_citas_en_horario
            conexion = ConexionBD.obtener_conexion_seguridad()         
            cursor = conexion.cursor() 
            cursor.execute("SELECT automall.fn_citas_en_horario(%s, %s)", (fecha_limpia, hora_busqueda)) 
            resultado = cursor.fetchone()
            cursor.close()
            conexion.close()
            return resultado[0] if resultado else 0

    @staticmethod
    def cliente_tiene_cita_pendiente_vehiculo(cedula_usuario, cod_catalogo):
        if not cedula_usuario or not cod_catalogo:
            return False
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()
        sql = """
            SELECT COUNT(*) FROM automall.citas
            WHERE cedula_usuario = %s AND cod_catalogo = %s AND estado = 'Pendiente' AND activo = 1
        """
        cursor.execute(sql, (cedula_usuario, int(cod_catalogo)))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return (resultado[0] > 0) if resultado else False
    

## Registrar-------------------------------------------------------------------------------
    @staticmethod
    def registrar_citas(fecha, hora, cod_catalogo, cedula_usuario):
        #Procedimiento Almacenado sp_agendar_cita
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()

        cursor.callproc('automall.sp_agendar_cita', (fecha, hora, cod_catalogo, cedula_usuario, '@resultado'))
        cursor.execute("SELECT @resultado")
        res = cursor.fetchone()
        
        conexion.commit()
        cursor.close()
        conexion.close()

        if res and res[0] and res[0].startswith('ERROR'):
            return False
        return True
    
    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)

        # CP-CITA-49 - INICIO CORRECCIÓN
        sql = """
        SELECT 
            v.placa,
            v.color,
            v.anio,
            c.cod_catalogo,
            m.nombre_modelo,
            ma.nombre_marca,
            i.URL as imagen_url
        FROM automall.vehiculo v
        INNER JOIN automall.catalogo c ON v.placa = c.placa
        LEFT JOIN automall.modelo m   ON v.cod_modelo = m.cod_modelo
        LEFT JOIN automall.marca ma   ON m.cod_marca = ma.cod_marca
        LEFT JOIN automall.imagen i   ON v.placa = i.placa
        WHERE c.estado = 'Activo'
        """
        # CP-CITA-49 - FIN CORRECCIÓN

        cursor.execute(sql)
        vehiculos_catalogo = cursor.fetchall()

        cursor.close()
        conexion.close()

        return vehiculos_catalogo    
    
    @staticmethod
    def obtener_citas_transito():
        #Vista SQL v_citas_detalle
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT v.cod_citas, v.fecha, v.hora, v.estado,
                   v.nombre_marca, v.nombre_modelo, v.placa, 
                   v.nombre_cliente AS nombre, v.apellido_cliente AS apellido, 
                   v.telefono_cliente AS telefono, v.cedula_usuario,
                   i.URL AS imagen_url
            FROM automall.v_citas_detalle v
            LEFT JOIN automall.vehiculo veh ON v.placa = veh.placa
            LEFT JOIN automall.imagen i ON veh.placa = i.placa
            WHERE v.activo = 1"""
        cursor.execute(sql)
        lista_citas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return lista_citas
## Elminar / modificar---------------------------------------------------------------------

    @staticmethod
    def eliminar_cita_db(cod_cita, cedula_usuario=None):
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True, buffered=True)
            
            if cedula_usuario is None:
                sql = "UPDATE automall.citas SET activo = 0 WHERE cod_citas = %s"
                parametros = (cod_cita,)
            
            else:
                sql = """
                    UPDATE automall.citas 
                    SET activo = 0
                    WHERE cod_citas = %s AND cedula_usuario = %s AND estado = 'Pendiente' AND activo = 1
                """
                parametros = (cod_cita, cedula_usuario)
            
            cursor.execute(sql, parametros)
            conexion.commit()
            
            filas_afectadas = cursor.rowcount
            cursor.close()
            conexion.close()
            
            if filas_afectadas > 0:
                return {"status": True, "mensaje": "¡La cita ha sido eliminada con éxito!"}
            return {"status": False, "mensaje": "No se pudo eliminar la cita seleccionada."}
        except Exception as e:
            return {"status": False, "mensaje": f"Error: {str(e)}"}
        
    @staticmethod
    def obtener_cita_por_id(cod_cita):

        # CP-CITA-48 - INICIO CORRECCIÓN
        sql = "SELECT fecha, hora, estado, cedula_usuario FROM automall.citas WHERE cod_citas = %s AND activo = 1"
        # CP-CITA-48 - FIN CORRECCIÓN
        valores = (int(cod_cita),)
        
        conexion = ConexionBD.obtener_conexion_seguridad() 
        cursor = conexion.cursor()
        
        cursor.execute(sql, valores)
        resultado = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        if resultado:
            hora_raw = str(resultado[1]).strip()
            hora_limpia = hora_raw[:5] if len(hora_raw) >= 5 else hora_raw

            # CP-CITA-48 - INICIO CORRECCIÓN
            return {
                'fecha': str(resultado[0]).strip(),
                'hora': hora_limpia,
                'estado': str(resultado[2]).strip(),
                'cedula_usuario': str(resultado[3]).strip() if resultado[3] else None
            }
            # CP-CITA-48 - FIN CORRECCIÓN
        return None

    @staticmethod
    def actualizar_cita(datos):

        sql = """
            UPDATE automall.citas 
            SET fecha = %s, hora = %s, estado = %s 
            WHERE cod_citas = %s AND activo = 1
        """
        hora_envio = datos['hora'].strip()
        if len(hora_envio) >= 5:
            hora_envio = hora_envio[:5]

        valores = (
            datos['fecha'].strip(),
            hora_envio,
            datos['estado'].strip(),
            int(datos['cod_citas'])
        )
        
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()
        
        cursor.execute(sql, valores)    
        conexion.commit()
        
        cursor.close()
        conexion.close()
## Finalizar cita------------------------------------------------------------------------------
    @staticmethod
    def finalizar_cita_db(cod_citas):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()
        sql = "UPDATE automall.citas SET estado = 'Finalizada' WHERE cod_citas = %s AND activo = 1"
        cursor.execute(sql, (cod_citas,))
        conexion.commit()
        cursor.close()
        conexion.close()

##Esta es la cita personal de cada cliente______________________________________________________
    @staticmethod
    def obtener_por_cliente(cedula_usuario):
        # Uso directo de la Vista SQL v_citas_detalle
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        
        sql = """
            SELECT v.cod_citas, v.fecha, v.hora, v.estado,
                   v.nombre_marca, v.nombre_modelo, v.placa,
                   i.URL AS imagen_url
            FROM automall.v_citas_detalle v
            LEFT JOIN automall.vehiculo veh ON v.placa = veh.placa
            LEFT JOIN automall.imagen i ON veh.placa = i.placa
            WHERE v.cedula_usuario = %s AND v.activo = 1
            ORDER BY v.fecha DESC, v.hora DESC
        """
        cursor.execute(sql, (cedula_usuario,))
        citas = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        return citas
    
    @staticmethod
    def modificar_hora_cliente(cod_cita, nueva_hora, cedula_usuario):
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True, buffered=True)
            
            # Restricción total de seguridad: Coincidencia de dueño y estado pendiente
            sql = """
                UPDATE automall.citas 
                SET hora = %s 
                WHERE cod_citas = %s AND cedula_usuario = %s AND estado = 'Pendiente' AND activo = 1
            """
            cursor.execute(sql, (cod_cita, nueva_hora , cedula_usuario))
            conexion.commit()
            
            filas_afectadas = cursor.rowcount
            cursor.close()
            conexion.close()
            
            if filas_afectadas > 0:
                return {"status": True, "mensaje": "¡La hora de tu cita ha sido modificada con éxito!"}
            return {"status": False, "mensaje": "No se pudo modificar la hora (la cita ya no está pendiente o no te pertenece)."}
        except Exception as e:
            return {"status": False, "mensaje": f"Error: {str(e)}"}

# Evita romper modulos
citasModel = CitasModel