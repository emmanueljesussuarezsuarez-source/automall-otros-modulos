from models.db import ConexionBD
from utils.validaciones import ValidacionUsuario
from utils.validaciones_recuperacion import ValidacionesRecuperacion
from werkzeug.security import check_password_hash, generate_password_hash
from models.bitacora import Bitacora

class Auth:
    def __init__(self, cedula_usuario, nombre, apellido, telefono, direccion, correo, password):
       
        self._cedula_usuario = cedula_usuario
        self._nombre = nombre
        self._apellido = apellido
        self._telefono = telefono
        self._direccion = direccion
        self._correo = correo
        self._password = password

    

    @property
    def cedula_usuario(self):
        return self._cedula_usuario

    @cedula_usuario.setter
    def cedula_usuario(self, value):
        self._cedula_usuario = value

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, value):
        self._nombre = value

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, value):
        self._apellido = value

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, value):
        self._telefono = value

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, value):
        self._direccion = value

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, value):
        self._correo = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value


    @staticmethod
    def verificar_credenciales(correo, password):
        error_correo = ValidacionUsuario.validar_formato_correo(correo)
        if error_correo:
            return {"error": error_correo}

        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True, buffered=True)

            cursor.callproc('sp_verificar_bloqueo', [correo])
            fila_bloqueo = None
            for rs in cursor.stored_results():
                fila_bloqueo = rs.fetchone()

            if fila_bloqueo and fila_bloqueo.get('bloqueado') == 1:
                segundos = int(fila_bloqueo.get('segundos_restantes') or 0)
                minutos = segundos // 60
                segs_resto = segundos % 60
                if minutos > 0:
                    tiempo_msg = f"{minutos} minuto(s) y {segs_resto} segundo(s)"
                else:
                    tiempo_msg = f"{segs_resto} segundo(s)"
                return {"error": f"Cuenta bloqueada temporalmente por demasiados intentos fallidos. "
                                 f"Intente de nuevo en {tiempo_msg}."}

            cursor.execute(
                "SELECT cedula_usuario, nombre, cod_rol, password, foto FROM t_usuario WHERE correo = %s",
                (correo,)
            )
            usuario = cursor.fetchone()

            if not usuario:
                return None

            db_password = usuario["password"]
            if db_password.startswith(("pbkdf2:", "scrypt:")):
                password_ok = check_password_hash(db_password, password)
            else:
                password_ok = (db_password == password)

            if not password_ok:
            
                cursor2 = conexion.cursor()
                cursor2.callproc('sp_registrar_fallo', [correo])
                cursor2.close()
                conexion.commit()
                return None

            cursor2 = conexion.cursor()
            cursor2.callproc('sp_registrar_exito', [correo])
            cursor2.close()
            conexion.commit()

            usuario.pop("password", None)

            Bitacora.registrar(usuario['cedula_usuario'], cod_accion=7, cod_modulo=1)
            return usuario
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None:
                conexion.close()


    @staticmethod
    def obtener_pregunta(correo):
        error_correo = ValidacionUsuario.validar_formato_correo(correo)
        if error_correo:
            return {"error": error_correo}

        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT u.cedula_usuario, p.nombre_preguntas, p2.nombre_preguntas AS nombre_preguntas_2
                FROM t_usuario u
                INNER JOIN t_det_repuesta r ON u.cedula_usuario = r.cedula_usuario
                INNER JOIN t_banco_preguntas p ON r.cod_preguntas = p.cod_preguntas
                LEFT JOIN t_det_repuesta r2 ON u.cedula_usuario = r2.cedula_usuario AND r2.cod_preguntas <> r.cod_preguntas
                LEFT JOIN t_banco_preguntas p2 ON r2.cod_preguntas = p2.cod_preguntas
                WHERE u.correo = %s
                LIMIT 1
            """, (correo,))
            return cursor.fetchone()
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None:
                conexion.close()

    @staticmethod
    def validar_respuesta(correo, respuesta):
        error_correo = ValidacionUsuario.validar_formato_correo(correo)
        if error_correo:
            return {"error": error_correo}

        error_respuesta = ValidacionesRecuperacion.validar_respuesta_recuperacion(respuesta)
        if error_respuesta:
            return {"error": error_respuesta}

        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT u.cedula_usuario
                FROM t_usuario u
                INNER JOIN t_det_repuesta r ON u.cedula_usuario = r.cedula_usuario
                WHERE u.correo = %s AND r.respuesta = %s
            """, (correo, respuesta.strip()))
            return cursor.fetchone()
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None:
                conexion.close()

    @staticmethod
    def actualizar_password(correo, nueva_password):
        error_correo = ValidacionUsuario.validar_formato_correo(correo)
        if error_correo:
            return {"status": False, "mensaje": error_correo}

        error_pass = ValidacionesRecuperacion.validar_password_recuperacion(nueva_password)
        if error_pass:
            return {"status": False, "mensaje": error_pass}

        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(buffered=True)
            password_hash = generate_password_hash(nueva_password)
            cursor.execute(
                "UPDATE t_usuario SET password = %s WHERE correo = %s",
                (password_hash, correo)
            )
            conexion.commit()

            if cursor.rowcount > 0:
                return {"status": True, "mensaje": "Contraseña actualizada exitosamente."}
            return {"status": False, "mensaje": "No se encontró el usuario para actualizar."}
        except Exception as e:
            if conexion is not None:
                try:
                    conexion.rollback()
                except Exception:
                    pass
            return {"status": False, "mensaje": f"Error en la base de datos: {str(e)}"}
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None:
                conexion.close()