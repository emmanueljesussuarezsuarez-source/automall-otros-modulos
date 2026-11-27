from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora

class MetodoPago:
   
    @staticmethod
    def guardar(nombre_metodo, requiere_referencia, estado, id_usuario_sesion):
       
        try:
            MetodoPago.__validar_datos(nombre_metodo)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion() 
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO metodo_pago (nombre_metodo, requiere_referencia, estado) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre_metodo.strip(), requiere_referencia, estado))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=29) 
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El método de pago '{nombre_metodo}' ya se encuentra registrado.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(cod_metodo, nombre_metodo, requiere_referencia, estado, id_usuario_sesion):
        
        try:
            MetodoPago.__validar_datos(nombre_metodo)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE metodo_pago SET nombre_metodo=%s, requiere_referencia=%s, estado=%s WHERE cod_metodo=%s"
            cursor.execute(sql, (nombre_metodo.strip(), requiere_referencia, estado, cod_metodo))
            
            
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=29)
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El método '{nombre_metodo}' ya existe, intente con otro nombre.")
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(cod_metodo, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            
            sql = "UPDATE metodo_pago SET estado = 'Inactivo' WHERE cod_metodo = %s"
            cursor.execute(sql, (cod_metodo,))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=29)
            
            conexion.commit()
            return True
        except Error:
            return False
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT * FROM metodo_pago ORDER BY cod_metodo ASC"
        cursor.execute(sql)
        metodos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return metodos

   
    @staticmethod
    def __validar_datos(nombre_metodo):
        if not nombre_metodo or len(nombre_metodo.strip()) < 2:
            raise ValueError("El nombre del método debe tener al menos 2 caracteres.")
        
        if len(nombre_metodo) > 50:
            raise ValueError("El nombre del método es demasiado largo (máximo 50 caracteres).")