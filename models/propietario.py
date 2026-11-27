from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora # Importamos la bitácora
import re 

class Propietario:
    # ==========================================
    #   MÉTODOS DE ESCRITURA
    # ==========================================

    @staticmethod
    def guardar(cedula, razon_social, telefono, correo, direccion, tipo, estado, id_usuario_sesion):
        try:
            # Forzamos que el estado siempre sea Activo al guardar
            estado_fijo = "Activo"
            Propietario.__validar_datos(cedula, razon_social, correo, telefono)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = """INSERT INTO propietario (cedula_propietario, razon_social, telefono, correo, direccion, tipo, estado, fecha_registro) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""
            cursor.execute(sql, (cedula.strip(), razon_social.strip(), telefono.strip(), 
                                correo.strip().lower(), direccion.strip(), tipo, estado_fijo))
            
            Bitacora.registrar(id_usuario_sesion, cod_accion=1, cod_modulo=16)
            conexion.commit()
            return True
        except Error as e:
            if e.errno == 1062:
                raise Exception(f"La cédula o RIF '{cedula}' ya se encuentra registrado.")
            raise Exception(f"Error en la base de datos: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def actualizar(cedula, razon_social, telefono, correo, direccion, tipo, estado, id_usuario_sesion):
        try:
            Propietario.__validar_datos(cedula, razon_social, correo, telefono)
        except ValueError as e:
            raise Exception(f"Validación: {str(e)}")

        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = """UPDATE propietario SET razon_social=%s, telefono=%s, correo=%s, direccion=%s, tipo=%s, estado='Activo' 
                     WHERE cedula_propietario=%s"""
            cursor.execute(sql, (razon_social.strip(), telefono.strip(), correo.strip().lower(), 
                                direccion.strip(), tipo, cedula))
            Bitacora.registrar(id_usuario_sesion, cod_accion=3, cod_modulo=16)
            conexion.commit()
            return True
        except Error as e:
            raise Exception(f"Error al actualizar: {str(e)}")
        finally:
            conexion.close()

    @staticmethod
    def eliminar(cedula, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE propietario SET estado = 'Inactivo' WHERE cedula_propietario = %s"
            cursor.execute(sql, (cedula,))
            
            # REGISTRO EN BITÁCORA: Acción 3 (Eliminar/Inactivar)
            Bitacora.registrar(id_usuario_sesion, cod_accion=4, cod_modulo=16)
            
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
    def obtener_todos():
        """Obtiene todos los propietarios usando la VISTA resumen"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            # Ahora consultamos a la VISTA
            cursor.execute("SELECT * FROM vw_propietarios_resumen ORDER BY razon_social ASC")
            propietarios = cursor.fetchall()
            return propietarios
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def buscar_por_cedula(cedula):
        """Obtiene un propietario específico por su ID único"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT * FROM propietario WHERE cedula_propietario = %s AND estado != 'Inactivo'"
        cursor.execute(sql, (cedula,))
        propietario = cursor.fetchone()
        conexion.close()
        return propietario

    @staticmethod
    def obtener_flota_por_propietario(cedula):
        """Obtiene los vehículos de un dueño usando la VISTA de detalles"""
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            # Consultamos directamente a la vista
            sql = "SELECT * FROM vw_vehiculos_propietarios_detalle WHERE cedula_propietario = %s"
            cursor.execute(sql, (cedula,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    # ==========================================
    #   MÉTODOS PRIVADOS (ENCAPSULAMIENTO)
    # ==========================================

    @staticmethod
    def __validar_datos(cedula, razon_social, correo, telefono):
        """Privado: Valida reglas de negocio del propietario."""
        # Validar Cédula (mínimo 7 caracteres)
        if not cedula or len(cedula.strip()) < 6:
            raise ValueError("La cédula o RIF es inválido o demasiado corto.")
        
        # Validar Nombre / Razón Social
        if not razon_social or len(razon_social.strip()) < 3:
            raise ValueError("La razón social debe tener al menos 3 caracteres.")
        
        # Validar Correo Electrónico (Regex)
        regex_correo = r'^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        if not re.match(regex_correo, correo.strip()):
            raise ValueError("El formato del correo electrónico es inválido.")
        
        # Validar Teléfono (que no esté vacío)
        if not telefono or len(telefono.strip()) < 10:
            raise ValueError("El número telefónico debe tener al menos 10 dígitos.")