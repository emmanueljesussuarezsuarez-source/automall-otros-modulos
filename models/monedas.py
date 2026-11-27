from models.db import ConexionBD
from mysql.connector import Error
from models.bitacora import Bitacora


class Moneda:

    @staticmethod
    def guardar(nombre_moneda, simbolo, estado, id_usuario_sesion):
        Moneda.__validar_moneda(nombre_moneda, simbolo, estado)

        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(cod_moneda), 0) + 1 AS siguiente "
                "FROM moneda"
            )

            resultado = cursor.fetchone()
            cod_moneda = resultado[0]

            sql = """
                INSERT INTO moneda
                (cod_moneda, nombre_moneda, simbolo, estado)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (
                    cod_moneda,
                    nombre_moneda.strip(),
                    simbolo.strip() if simbolo else None,
                    estado
                )
            )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=1,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()

            if e.errno == 1062:
                raise Exception(
                    f"La moneda '{nombre_moneda}' ya se encuentra registrada."
                )

            raise Exception(
                f"Error en la base de datos: {str(e)}"
            )

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def actualizar(
        cod_moneda,
        nombre_moneda,
        simbolo,
        estado,
        id_usuario_sesion
    ):
        Moneda.__validar_moneda(nombre_moneda, simbolo, estado)

        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()

            sql = """
                UPDATE moneda
                SET nombre_moneda = %s,
                    simbolo = %s,
                    estado = %s
                WHERE cod_moneda = %s
            """

            cursor.execute(
                sql,
                (
                    nombre_moneda.strip(),
                    simbolo.strip() if simbolo else None,
                    estado,
                    cod_moneda
                )
            )

            if cursor.rowcount == 0:
                raise Exception(
                    "La moneda indicada no existe."
                )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=3,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()

            if e.errno == 1062:
                raise Exception(
                    f"La moneda '{nombre_moneda}' ya existe."
                )

            raise Exception(
                f"Error al actualizar la moneda: {str(e)}"
            )

        except Exception:
            conexion.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(cod_moneda, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()

            sql = """
                UPDATE moneda
                SET estado = 'Inactivo'
                WHERE cod_moneda = %s
            """

            cursor.execute(sql, (cod_moneda,))

            if cursor.rowcount == 0:
                raise Exception(
                    "La moneda indicada no existe."
                )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=4,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()
            raise Exception(
                f"Error al desactivar la moneda: {str(e)}"
            )

        except Exception:
            conexion.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def obtener_todos():
        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor(dictionary=True)

            sql = """
                SELECT
                    cod_moneda,
                    nombre_moneda,
                    simbolo,
                    estado
                FROM moneda
                ORDER BY cod_moneda ASC
            """

            cursor.execute(sql)

            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    # =========================================================
    # MONEDAS DIGITALES
    # =========================================================

    @staticmethod
    def guardar_digital(
        nombre_digital,
        simbolo_digital,
        estado,
        id_usuario_sesion
    ):
        Moneda.__validar_moneda_digital(
            nombre_digital,
            simbolo_digital
        )

        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()

            cursor.execute(
                "SELECT COALESCE(MAX(cod_mon_digital), 0) + 1 AS siguiente "
                "FROM moneda_digital"
            )

            resultado = cursor.fetchone()
            cod_mon_digital = resultado[0]

            sql = """
                INSERT INTO moneda_digital
                (
                    cod_mon_digital,
                    nombre_digital,
                    simbolo_digital,
                    estado
                )
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (
                    cod_mon_digital,
                    nombre_digital.strip(),
                    simbolo_digital.strip() if simbolo_digital else None,
                    estado
                )
            )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=1,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()

            if e.errno == 1062:
                raise Exception(
                    f"La moneda digital '{nombre_digital}' "
                    f"ya se encuentra registrada."
                )

            raise Exception(
                f"Error en la base de datos: {str(e)}"
            )

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def actualizar_digital(
        cod_mon_digital,
        nombre_digital,
        simbolo_digital,
        estado,
        id_usuario_sesion
    ):
        Moneda.__validar_moneda_digital(
            nombre_digital,
            simbolo_digital
        )

        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()

            sql = """
                UPDATE moneda_digital
                SET nombre_digital = %s,
                    simbolo_digital = %s,
                    estado = %s
                WHERE cod_mon_digital = %s
            """

            cursor.execute(
                sql,
                (
                    nombre_digital.strip(),
                    simbolo_digital.strip() if simbolo_digital else None,
                    estado,
                    cod_mon_digital
                )
            )

            if cursor.rowcount == 0:
                raise Exception(
                    "La moneda digital indicada no existe."
                )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=3,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()

            if e.errno == 1062:
                raise Exception(
                    f"La moneda digital '{nombre_digital}' ya existe."
                )

            raise Exception(
                f"Error al actualizar la moneda digital: {str(e)}"
            )

        except Exception:
            conexion.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def eliminar_digital(cod_mon_digital, id_usuario_sesion):
        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor()

            sql = """
                UPDATE moneda_digital
                SET estado = 0
                WHERE cod_mon_digital = %s
            """

            cursor.execute(sql, (cod_mon_digital,))

            if cursor.rowcount == 0:
                raise Exception(
                    "La moneda digital indicada no existe."
                )

            Bitacora.registrar(
                id_usuario_sesion,
                cod_accion=4,
                cod_modulo=31
            )

            conexion.commit()
            return True

        except Error as e:
            conexion.rollback()
            raise Exception(
                f"Error al desactivar la moneda digital: {str(e)}"
            )

        except Exception:
            conexion.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def obtener_todas_digitales():
        conexion = ConexionBD.obtener_conexion()
        cursor = None

        try:
            cursor = conexion.cursor(dictionary=True)

            sql = """
                SELECT
                    cod_mon_digital,
                    nombre_digital,
                    simbolo_digital,
                    estado
                FROM moneda_digital
                ORDER BY cod_mon_digital ASC
            """

            cursor.execute(sql)

            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()
            conexion.close()

   

    @staticmethod
    def __validar_moneda(nombre_moneda, simbolo, estado):
        if not nombre_moneda or len(nombre_moneda.strip()) < 2:
            raise ValueError(
                "El nombre de la moneda debe tener al menos 2 caracteres."
            )

        if len(nombre_moneda.strip()) > 50:
            raise ValueError(
                "El nombre de la moneda no puede superar los 50 caracteres."
            )

        if simbolo and len(simbolo.strip()) > 10:
            raise ValueError(
                "El símbolo de la moneda no puede superar los 10 caracteres."
            )

        if estado not in ["Activo", "Inactivo"]:
            raise ValueError(
                "El estado de la moneda no es válido."
            )

    @staticmethod
    def __validar_moneda_digital(nombre_digital, simbolo_digital):
        if not nombre_digital or len(nombre_digital.strip()) < 2:
            raise ValueError(
                "El nombre de la moneda digital debe tener "
                "al menos 2 caracteres."
            )

        if len(nombre_digital.strip()) > 50:
            raise ValueError(
                "El nombre de la moneda digital no puede superar "
                "los 50 caracteres."
            )

        if simbolo_digital and len(simbolo_digital.strip()) > 30:
            raise ValueError(
                "El símbolo digital no puede superar los 30 caracteres."
            )