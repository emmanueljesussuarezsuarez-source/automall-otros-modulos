from models.db import ConexionBD
from utils.validaciones_taller import ValidacionTaller
from models.bitacora import Bitacora

class Taller:
    def __init__(self, cod_taller=None, nombre_taller=None, direccion=None, estado='1'):
        self.__cod_taller = cod_taller
        self.__nombre_taller = nombre_taller
        self.__direccion = direccion
        self.__estado = estado

    @property
    def cod_taller(self):
        return self.__cod_taller

    @cod_taller.setter
    def cod_taller(self, valor):
        self.__cod_taller = valor

    @property
    def nombre_taller(self):
        return self.__nombre_taller

    @nombre_taller.setter
    def nombre_taller(self, valor):
        self.__nombre_taller = valor

    @property
    def direccion(self):
        return self.__direccion

    @direccion.setter
    def direccion(self, valor):
        self.__direccion = valor

    @property
    def estado(self):
        return self.__estado

    @estado.setter
    def estado(self, valor):
        self.__estado = valor

    @staticmethod
    def obtener_todos(cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT cod_taller, nombre_taller, direccion, estado
            FROM taller
            WHERE estado = '1'
            ORDER BY cod_taller DESC
        """)
        talleres = cursor.fetchall()
        if cedula_usuario:
                    Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=10)
        cursor.close()
        conexion.close()
        return talleres

    @staticmethod
    def obtener_por_id(cod_taller):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            SELECT cod_taller, nombre_taller, direccion, estado
            FROM taller
            WHERE cod_taller = %s
        """, (cod_taller,))
        taller = cursor.fetchone()
        cursor.close()
        conexion.close()
        return taller

    @staticmethod
    def existe_nombre(nombre_taller, excluir_cod_taller=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        try:
            if excluir_cod_taller:
                cursor.execute("""
                    SELECT cod_taller
                    FROM taller
                    WHERE LOWER(nombre_taller) = LOWER(%s)
                      AND cod_taller <> %s
                    LIMIT 1
                """, (nombre_taller.strip(), excluir_cod_taller))
            else:
                cursor.execute("""
                    SELECT cod_taller
                    FROM taller
                    WHERE LOWER(nombre_taller) = LOWER(%s)
                    LIMIT 1
                """, (nombre_taller.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar(nombre_taller, direccion, estado='1', cedula_usuario=None):
        valido, errores = ValidacionTaller.validar_taller(
            nombre_taller,
            direccion,
            estado,
            existe_func=Taller.existe_nombre
        )

        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO taller (nombre_taller, direccion, estado)
                VALUES (%s, %s, %s)
            """, (nombre_taller.strip(), direccion.strip(), estado))
            conexion.commit()
            if cedula_usuario:
                                Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=10)
            return {"status": True, "mensaje": "Taller registrado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al guardar el taller: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(cod_taller, nombre_taller, direccion, estado, cedula_usuario=None):
        valido, errores = ValidacionTaller.validar_taller(
            nombre_taller,
            direccion,
            estado,
            excluir_cod_taller=cod_taller,
            existe_func=Taller.existe_nombre
        )

        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE taller
                SET nombre_taller = %s,
                    direccion = %s,
                    estado = %s
                WHERE cod_taller = %s
            """, (nombre_taller.strip(), direccion.strip(), estado, cod_taller))
            conexion.commit()
            if cedula_usuario:
                                            Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=10)
            return {"status": True, "mensaje": "Taller actualizado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al actualizar el taller: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(cod_taller, cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE taller
                SET estado = '0'
                WHERE cod_taller = %s
            """, (cod_taller,))
            conexion.commit()
            if cedula_usuario:
                      Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=10)
            return {"status": True, "mensaje": "Taller desactivado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al desactivar el taller: {str(e)}"}
        finally:
            cursor.close()
            conexion.close()