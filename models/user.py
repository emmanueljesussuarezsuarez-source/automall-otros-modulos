import os
from models.db import ConexionBD
from models.bitacora import Bitacora
from utils.validaciones import ValidacionUsuario
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


class Usuario:
    def __init__(self, cedula, nombre, apellido, telefono, direccion, correo, password, foto, cod_rol=4):
        self._cedula = cedula
        self._nombre = nombre
        self._apellido = apellido
        self._telefono = telefono
        self._direccion = direccion
        self._correo = correo
        self._password = password
        self._foto = foto
        self._cod_rol = cod_rol

    @property
    def cedula(self): return self._cedula
    @cedula.setter
    def cedula(self, valor): self._cedula = valor

    @property
    def nombre(self): return self._nombre
    @nombre.setter
    def nombre(self, valor): self._nombre = valor

    @property
    def apellido(self): return self._apellido
    @apellido.setter
    def apellido(self, valor): self._apellido = valor

    @property
    def telefono(self): return self._telefono
    @telefono.setter
    def telefono(self, valor): self._telefono = valor

    @property
    def direccion(self): return self._direccion
    @direccion.setter
    def direccion(self, valor): self._direccion = valor

    @property
    def correo(self): return self._correo
    @correo.setter
    def correo(self, valor): self._correo = valor

    @property
    def password(self): return self._password
    @password.setter
    def password(self, valor): self._password = valor

    @property
    def foto(self): return self._foto
    @foto.setter
    def foto(self, valor): self._foto = valor

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def verificar_password(password_guardada, password_ingresada):
        if not password_guardada:
            return False
        try:
            if check_password_hash(password_guardada, password_ingresada):
                return True
        except Exception:
            pass
        return password_guardada == password_ingresada

    @staticmethod
    def verificar_existencia(cedula, correo, es_nuevo=True, cedula_actual=None):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)

        if es_nuevo:
            sql = "SELECT cedula_usuario, correo FROM t_usuario WHERE cedula_usuario = %s OR correo = %s"
            cursor.execute(sql, (cedula, correo))
        else:
            sql = "SELECT correo FROM t_usuario WHERE correo = %s AND cedula_usuario != %s"
            cursor.execute(sql, (correo, cedula_actual))

        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado

    @staticmethod
    def obtener_roles_disponibles():
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT cod_rol, nombre_rol FROM t_rol ORDER BY cod_rol ASC")
            roles = cursor.fetchall()
            cursor.close()
            conexion.close()
            return roles
        except Exception:
            return []

    @staticmethod
    def registrar_usuario_completo(form_data, files_data, cedula_usuario_registro):
        cedula = form_data.get('cedula')
        nombre = form_data.get('nombre')
        apellido = form_data.get('apellido')
        telefono = form_data.get('telefono')
        direccion = form_data.get('direccion')
        correo = form_data.get('email')
        password = form_data.get('password')
        cod_rol = form_data.get('cod_rol', 4)
        
        foto = files_data.get('foto_perfil')
        nombre_foto = "default.png"

        nuevo_usuario = Usuario(
            cedula, nombre, apellido, telefono, direccion, correo, password, nombre_foto, cod_rol=cod_rol
        )

        resultado_db = nuevo_usuario.guardar()

        if not resultado_db['status']:
            return resultado_db

        if cedula_usuario_registro:
            try:
                Bitacora.registrar(
                    cedula_usuario=cedula_usuario_registro,
                    cod_accion=1,  
                    cod_modulo=1   
                )
            except Exception:
                pass

        if foto and foto.filename != '':
            try:
                extension = os.path.splitext(foto.filename)[1]
                nombre_foto = secure_filename(f"{cedula}{extension}")
                
                ruta_guardado = os.path.join('static', 'uploads', 'perfiles', nombre_foto)
                os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
                foto.save(ruta_guardado)
                
                conexion = ConexionBD.obtener_conexion_seguridad()
                cursor = conexion.cursor()
                cursor.execute("UPDATE t_usuario SET foto = %s WHERE cedula_usuario = %s", (nombre_foto, cedula))
                conexion.commit()
                cursor.close()
                conexion.close()
            except Exception as e:
                return {"status": True, "mensaje": f"Usuario creado, pero hubo un error guardando la foto: {str(e)}"}

        return {"status": True, "mensaje": "Usuario y perfil registrados exitosamente."}

    @staticmethod
    def actualizar(cedula_usuario, nombre, apellido, telefono, direccion, correo, cedula_usuario_session, cod_rol=None):
        err = ValidacionUsuario.validar_nombre_apellido(nombre, "Nombre") or \
              ValidacionUsuario.validar_nombre_apellido(apellido, "Apellido") or \
              ValidacionUsuario.validar_telefono(telefono) or \
              ValidacionUsuario.validar_formato_correo(correo) or \
              ValidacionUsuario.validar_direccion(direccion)

        if err:
            return {"status": False, "mensaje": err}

        existe = Usuario.verificar_existencia(None, correo, es_nuevo=False, cedula_actual=cedula_usuario)
        if existe:
            return {"status": False, "mensaje": "El correo ya está siendo usado por otro usuario."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            
            if cod_rol:
                sql = """
                    UPDATE t_usuario
                    SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, correo = %s, cod_rol = %s
                    WHERE cedula_usuario = %s
                """
                cursor.execute(sql, (nombre, apellido, telefono, direccion, correo, cod_rol, cedula_usuario))
            else:
                sql = """
                    UPDATE t_usuario
                    SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, correo = %s
                    WHERE cedula_usuario = %s
                """
                cursor.execute(sql, (nombre, apellido, telefono, direccion, correo, cedula_usuario))
                
            conexion.commit()
            cursor.close()
            conexion.close()

            if cedula_usuario_session:
                try:
                    Bitacora.registrar(
                        cedula_usuario=cedula_usuario_session,
                        cod_accion=3,  
                        cod_modulo=1
                    )
                except Exception:
                    pass

            return {"status": True, "mensaje": "Usuario actualizado correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def actualizar_datos_perfil(cedula_usuario, telefono, direccion, correo, foto_perfil=None):
        err = ValidacionUsuario.validar_telefono(telefono) or \
              ValidacionUsuario.validar_direccion(direccion) or \
              ValidacionUsuario.validar_formato_correo(correo)

        if err:
            return {"status": False, "mensaje": err}

        existe = Usuario.verificar_existencia(None, correo, es_nuevo=False, cedula_actual=cedula_usuario)
        if existe:
            return {"status": False, "mensaje": "El correo ya está siendo usado por otro usuario."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()

            if foto_perfil and foto_perfil.filename != '':
                extension = os.path.splitext(foto_perfil.filename)[1].lower()
                if extension not in ['.jpg', '.jpeg', '.png']:
                    cursor.close()
                    conexion.close()
                    return {"status": False, "mensaje": "Formato de foto no válido. Use JPG, JPEG o PNG."}

                nombre_foto = secure_filename(f"{cedula_usuario}{extension}")
                ruta_guardado = os.path.join('static', 'uploads', 'perfiles', nombre_foto)
                os.makedirs(os.path.dirname(ruta_guardado), exist_ok=True)
                foto_perfil.save(ruta_guardado)

                sql = """
                    UPDATE t_usuario
                    SET telefono = %s, direccion = %s, correo = %s, foto = %s
                    WHERE cedula_usuario = %s
                """
                cursor.execute(sql, (telefono, direccion, correo, nombre_foto, cedula_usuario))
            else:
                sql = """
                    UPDATE t_usuario
                    SET telefono = %s, direccion = %s, correo = %s
                    WHERE cedula_usuario = %s
                """
                cursor.execute(sql, (telefono, direccion, correo, cedula_usuario))

            conexion.commit()
            cursor.close()
            conexion.close()

            try:
                Bitacora.registrar(
                    cedula_usuario=cedula_usuario,
                    cod_accion=13,  
                    cod_modulo=1
                )
            except Exception:
                pass

            return {"status": True, "mensaje": "Datos personales actualizados correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def cambiar_password(cedula_usuario, password_actual, nueva_password, confirmar_password):
        if not password_actual or not nueva_password or not confirmar_password:
            return {"status": False, "mensaje": "Debe completar todos los campos de contraseña."}

        if nueva_password != confirmar_password:
            return {"status": False, "mensaje": "La nueva contraseña y su confirmación no coinciden."}

        err = ValidacionUsuario.validar_password_segura(nueva_password)
        if err:
            return {"status": False, "mensaje": err}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT password FROM t_usuario WHERE cedula_usuario = %s LIMIT 1", (cedula_usuario,))
            usuario = cursor.fetchone()

            if not usuario:
                cursor.close()
                conexion.close()
                return {"status": False, "mensaje": "Usuario no encontrado."}

            if not Usuario.verificar_password(usuario["password"], password_actual):
                cursor.close()
                conexion.close()
                return {"status": False, "mensaje": "La contraseña actual es incorrecta."}

            cursor = conexion.cursor()
            password_hash = Usuario.hash_password(nueva_password)
            cursor.execute("UPDATE t_usuario SET password = %s WHERE cedula_usuario = %s", (password_hash, cedula_usuario))
            conexion.commit()
            cursor.close()
            conexion.close()

            try:
                Bitacora.registrar(
                    cedula_usuario=cedula_usuario,
                    cod_accion=13, 
                    cod_modulo=1
                )
            except Exception:
                pass

            return {"status": True, "mensaje": "Contraseña actualizada correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def obtener_preguntas_banco():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT cod_preguntas, nombre_preguntas FROM t_banco_preguntas WHERE estado = 0 ORDER BY nombre_preguntas")
        preguntas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return preguntas

    @staticmethod
    def _validar_preguntas_existen(cod_pregunta_1, cod_pregunta_2):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT cod_preguntas FROM t_banco_preguntas WHERE estado = 0 AND cod_preguntas IN (%s, %s)", (cod_pregunta_1, cod_pregunta_2))
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()

        codigos_validos = {str(f["cod_preguntas"]) for f in filas}
        return str(cod_pregunta_1) in codigos_validos and str(cod_pregunta_2) in codigos_validos

    @staticmethod
    def guardar_preguntas_seguridad(cedula_usuario, pregunta_1, respuesta_1, confirmar_respuesta_1, pregunta_2, respuesta_2, confirmar_respuesta_2):
        if not pregunta_1 or not pregunta_2 or not respuesta_1 or not respuesta_2:
            return {"status": False, "mensaje": "Debe completar las preguntas y respuestas de seguridad."}

        if respuesta_1 != confirmar_respuesta_1 or respuesta_2 != confirmar_respuesta_2:
            return {"status": False, "mensaje": "La confirmación de una o ambas respuestas no coincide."}

        if str(pregunta_1) == str(pregunta_2):
            return {"status": False, "mensaje": "Debe seleccionar dos preguntas de seguridad diferentes."}

        if not Usuario._validar_preguntas_existen(pregunta_1, pregunta_2):
            return {"status": False, "mensaje": "Una o ambas preguntas de seguridad no existen o no están activas."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT cod_repuesta FROM t_det_repuesta WHERE cedula_usuario = %s ORDER BY cod_repuesta LIMIT 2", (cedula_usuario,))
            registros = cursor.fetchall()

            cursor2 = conexion.cursor()

            if len(registros) == 0:
                cursor2.execute("INSERT INTO t_det_repuesta (respuesta, fecha_registro, cod_preguntas, cedula_usuario) VALUES (%s, CURDATE(), %s, %s)", (respuesta_1, pregunta_1, cedula_usuario))
                cursor2.execute("INSERT INTO t_det_repuesta (respuesta, fecha_registro, cod_preguntas, cedula_usuario) VALUES (%s, CURDATE(), %s, %s)", (respuesta_2, pregunta_2, cedula_usuario))
            elif len(registros) == 1:
                cursor2.execute("UPDATE t_det_repuesta SET respuesta = %s, fecha_registro = CURDATE(), cod_preguntas = %s WHERE cod_repuesta = %s", (respuesta_1, pregunta_1, registros[0]["cod_repuesta"]))
                cursor2.execute("INSERT INTO t_det_repuesta (respuesta, fecha_registro, cod_preguntas, cedula_usuario) VALUES (%s, CURDATE(), %s, %s)", (respuesta_2, pregunta_2, cedula_usuario))
            else:
                cursor2.execute("UPDATE t_det_repuesta SET respuesta = %s, fecha_registro = CURDATE(), cod_preguntas = %s WHERE cod_repuesta = %s", (respuesta_1, pregunta_1, registros[0]["cod_repuesta"]))
                cursor2.execute("UPDATE t_det_repuesta SET respuesta = %s, fecha_registro = CURDATE(), cod_preguntas = %s WHERE cod_repuesta = %s", (respuesta_2, pregunta_2, registros[1]["cod_repuesta"]))

            conexion.commit()
            cursor.close()
            cursor2.close()
            conexion.close()

            try:
                Bitacora.registrar(cedula_usuario=cedula_usuario, cod_accion=13, cod_modulo=1)
            except Exception:
                pass

            return {"status": True, "mensaje": "Preguntas de seguridad guardadas correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def validar_respuestas_seguridad(cedula_usuario, respuesta_1, respuesta_2):
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT respuesta FROM t_det_repuesta WHERE cedula_usuario = %s ORDER BY cod_repuesta LIMIT 2", (cedula_usuario,))
            registros = cursor.fetchall()
            cursor.close()
            conexion.close()

            if len(registros) < 2:
                return {"status": False, "mensaje": "No existen preguntas de seguridad registradas."}

            if registros[0]["respuesta"] != respuesta_1 or registros[1]["respuesta"] != respuesta_2:
                return {"status": False, "mensaje": "Las respuestas de seguridad no coinciden."}

            return {"status": True, "mensaje": "Respuestas de seguridad correctas."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def actualizar_preguntas_seguridad(cedula_usuario, respuesta_vieja_1, respuesta_vieja_2, pregunta_nueva_1, respuesta_nueva_1, confirmar_respuesta_nueva_1, pregunta_nueva_2, respuesta_nueva_2, confirmar_respuesta_nueva_2):
        validacion = Usuario.validar_respuestas_seguridad(cedula_usuario, respuesta_vieja_1, respuesta_vieja_2)
        if not validacion["status"]:
            return validacion

        if respuesta_nueva_1 != confirmar_respuesta_nueva_1 or respuesta_nueva_2 != confirmar_respuesta_nueva_2:
            return {"status": False, "mensaje": "La confirmación de las nuevas respuestas no coincide."}

        if str(pregunta_nueva_1) == str(pregunta_nueva_2):
            return {"status": False, "mensaje": "Debe seleccionar dos preguntas de seguridad diferentes."}

        if not Usuario._validar_preguntas_existen(pregunta_nueva_1, pregunta_nueva_2):
            return {"status": False, "mensaje": "Una o ambas preguntas de seguridad no existen o no están activas."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT cod_repuesta FROM t_det_repuesta WHERE cedula_usuario = %s ORDER BY cod_repuesta LIMIT 2", (cedula_usuario,))
            registros = cursor.fetchall()

            if len(registros) < 2:
                cursor.close()
                conexion.close()
                return {"status": False, "mensaje": "No existen suficientes preguntas para actualizar."}

            cursor2 = conexion.cursor()
            cursor2.execute("UPDATE t_det_repuesta SET respuesta = %s, fecha_registro = CURDATE(), cod_preguntas = %s WHERE cod_repuesta = %s", (respuesta_nueva_1, pregunta_nueva_1, registros[0]["cod_repuesta"]))
            cursor2.execute("UPDATE t_det_repuesta SET respuesta = %s, fecha_registro = CURDATE(), cod_preguntas = %s WHERE cod_repuesta = %s", (respuesta_nueva_2, pregunta_nueva_2, registros[1]["cod_repuesta"]))

            conexion.commit()
            cursor.close()
            cursor2.close()
            conexion.close()

            try:
                Bitacora.registrar(cedula_usuario=cedula_usuario, cod_accion=13, cod_modulo=1)
            except Exception:
                pass

            return {"status": True, "mensaje": "Preguntas de seguridad actualizadas correctamente."}
        except Exception as e:
            return {"status": False, "mensaje": str(e)}

    @staticmethod
    def obtener_todos(cedula_usuario_session=None):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_usuario WHERE estado = 1")
        usuarios = cursor.fetchall()
        cursor.close()
        conexion.close()

        if cedula_usuario_session:
            try:
                Bitacora.registrar(cedula_usuario=cedula_usuario_session, cod_accion=2, cod_modulo=1)
            except Exception:
                pass

        return usuarios

    @staticmethod
    def eliminar(cedula_usuario, cedula_usuario_session):
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            cursor.execute("UPDATE t_usuario SET estado = 0 WHERE cedula_usuario = %s", (cedula_usuario,))
            conexion.commit()
            cursor.close()
            conexion.close()

            if cedula_usuario_session:
                try:
                    Bitacora.registrar(cedula_usuario=cedula_usuario_session, cod_accion=3, cod_modulo=1)
                except Exception:
                    pass

            return True
        except:
            return False

    @staticmethod
    def obtener_por_cedula(cedula_usuario):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT u.*, r.nombre_rol
            FROM t_usuario u
            LEFT JOIN t_rol r ON u.cod_rol = r.cod_rol
            WHERE u.cedula_usuario = %s
        """
        cursor.execute(sql, (cedula_usuario,))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        return usuario

    @staticmethod
    def buscar_cliente_por_cedula(cedula):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)

        sql = """
            SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo
            FROM t_usuario
            WHERE cedula_usuario = %s AND cod_rol = 4
            LIMIT 1
        """

        cursor.execute(sql, (cedula,))
        cliente = cursor.fetchone()

        cursor.close()
        conexion.close()

        if cliente:
            return {
                'exito': True,
                'nombre_completo': f"{cliente['nombre']} {cliente['apellido']}",
                'cedula': cliente['cedula_usuario'],
                'telefono': cliente['telefono'],
                'direccion': cliente['direccion'],
                'correo': cliente['correo']
            }

        return None

    @staticmethod
    def obtener_por_rol(cod_rol):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre_rol
            FROM t_usuario u
            JOIN t_rol r ON u.cod_rol = r.cod_rol
            WHERE u.cod_rol = %s
            ORDER BY u.nombre, u.apellido
        """, (cod_rol,))
        usuarios = cursor.fetchall()
        cursor.close()
        conexion.close()
        return usuarios

    @staticmethod
    def cambiar_estado(cedula, estado):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("UPDATE t_usuario SET estado = %s WHERE cedula_usuario = %s", (estado, cedula))
        conexion.commit()
        cursor.close()
        conexion.close()
        return True

    def guardar(self):
        err = ValidacionUsuario.validar_cedula_formato(self.cedula) or \
              ValidacionUsuario.validar_nombre_apellido(self.nombre, "Nombre") or \
              ValidacionUsuario.validar_nombre_apellido(self.apellido, "Apellido") or \
              ValidacionUsuario.validar_telefono(self.telefono) or \
              ValidacionUsuario.validar_formato_correo(self.correo) or \
              ValidacionUsuario.validar_direccion(self.direccion) or \
              ValidacionUsuario.validar_password_segura(self.password)

        if err:
            return {"status": False, "mensaje": err}

        existe = self.verificar_existencia(self.cedula, self.correo, es_nuevo=True)
        if existe:
            if str(existe['cedula_usuario']) == str(self.cedula):
                return {"status": False, "mensaje": "La cédula ya se encuentra registrada."}
            if existe['correo'] == self.correo:
                return {"status": False, "mensaje": "El correo ya está en uso por otro usuario."}

        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
          
            sql = """
                INSERT INTO t_usuario
                (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, foto, cod_rol, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """
            password_guardada = Usuario.hash_password(self.password)
            val = (
                self.cedula, self.nombre, self.apellido,
                self.telefono, self.direccion, self.correo,
                password_guardada, self.foto, self._cod_rol
            )
            cursor.execute(sql, val)
            conexion.commit()
            cursor.close()
            conexion.close()
            return {"status": True, "mensaje": "Usuario registrado exitosamente."}
        except Exception as e:
            return {"status": False, "mensaje": f"Error en BD: {str(e)}"}