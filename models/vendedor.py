from models.db import ConexionBD
from utils.validaciones import ValidacionUsuario
from werkzeug.security import generate_password_hash
from models.bitacora import Bitacora

class Vendedor: 
    def __init__(self, cedula, nombre, apellido, telefono, direccion, correo, password, foto="default.png", cod_rol=3):
        self.cedula = cedula
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.direccion = direccion
        self.correo = correo
        self.password = password  
        self.foto = foto
        self.cod_rol = cod_rol
        self.estado = 1

    @staticmethod
    def verificar_existencia(cedula, correo, cedula_actual=None):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        
        if cedula_actual is None:
            sql = "SELECT cedula_usuario, correo FROM t_usuario WHERE cedula_usuario = %s OR correo = %s"
            cursor.execute(sql, (cedula, correo))
        else:
            sql = "SELECT correo FROM t_usuario WHERE correo = %s AND cedula_usuario != %s"
            cursor.execute(sql, (correo, cedula_actual))
            
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado

    def guardar(self, cedula_usuario=None):
        err1 = ValidacionUsuario.validar_cedula_formato(self.cedula)
        err2 = ValidacionUsuario.validar_nombre_apellido(self.nombre, "Nombre")
        err3 = ValidacionUsuario.validar_nombre_apellido(self.apellido, "Apellido")
        err4 = ValidacionUsuario.validar_telefono(self.telefono)
        err5 = ValidacionUsuario.validar_formato_correo(self.correo)
        err6 = ValidacionUsuario.validar_direccion(self.direccion)
        err7 = ValidacionUsuario.validar_password_segura(self.password)
            
        err = err1 or err2 or err3 or err4 or err5 or err6 or err7
        
        if err:
            return {"status": False, "mensaje": err}

        existe = self.verificar_existencia(self.cedula, self.correo)
        if existe:
            if str(existe.get('cedula_usuario')) == str(self.cedula):
                return {"status": False, "mensaje": "La cédula ya se encuentra registrada."}
            if existe.get('correo') == self.correo:
                return {"status": False, "mensaje": "El correo ya está en uso por otro usuario."}

        password_hasheada = generate_password_hash(self.password)

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            sql = """
                INSERT INTO t_usuario 
                (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, foto, estado, cod_rol) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (self.cedula, self.nombre, self.apellido, self.telefono,
                   self.direccion, self.correo, password_hasheada, self.foto, 
                   self.estado, self.cod_rol)
            cursor.execute(sql, val)
            conexion.commit()
            
            if cedula_usuario:
                Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=18)
                
            cursor.close()
            conexion.close()
            return {"status": True, "mensaje": "Vendedor registrado exitosamente."}
        except Exception as e:
            return {"status": False, "mensaje": f"Error en BD: {str(e)}"}

    @staticmethod
    def obtener_todos(cedula_usuario=None):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre_rol 
            FROM t_usuario u
            JOIN t_rol r ON u.cod_rol = r.cod_rol
            WHERE u.cod_rol = 3
            ORDER BY u.nombre, u.apellido
        """)
        vendedores = cursor.fetchall()
        
        if cedula_usuario:
            Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=18)
            
        cursor.close()
        conexion.close()
        return vendedores

    @staticmethod
    def obtener_por_cedula(cedula):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre_rol 
            FROM t_usuario u
            JOIN t_rol r ON u.cod_rol = r.cod_rol
            WHERE u.cedula_usuario = %s AND u.cod_rol = 3
        """, (cedula,))
        vendedor = cursor.fetchone()
        cursor.close()
        conexion.close()
        return vendedor

    @staticmethod
    def actualizar(cedula, nombre, apellido, telefono, direccion, correo, cedula_usuario=None):
        err = (ValidacionUsuario.validar_nombre_apellido(nombre, "Nombre") or
               ValidacionUsuario.validar_nombre_apellido(apellido, "Apellido") or
               ValidacionUsuario.validar_telefono(telefono) or
               ValidacionUsuario.validar_formato_correo(correo) or
               ValidacionUsuario.validar_direccion(direccion))
        
        if err:
            return {"status": False, "mensaje": err}

        existe = Vendedor.verificar_existencia(None, correo, cedula_actual=cedula)
        if existe:
            return {"status": False, "mensaje": "El correo ya está siendo usado por otro usuario."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            sql = """
                UPDATE t_usuario 
                SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, correo = %s
                WHERE cedula_usuario = %s AND cod_rol = 3
            """
            cursor.execute(sql, (nombre, apellido, telefono, direccion, correo, cedula))
            conexion.commit()
            
            if cedula_usuario:
                Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=18)
                
            cursor.close()
            conexion.close()
            return {"status": True, "mensaje": "Vendedor actualizado correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def cambiar_estado(cedula, estado, cedula_usuario=None):
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE t_usuario SET estado = %s 
                WHERE cedula_usuario = %s AND cod_rol = 3
            """, (estado, cedula))
            conexion.commit()
            
            if cedula_usuario:
                Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=18)
                
            cursor.close()
            conexion.close()
            return True
        except Exception as e:
            print(f"Error al cambiar estado: {e}")
            return False