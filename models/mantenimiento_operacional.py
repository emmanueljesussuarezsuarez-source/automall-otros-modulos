from models.db import ConexionBD
from utils.validaciones_mantenimiento_operacional import ValidacionMantenimientoOperacional
from models.bitacora import Bitacora


class MantenimientoOperacional:
    def __init__(self, cod_mantenimiento=None, descripcion_general=None, quien_autoriza=None, estado=None, costo_base=None, costo_final=None):
        self.__cod_mantenimiento = cod_mantenimiento
        self.__descripcion_general = descripcion_general
        self.__quien_autoriza = quien_autoriza
        self.__estado = estado
        self.__costo_base = costo_base
        self.__costo_final = costo_final


    @property
    def cod_mantenimiento(self):
        return self.__cod_mantenimiento


    @cod_mantenimiento.setter
    def cod_mantenimiento(self, valor):
        self.__cod_mantenimiento = valor


    @property
    def descripcion_general(self):
        return self.__descripcion_general


    @descripcion_general.setter
    def descripcion_general(self, valor):
        self.__descripcion_general = valor


    @property
    def quien_autoriza(self):
        return self.__quien_autoriza


    @quien_autoriza.setter
    def quien_autoriza(self, valor):
        self.__quien_autoriza = valor


    @property
    def estado(self):
        return self.__estado


    @estado.setter
    def estado(self, valor):
        self.__estado = valor


    @property
    def costo_base(self):
        return self.__costo_base


    @costo_base.setter
    def costo_base(self, valor):
        self.__costo_base = valor


    @property
    def costo_final(self):
        return self.__costo_final


    @costo_final.setter
    def costo_final(self, valor):
        self.__costo_final = valor


    @staticmethod
    def obtener_mantenimientos(cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                m.cod_mantenimiento,
                m.descripcion_general,
                m.quien_autoriza,
                m.estado,
                m.costo_base,
                m.costo_final,
                dm.tipo,
                dm.fecha_solicitud,
                dm.fecha_completada,
                dm.placa,
                dm.cod_taller,
                dm.cedula_usuario,
                t.nombre_taller
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON dm.cod_mantenimiento = m.cod_mantenimiento
            LEFT JOIN taller t ON t.cod_taller = dm.cod_taller
            WHERE m.estado IN ('Activo', 'Finalizado')
            GROUP BY m.cod_mantenimiento
            ORDER BY m.cod_mantenimiento DESC
        """)
        rows = cursor.fetchall()
        if cedula_usuario:
            Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=3)
        cursor.close()
        conexion.close()
        return rows


    @staticmethod
    def obtener_talleres():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT cod_taller, nombre_taller
            FROM taller
            WHERE estado = '1'
            ORDER BY nombre_taller ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conexion.close()
        return rows


    @staticmethod
    def obtener_usuarios_autorizadores():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT
                    u.cedula_usuario,
                    u.nombre,
                    u.apellido,
                    r.nombre_rol
                FROM t_usuario u
                INNER JOIN t_rol r ON r.cod_rol = u.cod_rol
                WHERE r.nombre_rol IN ('Administrador', 'Super Usuario')
                ORDER BY u.nombre ASC, u.apellido ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener usuarios autorizadores: {e}")
            return []
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def obtener_vehiculos_disponibles():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT placa, estado
            FROM vehiculo
            WHERE estado IN ('Disponible', 'Mantenimiento')
            ORDER BY placa ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conexion.close()
        return rows


    @staticmethod
    def obtener_vehiculos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT placa, estado
            FROM vehiculo
            WHERE estado IN ('Disponible')
            ORDER BY placa ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conexion.close()
        return rows


    @staticmethod
    def validar_existencias(placa, cod_taller, quien_autoriza):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        con_sec = ConexionBD.obtener_conexion_seguridad()
        cursor_sec = con_sec.cursor(dictionary=True)
        try:
            cursor.execute("SELECT placa FROM vehiculo WHERE placa = %s LIMIT 1", (placa,))
            vehiculo = cursor.fetchone()
            if not vehiculo:
                return {"status": False, "mensaje": "La placa seleccionada no existe en la tabla vehiculo."}


            cursor.execute("SELECT cod_taller FROM taller WHERE cod_taller = %s AND estado = '1' LIMIT 1", (cod_taller,))
            taller = cursor.fetchone()
            if not taller:
                return {"status": False, "mensaje": "El taller seleccionado no existe o no está activo."}


            cursor_sec.execute("SELECT cedula_usuario FROM t_usuario WHERE cedula_usuario = %s LIMIT 1", (quien_autoriza,))
            usuario = cursor_sec.fetchone()
            if not usuario:
                return {"status": False, "mensaje": "La persona que autoriza no existe en la tabla t_usuario."}


            return {"status": True}
        except Exception as e:
            return {"status": False, "mensaje": f"Error validando existencias: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()
            cursor_sec.close()
            con_sec.close()


    @staticmethod
    def guardar(descripcion_general, quien_autoriza, tipo, fecha_solicitud, fecha_completada, placa, cod_taller, cedula_usuario, costo_base=None, costo_final=None, detalles=None):
        datos = {
            "descripcion_general": descripcion_general,
            "quien_autoriza": quien_autoriza,
            "tipo": tipo,
            "fecha_solicitud": fecha_solicitud,
            "fecha_completada": fecha_completada,
            "placa": placa,
            "cod_taller": cod_taller
        }


        valido, errores = ValidacionMantenimientoOperacional.validar_mantenimiento(datos)
        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}


        valida_bd = MantenimientoOperacional.validar_existencias(placa, cod_taller, quien_autoriza)
        if not valida_bd["status"]:
            return valida_bd


        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False


            cursor.execute("""
                INSERT INTO mantenimiento (descripcion_general, quien_autoriza, estado, costo_base, costo_final)
                VALUES (%s, %s, %s, %s, %s)
            """, (descripcion_general, quien_autoriza, "Activo", costo_base, costo_final))


            cod_mantenimiento = cursor.lastrowid


            if detalles:
                for detalle in detalles:
                    if detalle.get('descripcion_detalle') or detalle.get('cantidad'):
                        cursor.execute("""
                            INSERT INTO mantenimiento_cant
                            (cod_mantenimiento, descripcion_detalle, cantidad)
                            VALUES (%s, %s, %s)
                        """, (
                            cod_mantenimiento,
                            detalle.get('descripcion_detalle'),
                            detalle.get('cantidad')
                        ))


            cursor.execute("""
                INSERT INTO det_mantenimiento
                (tipo, fecha_solicitud, fecha_completada, cod_mantenimiento, placa, cod_taller, cedula_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                tipo,
                fecha_solicitud,
                fecha_completada if fecha_completada else None,
                cod_mantenimiento,
                placa,
                cod_taller,
                cedula_usuario
            ))


            cursor.execute("""
                UPDATE vehiculo
                SET estado = 'Mantenimiento'
                WHERE placa = %s
            """, (placa,))


            conexion.commit()
            Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=3)
            return {"status": True, "mensaje": "Mantenimiento registrado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error en la base de datos: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def actualizar(cod_mantenimiento, descripcion_general, quien_autoriza, tipo, fecha_solicitud, fecha_completada, placa, cod_taller, cedula_usuario, costo_base=None, costo_final=None, detalles=None):
        datos = {
            "descripcion_general": descripcion_general,
            "quien_autoriza": quien_autoriza,
            "tipo": tipo,
            "fecha_solicitud": fecha_solicitud,
            "fecha_completada": fecha_completada,
            "placa": placa,
            "cod_taller": cod_taller
        }


        valido, errores = ValidacionMantenimientoOperacional.validar_mantenimiento(datos)
        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}


        valida_bd = MantenimientoOperacional.validar_existencias(placa, cod_taller, quien_autoriza)
        if not valida_bd["status"]:
            return valida_bd


        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False


            cursor.execute("""
                UPDATE mantenimiento
                SET descripcion_general = %s,
                    quien_autoriza = %s,
                    costo_base = %s,
                    costo_final = %s
                WHERE cod_mantenimiento = %s
            """, (descripcion_general, quien_autoriza, costo_base, costo_final, cod_mantenimiento))


            cursor.execute("""
                DELETE FROM mantenimiento_cant WHERE cod_mantenimiento = %s
            """, (cod_mantenimiento,))


            if detalles:
                for detalle in detalles:
                    if detalle.get('descripcion_detalle') or detalle.get('cantidad'):
                        cursor.execute("""
                            INSERT INTO mantenimiento_cant
                            (cod_mantenimiento, descripcion_detalle, cantidad)
                            VALUES (%s, %s, %s)
                        """, (
                            cod_mantenimiento,
                            detalle.get('descripcion_detalle'),
                            detalle.get('cantidad')
                        ))


            cursor.execute("""
                UPDATE det_mantenimiento
                SET tipo = %s,
                    fecha_solicitud = %s,
                    fecha_completada = %s,
                    placa = %s,
                    cod_taller = %s,
                    cedula_usuario = %s
                WHERE cod_mantenimiento = %s
            """, (
                tipo,
                fecha_solicitud,
                fecha_completada if fecha_completada else None,
                placa,
                cod_taller,
                cedula_usuario,
                cod_mantenimiento
            ))


            cursor.execute("""
                UPDATE vehiculo
                SET estado = 'Mantenimiento'
                WHERE placa = %s
            """, (placa,))


            conexion.commit()
            Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=3)
            return {"status": True, "mensaje": "Mantenimiento actualizado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error en la base de datos: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def inactivar(cod_mantenimiento, cedula_usuario):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False
            cursor.execute("""
                UPDATE mantenimiento
                SET estado = 'Inactivo'
                WHERE cod_mantenimiento = %s
            """, (cod_mantenimiento,))
            conexion.commit()
            Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=3)
            return True
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def finalizar(cod_mantenimiento, placa, cedula_usuario, costo_final=None, detalles=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False


            cursor.execute("""
                UPDATE mantenimiento
                SET estado = 'Finalizado',
                    costo_final = %s
                WHERE cod_mantenimiento = %s
            """, (costo_final, cod_mantenimiento))


            cursor.execute("""
                UPDATE det_mantenimiento
                SET fecha_completada = CURDATE()
                WHERE cod_mantenimiento = %s AND (fecha_completada IS NULL OR fecha_completada = '')
            """, (cod_mantenimiento,))


            if detalles:
                for detalle in detalles:
                    if detalle.get('descripcion_detalle') or detalle.get('cantidad'):
                        cursor.execute("""
                            INSERT INTO mantenimiento_cant
                            (cod_mantenimiento, descripcion_detalle, cantidad)
                            VALUES (%s, %s, %s)
                        """, (
                            cod_mantenimiento,
                            detalle.get('descripcion_detalle'),
                            detalle.get('cantidad')
                        ))


            cursor.execute("""
                UPDATE vehiculo
                SET estado = 'Disponible'
                WHERE placa = %s
            """, (placa,))


            conexion.commit()
            Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=3)
            return True
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def obtener_detalle_por_mantenimiento(cod_mantenimiento):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT descripcion_detalle, cantidad
                FROM mantenimiento_cant
                WHERE cod_mantenimiento = %s
            """, (cod_mantenimiento,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def filtrar_reporte(cod_mantenimiento=None, placa=None, estado=None, cod_taller=None, fecha_inicio=None, fecha_fin=None, costo_base_desde=None, costo_base_hasta=None, costo_final_desde=None, costo_final_hasta=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            consulta = """
                SELECT
                    m.cod_mantenimiento,
                    m.descripcion_general,
                    m.quien_autoriza,
                    m.estado,
                    m.costo_base,
                    m.costo_final,
                    dm.tipo,
                    dm.fecha_solicitud,
                    dm.fecha_completada,
                    dm.placa,
                    dm.cod_taller,
                    dm.cedula_usuario,
                    t.nombre_taller,
                    mc.descripcion_detalle,
                    mc.cantidad
                FROM mantenimiento m
                INNER JOIN det_mantenimiento dm ON dm.cod_mantenimiento = m.cod_mantenimiento
                LEFT JOIN taller t ON t.cod_taller = dm.cod_taller
                LEFT JOIN mantenimiento_cant mc ON mc.cod_mantenimiento = m.cod_mantenimiento
                WHERE 1 = 1
            """
            parametros = []


            if cod_mantenimiento:
                consulta += " AND m.cod_mantenimiento = %s"
                parametros.append(cod_mantenimiento)


            if placa:
                consulta += " AND dm.placa = %s"
                parametros.append(placa)


            if estado:
                consulta += " AND m.estado = %s"
                parametros.append(estado)


            if cod_taller:
                consulta += " AND dm.cod_taller = %s"
                parametros.append(cod_taller)


            if fecha_inicio and fecha_fin:
                consulta += " AND dm.fecha_solicitud BETWEEN %s AND %s"
                parametros.extend([fecha_inicio, fecha_fin])
            elif fecha_inicio:
                consulta += " AND dm.fecha_solicitud >= %s"
                parametros.append(fecha_inicio)
            elif fecha_fin:
                consulta += " AND dm.fecha_solicitud <= %s"
                parametros.append(fecha_fin)


            if costo_base_desde is not None and costo_base_desde != '':
                consulta += " AND m.costo_base >= %s"
                parametros.append(costo_base_desde)


            if costo_base_hasta is not None and costo_base_hasta != '':
                consulta += " AND m.costo_base <= %s"
                parametros.append(costo_base_hasta)


            if costo_final_desde is not None and costo_final_desde != '':
                consulta += " AND m.costo_final >= %s"
                parametros.append(costo_final_desde)


            if costo_final_hasta is not None and costo_final_hasta != '':
                consulta += " AND m.costo_final <= %s"
                parametros.append(costo_final_hasta)


            consulta += " ORDER BY m.cod_mantenimiento DESC"


            cursor.execute(consulta, tuple(parametros))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()