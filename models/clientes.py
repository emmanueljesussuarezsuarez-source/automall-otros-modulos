import os
import time
from werkzeug.utils import secure_filename
from models.db import ConexionBD
from utils.validaciones import ValidacionUsuario
from werkzeug.security import generate_password_hash


class ClienteModel:
    CARPETA_PERFILES = os.path.join('static', 'uploads', 'perfiles')

    def __init__(self, cedula, nombre, apellido, telefono, direccion, correo, password, foto, cod_rol=4):
        self.__cedula = cedula
        self.__nombre = nombre
        self.__apellido = apellido
        self.__telefono = telefono
        self.__direccion = direccion
        self.__correo = correo
        self.__password = password
        self.__foto = foto
        self.__cod_rol = cod_rol

    @property
    def cedula(self): return self.__cedula

    @property
    def nombre(self): return self.__nombre

    @property
    def apellido(self): return self.__apellido

    @property
    def telefono(self): return self.__telefono

    @property
    def direccion(self): return self.__direccion

    @property
    def correo(self): return self.__correo

    @property
    def password(self): return self.__password

    @property
    def foto(self): return self.__foto

    @property
    def cod_rol(self): return self.__cod_rol

    @staticmethod
    def guardar_foto_perfil(archivo, cedula):
        
        if not archivo or archivo.filename == '':
            return None

        # CP-CLIE-37 - INICIO CORRECCIÓN
        EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        extension = archivo.filename.rsplit('.', 1)[-1].lower()
        if extension not in EXTENSIONES_PERMITIDAS:
            return None
        # CP-CLIE-37 - FIN CORRECCIÓN

        nombre_unico = f"{cedula}_{int(time.time())}.{extension}"
        nombre_seguro = secure_filename(nombre_unico)
        ruta_destino = os.path.join(ClienteModel.CARPETA_PERFILES, nombre_seguro)

        os.makedirs(ClienteModel.CARPETA_PERFILES, exist_ok=True)
        archivo.save(ruta_destino)
        return f"uploads/perfiles/{nombre_seguro}"

    # Registrar-----------------------------------------------------------------------
    @staticmethod
    def verificar_existencia(cedula, correo):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT cedula_usuario, correo FROM seguridad.t_usuario WHERE cedula_usuario = %s OR correo = %s"
        cursor.execute(sql, (cedula, correo))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado

    def registrar_cliente_db(self):
        err = ValidacionUsuario.validar_cedula_formato(self.__cedula)
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_nombre_apellido(self.__nombre, "Nombre")
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_nombre_apellido(self.__apellido, "Apellido")
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_telefono(self.__telefono)
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_direccion(self.__direccion)
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_formato_correo(self.__correo)
        if err: return {"status": False, "mensaje": err}

        err = ValidacionUsuario.validar_password_segura(self.__password)
        if err: return {"status": False, "mensaje": err}

        if self.verificar_existencia(self.__cedula, self.__correo):
            return {"status": False, "mensaje": "La cédula o el correo electrónico ya se encuentran registrados."}

        try:
            hash_pwd = generate_password_hash(self.__password)

            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()

            #Procedimiento Almacenado sp_registrar_cliente
            cursor.callproc('automall.sp_registrar_cliente', (
                # CP-CLIE-36 - INICIO CORRECCIÓN
                str(self.__cedula).strip(),
                # CP-CLIE-36 - FIN CORRECCIÓN
                self.__nombre.strip(),
                self.__apellido.strip(),
                self.__telefono.strip(),
                self.__direccion.strip(),
                self.__correo.strip(),
                hash_pwd,
                self.__foto,
                '@resultado'
            ))
            cursor.execute("SELECT @resultado")
            res = cursor.fetchone()

            conexion.commit()
            cursor.close()
            conexion.close()

            if res and res[0] and res[0].startswith('ERROR'):
                return {"status": False, "mensaje": res[0].replace('ERROR: ', '')}

            return {"status": True, "mensaje": "¡Tu cuenta de cliente ha sido creada con éxito!"}

        except Exception as e:
            return {"status": False, "mensaje": f"Error interno en el servidor: {str(e)}"}

    # consultar -----------------------------------------------------------------------
    @staticmethod
    def obtener_clientes():
        #Vista SQL v_clientes_activos
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo, foto
            FROM automall.v_clientes_activos
            ORDER BY apellido ASC, nombre ASC
        """
        cursor.execute(sql)
        clientes = cursor.fetchall()
        cursor.close()
        conexion.close()
        return clientes

    @staticmethod
    def obtener_por_cedula(cedula):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo, foto
            FROM seguridad.t_usuario
            WHERE cedula_usuario = %s AND cod_rol = 4 AND estado = 1
        """
        cursor.execute(sql, (cedula,))
        cliente = cursor.fetchone()
        cursor.close()
        conexion.close()
        return cliente
# Modificar -------------------------------------------------------------------------------------------------
    @staticmethod
    def actualizar_cliente(datos):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()
        sql = """
            UPDATE seguridad.t_usuario
            SET nombre = %s, apellido = %s, telefono = %s, direccion = %s, correo = %s, foto = %s
            WHERE cedula_usuario = %s AND cod_rol = 4 AND estado = 1
        """
        valores = (
            datos['nombre'].strip(),
            datos['apellido'].strip(),
            datos['telefono'].strip(),
            datos['direccion'].strip(),
            datos['correo'].strip(),
            datos['foto'],
            datos['cedula']
        )
        cursor.execute(sql, valores)
        conexion.commit()
        filas = cursor.rowcount
        cursor.close()
        conexion.close()
        return filas > 0
# Eliminar-----------------------------------------------------------------------------------------------------
    @staticmethod
    def eliminar_cliente(cedula):
        try:
            # CP-CLIE-38 - INICIO CORRECCIÓN
            try:
                from models.citas import CitasModel
                citas = CitasModel.obtener_por_cliente(cedula)
                if citas and any(isinstance(c, dict) and c.get('estado') == 'Pendiente' for c in citas):
                    return {"status": False, "mensaje": "No se puede eliminar: el cliente posee citas activas en tránsito."}
            except Exception:
                pass
            # CP-CLIE-38 - FIN CORRECCIÓN
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor()
            sql = "UPDATE seguridad.t_usuario SET estado = 0 WHERE cedula_usuario = %s AND cod_rol = 4"
            cursor.execute(sql, (cedula,))
            conexion.commit()
            filas = cursor.rowcount
            cursor.close()
            conexion.close()
            if filas > 0:
                return {"status": True, "mensaje": "Cliente eliminado del sistema con éxito."}
            return {"status": False, "mensaje": "No se encontró el cliente o no se puede eliminar."}
        except Exception as e:
            return {"status": False, "mensaje": f"Error al eliminar: {str(e)}"}




