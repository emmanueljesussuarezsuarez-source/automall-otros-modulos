from models.db import ConexionBD
from models.bitacora import Bitacora
from utils.validaciones_compra import ValidacionCompra
from mysql.connector import Error
from datetime import date


# ============================================================
#   CONSTANTES
# ============================================================
ESTADO_PENDIENTE  = 'Pendiente'
ESTADO_COMPLETADA = 'Completada'
ESTADO_ANULADA    = 'Anulada'
ESTADOS_COMPRA    = {ESTADO_PENDIENTE, ESTADO_COMPLETADA, ESTADO_ANULADA}

COD_ACCION_INSERT = 1
COD_ACCION_UPDATE = 3
COD_ACCION_DELETE = 4
COD_ACCION_APROBAR = 6
COD_MODULO_COMPRA = 21


class CompraModel:

    # ==========================================================
    #   COMPRAS (CABECERA)
    # ==========================================================

    @staticmethod
    def obtener_todas(incluir_anuladas=False):
        """
        Devuelve todas las compras con conteo de items y razón social del proveedor.

        :param incluir_anuladas: si True, incluye también las compras con estado 'Anulada'.
                                 Las anuladas siempre se ordenan al final del listado.
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)

            where = "" if incluir_anuladas else "WHERE c.estado <> %s"

            sql = f"""
                SELECT c.cod_compras,
                       c.fecha_compra,
                       c.precio,
                       c.tipo_compra,
                       c.estado,
                       c.observaciones,
                       c.rif_cedula_proveedor,
                       p.razon_social AS proveedor,
                       (SELECT COUNT(*)
                          FROM det_compra d
                         WHERE d.cod_compras = c.cod_compras) AS total_items
                  FROM compras_accesorios c
                  LEFT JOIN proveedor_compra p
                         ON p.rif_cedula_proveedor = c.rif_cedula_proveedor
                  {where}
                 ORDER BY
                    CASE WHEN c.estado = 'Anulada' THEN 1 ELSE 0 END,
                    c.fecha_compra DESC,
                    c.cod_compras DESC
            """

            if incluir_anuladas:
                cursor.execute(sql)
            else:
                cursor.execute(sql, (ESTADO_ANULADA,))

            return cursor.fetchall()
        except Error as e:
            raise Exception(f"Error al listar compras: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def obtener_por_id(cod_compras):
        """Devuelve la cabecera + detalles de una compra, o None si no existe."""
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT c.cod_compras,
                       c.fecha_compra,
                       c.precio,
                       c.tipo_compra,
                       c.estado,
                       c.observaciones,
                       c.rif_cedula_proveedor,
                       p.razon_social AS proveedor,
                       p.telefono     AS proveedor_telefono,
                       p.correo       AS proveedor_correo
                  FROM compras_accesorios c
                  LEFT JOIN proveedor_compra p
                         ON p.rif_cedula_proveedor = c.rif_cedula_proveedor
                 WHERE c.cod_compras = %s
            """, (cod_compras,))
            compra = cursor.fetchone()
            if not compra:
                return None

            cursor.execute("""
                SELECT d.cod_det_compra,
                       d.cantidad,
                       d.cod_insumo,
                       i.nombre_insumo,
                       i.unidad_medida
                  FROM det_compra d
                  LEFT JOIN insumos i ON i.cod_insumo = d.cod_insumo
                 WHERE d.cod_compras = %s
                 ORDER BY d.cod_det_compra ASC
            """, (cod_compras,))
            compra['detalles'] = cursor.fetchall()
            return compra
        except Error as e:
            raise Exception(f"Error al obtener compra: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def crear(rif_cedula_proveedor, tipo_compra='Normal',
              observaciones='', id_usuario_sesion=None):
        """
        Crea una compra en estado Pendiente con precio 0.
        Devuelve el cod_compras generado.
        """
        # ---------- Validaciones de negocio ----------
        valido, errores = ValidacionCompra.validar_cabecera({
            'rif_cedula_proveedor': rif_cedula_proveedor,
            'tipo_compra': tipo_compra,
            'observaciones': observaciones,
        })
        if not valido:
            raise Exception(f"Validación: {next(iter(errores.values()))}")

        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()

            # Verificar que el proveedor exista y esté activo
            cursor.execute("""
                SELECT 1 FROM proveedor_compra
                 WHERE rif_cedula_proveedor = %s
                   AND estado = 'Activo'
            """, (rif_cedula_proveedor,))
            if not cursor.fetchone():
                raise Exception("Validación: el proveedor no existe o está inactivo.")

            cursor.execute("""
                INSERT INTO compras_accesorios
                    (fecha_compra, precio, tipo_compra, estado,
                     observaciones, rif_cedula_proveedor)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                date.today(),
                0,
                tipo_compra.strip(),
                ESTADO_PENDIENTE,
                observaciones.strip() if observaciones else '',
                rif_cedula_proveedor
            ))
            cod_compras = cursor.lastrowid

            if id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_INSERT,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return cod_compras
        except Error as e:
            conexion.rollback()
            if e.errno == 1452:
                raise Exception("El proveedor indicado no existe.")
            raise Exception(f"Error al crear compra: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def actualizar_estado(cod_compras, estado, id_usuario_sesion=None):
        """
        Cambia el estado de una compra (sin tocar stock).
        Estados permitidos: Pendiente, Completada, Anulada.
        Para anular/revertir stock usa `eliminar`. Para reactivar usa `reactivar`.
        """
        if estado not in ESTADOS_COMPRA:
            raise Exception(f"Validación: estado inválido '{estado}'.")

        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE compras_accesorios
                   SET estado = %s
                 WHERE cod_compras = %s
            """, (estado, cod_compras))
            filas = cursor.rowcount

            if filas and id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_APROBAR,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return filas > 0
        except Error as e:
            conexion.rollback()
            raise Exception(f"Error al actualizar estado: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(cod_compras, id_usuario_sesion=None):
        """
        Borrado lógico: marca la compra como Anulada Y devuelve al stock
        todos los insumos que la compra había sumado.

        Ambas operaciones se hacen en una sola transacción:
          - Si algo falla, se revierte todo (ni anulación ni descuento).
        Los detalles NO se borran (se conserva el histórico).
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)

            # 1. Verificar que la compra exista y no esté ya anulada
            cursor.execute("""
                SELECT estado FROM compras_accesorios
                 WHERE cod_compras = %s
            """, (cod_compras,))
            fila = cursor.fetchone()
            if not fila:
                return {"status": False, "mensaje": "La compra no existe."}
            if fila['estado'] == ESTADO_ANULADA:
                return {"status": False, "mensaje": "La compra ya estaba anulada."}

            # 2. Revertir stock: restar a insumos lo que la compra sumó
            cursor.execute("""
                UPDATE insumos i
                JOIN det_compra d ON d.cod_insumo = i.cod_insumo
                   SET i.stock = GREATEST(i.stock - d.cantidad, 0)
                 WHERE d.cod_compras = %s
            """, (cod_compras,))

            # 3. Marcar la compra como Anulada (borrado lógico)
            cursor.execute("""
                UPDATE compras_accesorios
                   SET estado = %s
                 WHERE cod_compras = %s
                   AND estado <> %s
            """, (ESTADO_ANULADA, cod_compras, ESTADO_ANULADA))
            filas = cursor.rowcount

            if filas and id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_DELETE,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()

            if filas > 0:
                return {"status": True, "mensaje": "Compra anulada y stock revertido correctamente."}
            return {"status": False, "mensaje": "No se pudo anular la compra."}
        except Error as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al anular compra: {str(e)}"}
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def reactivar(cod_compras, id_usuario_sesion=None):
        """
        Reactiva una compra anulada: la vuelve a estado Pendiente Y
        suma al stock todos los insumos de sus detalles.

        Ambas operaciones se hacen en una sola transacción:
          - Si algo falla, se revierte todo (ni cambio de estado ni suma).
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)

            # 1. Verificar que exista y esté anulada
            cursor.execute("""
                SELECT estado FROM compras_accesorios
                 WHERE cod_compras = %s
            """, (cod_compras,))
            fila = cursor.fetchone()
            if not fila:
                return {"status": False, "mensaje": "La compra no existe."}
            if fila['estado'] != ESTADO_ANULADA:
                return {"status": False, "mensaje": "Solo se pueden reactivar compras anuladas."}

            # 2. Re-sumar stock
            cursor.execute("""
                UPDATE insumos i
                JOIN det_compra d ON d.cod_insumo = i.cod_insumo
                   SET i.stock = i.stock + d.cantidad
                 WHERE d.cod_compras = %s
            """, (cod_compras,))

            # 3. Devolver la compra a estado Pendiente
            cursor.execute("""
                UPDATE compras_accesorios
                   SET estado = %s
                 WHERE cod_compras = %s
                   AND estado = %s
            """, (ESTADO_PENDIENTE, cod_compras, ESTADO_ANULADA))
            filas = cursor.rowcount

            if filas and id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_UPDATE,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()

            if filas > 0:
                return {"status": True, "mensaje": "Compra reactivada y stock restaurado correctamente."}
            return {"status": False, "mensaje": "No se pudo reactivar la compra."}
        except Error as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al reactivar compra: {str(e)}"}
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    # ==========================================================
    #   DETALLES DE COMPRA
    # ==========================================================

    @staticmethod
    def agregar_detalle(cod_compras, cod_insumo, cantidad, id_usuario_sesion=None):
        """
        Agrega un insumo al detalle y suma stock.
        Verifica que la compra no esté anulada y que el insumo exista.
        """
        # ---------- Validaciones de negocio ----------
        valido, errores = ValidacionCompra.validar_detalle({
            'cod_compras': cod_compras,
            'cod_insumo': cod_insumo,
            'cantidad': cantidad,
        })
        if not valido:
            return {"status": False, "mensaje": next(iter(errores.values()))}

        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()

            # Compra debe existir y no estar anulada
            cursor.execute("""
                SELECT estado FROM compras_accesorios WHERE cod_compras = %s
            """, (cod_compras,))
            fila = cursor.fetchone()
            if not fila:
                return {"status": False, "mensaje": "La compra no existe."}
            if fila[0] == ESTADO_ANULADA:
                return {"status": False, "mensaje": "No se puede modificar una compra anulada."}

            # Insumo debe existir y estar activo
            cursor.execute("""
                SELECT 1 FROM insumos WHERE cod_insumo = %s AND estado = 1
            """, (cod_insumo,))
            if not cursor.fetchone():
                return {"status": False, "mensaje": "El insumo no existe o está inactivo."}

            # Insertar detalle
            cursor.execute("""
                INSERT INTO det_compra (cod_compras, cod_insumo, cantidad)
                VALUES (%s, %s, %s)
            """, (cod_compras, cod_insumo, cantidad))

            # Sumar stock
            cursor.execute("""
                UPDATE insumos
                   SET stock = stock + %s
                 WHERE cod_insumo = %s
            """, (cantidad, cod_insumo))

            conexion.commit()
            return {"status": True, "mensaje": "Insumo agregado correctamente."}
        except Error as e:
            conexion.rollback()
            if e.errno == 1062:
                return {"status": False, "mensaje": "Este insumo ya está agregado en la compra."}
            return {"status": False, "mensaje": f"Error al agregar insumo: {str(e)}"}
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def eliminar_detalle(cod_det_compra, id_usuario_sesion=None):
        """
        Elimina un detalle y resta del stock la cantidad registrada.
        Lee cod_insumo y cantidad de la propia BD (no confía en el cliente).
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT d.cod_insumo, d.cantidad, c.estado AS estado_compra
                  FROM det_compra d
                  JOIN compras_accesorios c ON c.cod_compras = d.cod_compras
                 WHERE d.cod_det_compra = %s
            """, (cod_det_compra,))
            detalle = cursor.fetchone()
            if not detalle:
                return {"status": False, "mensaje": "El detalle no existe."}
            if detalle['estado_compra'] == ESTADO_ANULADA:
                return {"status": False, "mensaje": "La compra está anulada, no se puede modificar."}

            cod_insumo = detalle['cod_insumo']
            cantidad   = detalle['cantidad']

            # Verificar stock suficiente
            cursor.execute("SELECT stock FROM insumos WHERE cod_insumo = %s",
                           (cod_insumo,))
            insumo = cursor.fetchone()
            if not insumo:
                return {"status": False, "mensaje": "El insumo asociado no existe."}
            if insumo['stock'] < cantidad:
                return {
                    "status": False,
                    "mensaje": (f"Stock insuficiente para revertir "
                                f"(actual {insumo['stock']}, requerido {cantidad}).")
                }

            cursor.execute("DELETE FROM det_compra WHERE cod_det_compra = %s",
                           (cod_det_compra,))
            cursor.execute("""
                UPDATE insumos SET stock = stock - %s WHERE cod_insumo = %s
            """, (cantidad, cod_insumo))

            if id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_DELETE,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return {"status": True, "mensaje": "Detalle eliminado correctamente."}
        except Error as e:
            conexion.rollback()
            return {"status": False, "mensaje": f"Error al eliminar detalle: {str(e)}"}
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    # ==========================================================
    #   PROVEEDORES
    # ==========================================================

    @staticmethod
    def obtener_proveedores(solo_activos=True):
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            where = "WHERE estado = 'Activo'" if solo_activos else ""
            sql = f"""
                SELECT rif_cedula_proveedor, razon_social, direccion,
                       telefono, correo, estado, fecha_registro
                  FROM proveedor_compra
                  {where}
                 ORDER BY razon_social
            """
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            raise Exception(f"Error al listar proveedores: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def obtener_proveedor_por_rif(rif):
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT rif_cedula_proveedor, razon_social, direccion,
                       telefono, correo, estado, fecha_registro
                  FROM proveedor_compra
                 WHERE rif_cedula_proveedor = %s
            """, (rif,))
            return cursor.fetchone()
        except Error as e:
            raise Exception(f"Error al obtener proveedor: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def crear_proveedor(rif, razon_social, direccion, telefono, correo,
                        id_usuario_sesion=None):
        # ---------- Validaciones de negocio ----------
        valido, errores = ValidacionCompra.validar_proveedor({
            'rif': rif,
            'razon_social': razon_social,
            'direccion': direccion,
            'telefono': telefono,
            'correo': correo,
        })
        if not valido:
            raise Exception(f"Validación: {next(iter(errores.values()))}")

        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO proveedor_compra
                    (rif_cedula_proveedor, razon_social, direccion,
                     telefono, correo, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, 'Activo', %s)
            """, (rif, razon_social.strip(), direccion.strip(),
                  telefono, correo.strip(), date.today()))

            if id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_INSERT,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return True
        except Error as e:
            conexion.rollback()
            if e.errno == 1062:
                raise Exception(f"El proveedor con RIF/Cédula {rif} ya existe.")
            raise Exception(f"Error al crear proveedor: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def actualizar_proveedor(rif, razon_social, direccion, telefono, correo,
                             estado='Activo', id_usuario_sesion=None):
        valido, errores = ValidacionCompra.validar_proveedor({
            'rif': rif,
            'razon_social': razon_social,
            'direccion': direccion,
            'telefono': telefono,
            'correo': correo,
            'estado': estado,
        })
        if not valido:
            raise Exception(f"Validación: {next(iter(errores.values()))}")

        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE proveedor_compra
                   SET razon_social = %s,
                       direccion    = %s,
                       telefono     = %s,
                       correo       = %s,
                       estado       = %s
                 WHERE rif_cedula_proveedor = %s
            """, (razon_social.strip(), direccion.strip(),
                  telefono, correo.strip(), estado, rif))
            filas = cursor.rowcount

            if filas and id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_UPDATE,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return filas > 0
        except Error as e:
            conexion.rollback()
            raise Exception(f"Error al actualizar proveedor: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def eliminar_proveedor(rif, id_usuario_sesion=None):
        """
        Borrado lógico del proveedor (estado='Inactivo').
        No se borra físicamente por las FK desde compras_accesorios.
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE proveedor_compra
                   SET estado = 'Inactivo'
                 WHERE rif_cedula_proveedor = %s
            """, (rif,))
            filas = cursor.rowcount

            if filas and id_usuario_sesion:
                Bitacora.registrar(id_usuario_sesion,
                                   cod_accion=COD_ACCION_DELETE,
                                   cod_modulo=COD_MODULO_COMPRA)

            conexion.commit()
            return filas > 0
        except Error as e:
            conexion.rollback()
            raise Exception(f"Error al inactivar proveedor: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    # ==========================================================
    #   INSUMOS (solo lectura, usados por el módulo de compras)
    # ==========================================================

    @staticmethod
    def obtener_insumos_activos():
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT cod_insumo, nombre_insumo, descripcion,
                       stock, unidad_medida
                  FROM insumos
                 WHERE estado = 1
                 ORDER BY nombre_insumo
            """)
            return cursor.fetchall()
        except Error as e:
            raise Exception(f"Error al listar insumos: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()

    @staticmethod
    def obtener_insumo_por_id(cod_insumo):
        conexion = ConexionBD.obtener_conexion()
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT cod_insumo, nombre_insumo, descripcion,
                       stock, unidad_medida
                  FROM insumos
                 WHERE cod_insumo = %s AND estado = 1
            """, (cod_insumo,))
            return cursor.fetchone()
        except Error as e:
            raise Exception(f"Error al obtener insumo: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            conexion.close()



