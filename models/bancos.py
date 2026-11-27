from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora

class Banco:
    # ==========================================
    #   MÉTODOS DE ESCRITURA
    # ==========================================

    @staticmethod
    def guardar(nombre_banco, estado, id_usuario_sesion):
       
        try:
            Banco.__validar_datos(nombre_banco)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion() 
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO banco (nombre_banco, estado) VALUES (%s, %s)"
            cursor.execute(sql, (nombre_banco.strip(), estado))
            
            
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=30) 
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El banco '{nombre_banco}' ya se encuentra registrado.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(cod_banco, nombre_banco, estado, id_usuario_sesion):
       
        try:
            Banco.__validar_datos(nombre_banco)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE banco SET nombre_banco=%s, estado=%s WHERE cod_banco=%s"
            cursor.execute(sql, (nombre_banco.strip(), estado, cod_banco))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=30)
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El banco '{nombre_banco}' ya existe, intente con otro nombre.")
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(cod_banco, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
           
            sql = "UPDATE banco SET estado = 'Inactivo' WHERE cod_banco = %s"
            cursor.execute(sql, (cod_banco,))
            
            
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=30)
            
            conexion.commit()
            return True
        except Error:
            return False
        finally:
            cursor.close()
            conexion.close()

    # ==========================================
    #   MÉTODOS DE CONSULTA
    # ==========================================

    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT * FROM banco ORDER BY cod_banco ASC"
        cursor.execute(sql)
        bancos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return bancos

    # ==========================================
    #   MÉTODOS PRIVADOS
    # ==========================================

    @staticmethod
    def __validar_datos(nombre_banco):
        if not nombre_banco or len(nombre_banco.strip()) < 2:
            raise ValueError("El nombre del banco debe tener al menos 2 caracteres.")
        
        if len(nombre_banco) > 50:
            raise ValueError("El nombre del banco es demasiado largo (máximo 50 caracteres).")