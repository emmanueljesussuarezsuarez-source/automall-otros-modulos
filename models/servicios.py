from models.db import ConexionBD
from utils.validaciones_servicios import ValidacionServicios
from models.bitacora import Bitacora


class Servicios:
    def __init__(self, cod_servicios=None, nombre_servicio=None, estado=None):
        self.__cod_servicios = cod_servicios
        self.__nombre_servicio = nombre_servicio
        self.__estado = estado

    @property
    def cod_servicios(self):
        return self.__cod_servicios

    @cod_servicios.setter
    def cod_servicios(self, valor):
        self.__cod_servicios = valor

    @property
    def nombre_servicio(self):
        return self.__nombre_servicio

    @nombre_servicio.setter
    def nombre_servicio(self, valor):
        self.__nombre_servicio = valor

    @property
    def estado(self):
        return self.__estado

    @estado.setter
    def estado(self, valor):
        self.__estado = valor

    @staticmethod
    def obtener_servicios(cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.cod_servicios,
                s.nombre_servicio,
                s.costo_base,
                s.estado,
                ds.cod_det_servicio,
                ds.costo_final,
                ds.descripcion_especifica,
                ds.fecha_realizacion,
                ds.placa,
                v.estado AS estado_vehiculo
            FROM servicios s
            LEFT JOIN det_servicios ds ON ds.cod_servicios = s.cod_servicios
            LEFT JOIN vehiculo v ON v.placa = ds.placa
            WHERE s.estado IN ('Activo', 'Finalizado')
            ORDER BY s.cod_servicios DESC
        """)
        rows = cursor.fetchall()
        if cedula_usuario:
            Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=9)
        cursor.close()
        conexion.close()
        return rows

    @staticmethod
    def obtener_vehiculos_disponibles():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT placa, estado
            FROM vehiculo
            WHERE estado IN ('Disponible')
            ORDER BY placa ASC
        """)
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return filas

    @staticmethod
    def existe_vehiculo(placa):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT placa
                FROM vehiculo
                WHERE placa = %s
                LIMIT 1
            """, (placa,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_costo_final(cod_servicios):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT costo_final
                FROM det_servicios
                WHERE cod_servicios = %s
                LIMIT 1
            """, (cod_servicios,))
            fila = cursor.fetchone()
            return fila["costo_final"] if fila else None
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar(nombre_servicio, costo_base, costo_final, descripcion_especifica, fecha_realizacion, placa,cedula_usuario=None):
        valido, errores = ValidacionServicios.validar_servicio(
            nombre_servicio,
            costo_base,
            costo_final,
            descripcion_especifica,
            fecha_realizacion,
            placa,
            costo_final_obligatorio=False
        )

        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}

        if not Servicios.existe_vehiculo(placa):
            return {"status": False, "mensaje": "La placa seleccionada no existe en la tabla vehiculo."}

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False

            cursor.execute("""
                INSERT INTO servicios (nombre_servicio, costo_base, estado)
                VALUES (%s, %s, %s)
            """, (nombre_servicio, costo_base, 'Activo'))

            cod_servicios = cursor.lastrowid

            cursor.execute("""
                INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios)
                VALUES (%s, %s, %s, %s, %s)
            """, (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios))

            cursor.execute("""
                UPDATE vehiculo
                SET estado = 'Servicio'
                WHERE placa = %s
            """, (placa,))

            conexion.commit()
            if cedula_usuario:
                                            Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=9)
            return {"status": True, "mensaje": "Servicio registrado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al guardar el servicio: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(cod_servicios, nombre_servicio, costo_base, costo_final, descripcion_especifica, fecha_realizacion, placa,cedula_usuario=None):
        valido, errores = ValidacionServicios.validar_servicio(
            nombre_servicio,
            costo_base,
            costo_final,
            descripcion_especifica,
            fecha_realizacion,
            placa,
            costo_final_obligatorio=False
        )

        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}

        if not Servicios.existe_vehiculo(placa):
            return {"status": False, "mensaje": "La placa seleccionada no existe en la tabla vehiculo."}

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False

            cursor.execute("""
                SELECT ds.placa
                FROM servicios s
                LEFT JOIN det_servicios ds ON ds.cod_servicios = s.cod_servicios
                WHERE s.cod_servicios = %s
                LIMIT 1
            """, (cod_servicios,))
            actual = cursor.fetchone()
            placa_anterior = actual[0] if actual else None

            cursor.execute("""
                UPDATE servicios
                SET nombre_servicio = %s,
                    costo_base = %s
                WHERE cod_servicios = %s
            """, (nombre_servicio, costo_base, cod_servicios))

            cursor.execute("""
                UPDATE det_servicios
                SET costo_final = %s,
                    descripcion_especifica = %s,
                    fecha_realizacion = %s,
                    placa = %s
                WHERE cod_servicios = %s
            """, (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios))

            if placa_anterior and placa_anterior != placa:
                cursor.execute("UPDATE vehiculo SET estado = 'Disponible' WHERE placa = %s", (placa_anterior,))
                cursor.execute("UPDATE vehiculo SET estado = 'Servicio' WHERE placa = %s", (placa,))

            conexion.commit()
            if cedula_usuario:
                                                        Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=9)
            return {"status": True, "mensaje": "Servicio actualizado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al actualizar el servicio: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def inactivar(cod_servicios,cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False
            cursor.execute("""
                UPDATE servicios
                SET estado = 'Inactivo'
                WHERE cod_servicios = %s
            """, (cod_servicios,))
            conexion.commit()
            if cedula_usuario:
                                  Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=9)
            return {"status": True, "mensaje": "Servicio inactivado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al inactivar el servicio: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def finalizar(cod_servicios, placa, cedula_usuario=None, costo_final=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            conexion.autocommit = False

            if costo_final is not None and str(costo_final).strip() != '':
                cursor.execute("""
                    UPDATE det_servicios
                    SET costo_final = %s
                    WHERE cod_servicios = %s
                """, (costo_final, cod_servicios))

            cursor.execute("""
                SELECT costo_final
                FROM det_servicios
                WHERE cod_servicios = %s
                LIMIT 1
            """, (cod_servicios,))
            fila = cursor.fetchone()

            if not fila or fila[0] is None:
                return {"status": False, "mensaje": "Debe registrar el costo final antes de finalizar el servicio."}

            cursor.execute("""
                UPDATE servicios
                SET estado = 'Finalizado'
                WHERE cod_servicios = %s
            """, (cod_servicios,))

            cursor.execute("""
                UPDATE vehiculo
                SET estado = 'Disponible'
                WHERE placa = %s
            """, (placa,))

            conexion.commit()
            if cedula_usuario:
                Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=9)
            return {"status": True, "mensaje": "Servicio finalizado y vehículo reactivado."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al finalizar el servicio: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_vehiculos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT placa
            FROM vehiculo
            ORDER BY placa ASC
        """)
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return filas

    @staticmethod
    def filtrar_reporte(cod_servicio, nombre_servicio, estado, placa):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.cod_servicios,
                s.nombre_servicio,
                s.costo_base,
                s.estado,
                ds.cod_det_servicio,
                ds.costo_final,
                ds.descripcion_especifica,
                ds.fecha_realizacion,
                ds.placa,
                v.estado AS estado_vehiculo
            FROM servicios s
            LEFT JOIN det_servicios ds ON ds.cod_servicios = s.cod_servicios
            LEFT JOIN vehiculo v ON v.placa = ds.placa
            WHERE (%s = '' OR s.cod_servicios = %s)
              AND (%s = '' OR s.nombre_servicio LIKE %s)
              AND (%s = '' OR s.estado = %s)
              AND (%s = '' OR ds.placa = %s)
            ORDER BY s.cod_servicios DESC
        """, (
            cod_servicio, cod_servicio,
            nombre_servicio, f"%{nombre_servicio}%",
            estado, estado,
            placa, placa
        ))
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return filas

    @staticmethod
    def obtener_servicio_por_codigo(cod_servicios):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.cod_servicios,
                s.nombre_servicio,
                s.costo_base,
                s.estado,
                ds.cod_det_servicio,
                ds.costo_final,
                ds.descripcion_especifica,
                ds.fecha_realizacion,
                ds.placa,
                v.estado AS estado_vehiculo
            FROM servicios s
            LEFT JOIN det_servicios ds ON ds.cod_servicios = s.cod_servicios
            LEFT JOIN vehiculo v ON v.placa = ds.placa
            WHERE s.cod_servicios = %s
            LIMIT 1
        """, (cod_servicios,))
        fila = cursor.fetchone()
        cursor.close()
        conexion.close()
        return fila