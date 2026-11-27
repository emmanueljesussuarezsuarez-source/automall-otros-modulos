from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora

class Rol:

    @staticmethod
    def guardar(nombre, descripcion, estatus, id_usuario_sesion):
       
        try:
            Rol.__validar_datos(nombre, descripcion)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO t_rol (nombre_rol, descripcion_rol, estatus) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre.strip(), descripcion.strip(), estatus))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=27) 
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El rol '{nombre}' ya se encuentra registrado.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(id_rol, nombre, descripcion, estatus, id_usuario_sesion):
        
        try:
            Rol.__validar_datos(nombre, descripcion)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE t_rol SET nombre_rol=%s, descripcion_rol=%s, estatus=%s WHERE cod_rol=%s"
            cursor.execute(sql, (nombre.strip(), descripcion.strip(), estatus, id_rol))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=27)
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El rol '{nombre}' ya existe, intente con otro nombre.")
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(id_rol, id_usuario_sesion):
       
        conexion = ConexionBD.obtener_conexion_seguridad()
        try:
            cursor = conexion.cursor()
           
            sql = "UPDATE t_rol SET estatus = 0 WHERE cod_rol = %s"
            cursor.execute(sql, (id_rol,))
            
           
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=27)
            
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
        # Traemos todos, incluso los inactivos si deseas gestionarlos, o puedes filtrar WHERE estatus = 1
        sql = "SELECT * FROM t_rol WHERE estatus = 1 ORDER BY cod_rol ASC"
        cursor.execute(sql)
        roles = cursor.fetchall()
        cursor.close()
        conexion.close()
        return roles

    

    @staticmethod
    def __validar_datos(nombre, descripcion):
       
        if not nombre or len(nombre.strip()) < 2:
            raise ValueError("El nombre del rol debe tener al menos 2 caracteres.")
        
        if len(nombre) > 50:
            raise ValueError("El nombre del rol es demasiado largo (máximo 50 caracteres).")
            
        if descripcion and len(descripcion) > 100:
            raise ValueError("La descripción excede el límite de 100 caracteres.")