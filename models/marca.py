from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora # 1. Importamos la bitácora

class Marca:
    # ==========================================
    #   MÉTODOS DE ESCRITURA
    # ==========================================

    @staticmethod
    def guardar(nombre, estado, id_usuario_sesion):
        # 1. Validación de Backend
        try:
            Marca.__validar_datos(nombre)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO marca (nombre_marca, estado) VALUES (%s, %s)"
            cursor.execute(sql, (nombre.strip(), estado))
            
            # REGISTRO EN BITÁCORA: Acción 1 (Guardar), Módulo 4 (Marcas)
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=6)
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"La marca '{nombre}' ya está registrada.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def actualizar(id, nombre, estado, id_usuario_sesion):
        # 1. Validación de Backend
        try:
            Marca.__validar_datos(nombre)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE marca SET nombre_marca=%s, estado=%s WHERE cod_marca=%s"
            cursor.execute(sql, (nombre.strip(), estado, id))
            
            # REGISTRO EN BITÁCORA: Acción 2 (Actualizar), Módulo 4 (Marcas)
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=6)
            
            conexion.commit()
            return True
        except Error as e:
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def eliminar(id, id_usuario_sesion):
        """IMPLEMENTACIÓN DE ELIMINADO LÓGICO"""
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE marca SET estado = 'Inactivo' WHERE cod_marca = %s"
            cursor.execute(sql, (id,))
            
            # REGISTRO EN BITÁCORA: Acción 3 (Eliminar/Inactivar), Módulo 4 (Marcas)
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=6)
            
            conexion.commit()
            return True
        except Error:
            return False
        finally:
            conexion.close()

    # ==========================================
    #   MÉTODOS DE CONSULTA
    # ==========================================

    @staticmethod
    def obtener_todas():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM marca WHERE estado != 'Inactivo' ORDER BY nombre_marca ASC")
        marcas = cursor.fetchall()
        conexion.close()
        return marcas

    @staticmethod
    def obtener_activas():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM marca WHERE estado = 'Activo' ORDER BY nombre_marca ASC")
        marcas = cursor.fetchall()
        conexion.close()
        return marcas

    # ==========================================
    #   MÉTODOS PRIVADOS (ENCAPSULAMIENTO)
    # ==========================================

    @staticmethod
    def __validar_datos(nombre):
        if not nombre or len(nombre.strip()) < 2:
            raise ValueError("El nombre de la marca debe tener al menos 2 caracteres.")
        if len(nombre) > 50:
            raise ValueError("El nombre de la marca es demasiado largo.")