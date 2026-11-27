from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora # 1. Importamos la bitácora

class Modelo:
    # ==========================================
    #   MÉTODOS DE ESCRITURA
    # ==========================================

    @staticmethod
    def guardar(nombre, estado, cod_marca, id_usuario_sesion):
        # 1. Validación de Backend
        try:
            Modelo.__validar_datos(nombre, cod_marca)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO modelo (nombre_modelo, estado, cod_marca) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre.strip(), estado, cod_marca))
            
            # REGISTRO EN BITÁCORA: Acción 1 (Guardar), Módulo 5 (Modelos)
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=7)
            
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"El modelo '{nombre}' ya existe para esta marca.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def actualizar(id, nombre, estado, cod_marca, id_usuario_sesion):
        # 1. Validación de Backend
        try:
            Modelo.__validar_datos(nombre, cod_marca)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE modelo SET nombre_modelo=%s, estado=%s, cod_marca=%s WHERE cod_modelo=%s"
            cursor.execute(sql, (nombre.strip(), estado, cod_marca, id))
            
            # REGISTRO EN BITÁCORA: Acción 2 (Actualizar), Módulo 5 (Modelos)
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=7)
            
            conexion.commit()
            return True
        except Error as e:
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def eliminar(id, id_usuario_sesion):
        """IMPLEMENTACIÓN DE ELIMINADO LÓGICO CON BITÁCORA"""
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            # En lugar de DELETE, cambiamos el estado a 'Inactivo'
            sql = "UPDATE modelo SET estado = 'Inactivo' WHERE cod_modelo = %s"
            cursor.execute(sql, (id,))
            
            # REGISTRO EN BITÁCORA: Acción 3 (Eliminar/Inactivar), Módulo 5 (Modelos)
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=7)
            
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
        """Obtiene modelos activos (JOIN con Marca)"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        # Filtramos para no mostrar los eliminados lógicamente
        sql = """
            SELECT m.*, ma.nombre_marca 
            FROM modelo m 
            INNER JOIN marca ma ON m.cod_marca = ma.cod_marca
            WHERE m.estado != 'Inactivo'
            ORDER BY ma.nombre_marca, m.nombre_modelo ASC
        """
        cursor.execute(sql)
        modelos = cursor.fetchall()
        conexion.close()
        return modelos

    @staticmethod
    def obtener_por_marca(cod_marca):
        """Obtiene modelos específicos de una marca (para selects dinámicos)"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT * FROM modelo WHERE cod_marca = %s AND estado = 'Activo' AND estado != 'Inactivo'"
        cursor.execute(sql, (cod_marca,))
        res = cursor.fetchall()
        conexion.close()
        return res

    # ==========================================
    #   MÉTODOS PRIVADOS (ENCAPSULAMIENTO)
    # ==========================================

    @staticmethod
    def __validar_datos(nombre, cod_marca):
        """Privado: Valida reglas de negocio del modelo."""
        if not nombre or len(nombre.strip()) < 1:
            raise ValueError("El nombre del modelo no puede estar vacío.")
        
        if not cod_marca or int(cod_marca) <= 0:
            raise ValueError("Debe seleccionar una marca válida.")
        
        if len(nombre) > 50:
            raise ValueError("El nombre del modelo es demasiado largo.")