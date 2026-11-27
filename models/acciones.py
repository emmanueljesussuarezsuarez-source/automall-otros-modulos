from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora

class Accion:
    @staticmethod
    def guardar(nombre, estatus, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO t_acciones (nom_accion, estatus) VALUES (%s, %s)"
            cursor.execute(sql, (nombre.strip(), estatus))
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=26) 
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception("La acción ya existe.")
            raise Exception(f"Error BD: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(id_accion, nombre, estatus, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE t_acciones SET nom_accion=%s, estatus=%s WHERE cod_accion=%s"
            cursor.execute(sql, (nombre.strip(), estatus, id_accion))
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=26)
            conexion.commit()
            return True
        except Error as e:
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(id_accion, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE t_acciones SET estatus = 0 WHERE cod_accion = %s"
            cursor.execute(sql, (id_accion,))
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=26)
            conexion.commit()
            return True
        except Error:
            return False
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_todas():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_acciones ORDER BY cod_accion ASC")
        acciones = cursor.fetchall()
        cursor.close()
        conexion.close()
        return acciones