from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora

class Modulo:
    @staticmethod
    def guardar(nombre, estatus, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO t_modulo (nombre_modulo, estatus) VALUES (%s, %s)"
            cursor.execute(sql, (nombre.strip(), estatus))
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=25) 
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception("El módulo ya existe.")
            raise Exception(f"Error BD: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(id_modulo, nombre, estatus, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE t_modulo SET nombre_modulo=%s, estatus=%s WHERE cod_modulo=%s"
            cursor.execute(sql, (nombre.strip(), estatus, id_modulo))
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=25)
            conexion.commit()
            return True
        except Error as e:
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(id_modulo, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE t_modulo SET estatus = 0 WHERE cod_modulo = %s"
            cursor.execute(sql, (id_modulo,))
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=25)
            conexion.commit()
            return True
        except Error:
            return False
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_modulo ORDER BY cod_modulo ASC")
        modulos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return modulos