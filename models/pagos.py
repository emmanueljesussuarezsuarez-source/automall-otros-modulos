from models.db import ConexionBD
from models.bitacora import Bitacora


class Pagos:
    METODO_BINANCE = "1"
    METODO_EFECTIVO = "2"
    METODO_PAGO_MOVIL = "3"
    METODO_ZELLE = "4"
    METODO_TRANSFERENCIA = "5"
    METODO_ZINLI = "6"

    METODOS_BANCARIOS = {"3", "5"}
    METODOS_DIGITALES = {"1", "4", "6"}

    def __init__(self, data=None):
        data = data or {}
        self.__cod_pagos = data.get("cod_pagos")

        monto = data.get("monto_pago")
        if monto in (None, ""):
            monto = data.get("monto_abonado", 0)
        self.__monto_pago = float(monto or 0)

        self.__cod_cuentas = data.get("cod_cuentas")
        self.__cod_cuota = data.get("cod_cuota") or None
        self.__descripcion = data.get("descripcion", "")
        self.__cod_moneda = data.get("cod_moneda") or None
        self.__cod_metodo = data.get("cod_metodo")
        self.__referencia = data.get("referencia", "")
        self.__cod_banco = data.get("cod_banco") or None
        self.__cod_mon_digital = data.get("cod_mon_digital") or None
        self.__saldo_actual = float(data.get("saldo_actual", 0) or 0)

    # ==========================================================
    # GETTERS
    # ==========================================================
    @property
    def cod_pagos(self): return self.__cod_pagos

    @property
    def monto_pago(self): return self.__monto_pago

    @property
    def cod_cuentas(self): return self.__cod_cuentas

    @property
    def cod_cuota(self): return self.__cod_cuota

    @property
    def descripcion(self): return self.__descripcion

    @property
    def cod_moneda(self): return self.__cod_moneda

    @property
    def cod_metodo(self): return self.__cod_metodo

    @property
    def referencia(self): return self.__referencia

    @property
    def cod_banco(self): return self.__cod_banco

    @property
    def cod_mon_digital(self): return self.__cod_mon_digital

    @property
    def saldo_actual(self): return self.__saldo_actual

    # ==========================================================
    # TASA DE CAMBIO Y CONVERSIÓN
    # ==========================================================
    @staticmethod
    def obtener_tasa():
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT valor, fecha FROM tasa_cambio ORDER BY id DESC LIMIT 1")
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener tasa de cambio: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    @staticmethod
    def moneda_es_bolivar(cod_moneda, cursor):
        if not cod_moneda:
            return False
        cursor.execute("SELECT nombre_moneda, simbolo FROM moneda WHERE cod_moneda = %s LIMIT 1", (cod_moneda,))
        moneda = cursor.fetchone()
        if not moneda:
            return False
        texto = f"{moneda.get('nombre_moneda', '')} {moneda.get('simbolo', '')}".lower()
        return any(k in texto for k in ("bolivar", "bolívar", "ves", "bs"))

    @staticmethod
    def convertir_a_usd(monto, cod_moneda, cursor):
        monto = float(monto or 0)
        if not Pagos.moneda_es_bolivar(cod_moneda, cursor):
            return monto, None

        cursor.execute("SELECT valor, fecha FROM tasa_cambio ORDER BY id DESC LIMIT 1")
        tasa = cursor.fetchone()
        if not tasa or not tasa.get("valor"):
            raise ValueError("No existe una tasa de cambio registrada. Actualice la tasa antes de registrar un pago en bolívares.")

        valor_tasa = float(tasa["valor"])
        if valor_tasa <= 0:
            raise ValueError("La tasa de cambio registrada no es válida.")

        return monto / valor_tasa, valor_tasa

    # ==========================================================
    # CONSULTA DE CUOTAS
    # ==========================================================
    @staticmethod
    def obtener_cuotas_por_cuenta(cod_cuentas):
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    cxc.cod_cuentas,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    v.cedula_usuario AS cedula_cliente,
                    dv.placa
                FROM cuentas_por_cobrar cxc
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                LEFT JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                WHERE cxc.cod_cuentas = %s
                LIMIT 1
            """, (cod_cuentas,))
            cuenta = cursor.fetchone()
            if not cuenta:
                return None

            cursor.execute("""
                SELECT
                    cod_cuota,
                    cod_cuentas,
                    numero_cuota,
                    monto_cuota,
                    monto_pagado,
                    GREATEST(0.00, monto_cuota - monto_pagado) AS saldo_cuota,
                    fecha_vencimiento,
                    fecha_pago,
                    estado,
                    CASE
                        WHEN estado IN ('Pendiente', 'Parcial') AND fecha_vencimiento < CURDATE() THEN 'Vencida'
                        ELSE estado
                    END AS estado_actual,
                    CASE
                        WHEN estado IN ('Pendiente', 'Parcial', 'Vencida') AND fecha_vencimiento < CURDATE()
                        THEN DATEDIFF(CURDATE(), fecha_vencimiento)
                        ELSE 0
                    END AS dias_mora
                FROM cuotas
                WHERE cod_cuentas = %s
                ORDER BY numero_cuota ASC
            """, (cod_cuentas,))
            cuotas = cursor.fetchall()

            for c in cuotas:
                c["monto_cuota"] = float(c["monto_cuota"] or 0)
                c["monto_pagado"] = float(c["monto_pagado"] or 0)
                c["saldo_cuota"] = float(c["saldo_cuota"] or 0)
                if c.get("fecha_vencimiento"):
                    c["fecha_vencimiento"] = c["fecha_vencimiento"].strftime("%Y-%m-%d")
                if c.get("fecha_pago"):
                    c["fecha_pago"] = c["fecha_pago"].strftime("%Y-%m-%d %H:%M:%S")

            return {
                "exito": True,
                "cod_cuentas": cuenta["cod_cuentas"],
                "cedula_cliente": cuenta["cedula_cliente"],
                "placa": cuenta.get("placa"),
                "frecuencia_pago": cuenta.get("frecuencia_pago") or "Mensual",
                "cantidad_cuotas": cuenta.get("cantidad_cuotas") or 1,
                "cuotas": cuotas
            }
        except Exception as e:
            print(f"Error al obtener cuotas de cuenta #{cod_cuentas}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    @staticmethod
    def obtener_cuotas_cliente(cedula_usuario):
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    c.cod_cuota,
                    c.cod_cuentas,
                    c.numero_cuota,
                    c.monto_cuota,
                    c.monto_pagado,
                    GREATEST(0.00, c.monto_cuota - c.monto_pagado) AS saldo_cuota,
                    c.fecha_vencimiento,
                    c.fecha_pago,
                    c.estado,
                    CASE
                        WHEN c.estado IN ('Pendiente', 'Parcial') AND c.fecha_vencimiento < CURDATE() THEN 'Vencida'
                        ELSE c.estado
                    END AS estado_actual,
                    CASE
                        WHEN c.estado IN ('Pendiente', 'Parcial', 'Vencida') AND c.fecha_vencimiento < CURDATE()
                        THEN DATEDIFF(CURDATE(), c.fecha_vencimiento)
                        ELSE 0
                    END AS dias_mora,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    cxc.deuda_total,
                    cxc.deuda AS deuda_cuenta,
                    dv.placa
                FROM cuotas c
                INNER JOIN cuentas_por_cobrar cxc ON c.cod_cuentas = cxc.cod_cuentas
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                WHERE v.cedula_usuario = %s
                  AND LOWER(v.estado) <> 'anulada'
                ORDER BY
                    CASE WHEN c.estado IN ('Pendiente', 'Parcial', 'Vencida') THEN 0 ELSE 1 END,
                    c.fecha_vencimiento ASC,
                    c.numero_cuota ASC
            """, (cedula_usuario,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener cuotas del cliente: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    @staticmethod
    def obtener_todas_cuotas_admin():
        conexion = None
        cursor = None
        conexion_seg = None
        cursor_seg = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    c.cod_cuota,
                    c.cod_cuentas,
                    c.numero_cuota,
                    c.monto_cuota,
                    c.monto_pagado,
                    GREATEST(0.00, c.monto_cuota - c.monto_pagado) AS saldo_cuota,
                    c.fecha_vencimiento,
                    c.fecha_pago,
                    c.estado,
                    CASE
                        WHEN c.estado IN ('Pendiente', 'Parcial') AND c.fecha_vencimiento < CURDATE() THEN 'Vencida'
                        ELSE c.estado
                    END AS estado_actual,
                    CASE
                        WHEN c.estado IN ('Pendiente', 'Parcial', 'Vencida') AND c.fecha_vencimiento < CURDATE()
                        THEN DATEDIFF(CURDATE(), c.fecha_vencimiento)
                        ELSE 0
                    END AS dias_mora,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    v.cedula_usuario,
                    dv.placa
                FROM cuotas c
                INNER JOIN cuentas_por_cobrar cxc ON c.cod_cuentas = cxc.cod_cuentas
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                WHERE LOWER(v.estado) <> 'anulada'
                  AND LOWER(cxc.estado) NOT IN ('anulado', 'anulada')
                ORDER BY
                    CASE
                        WHEN c.estado IN ('Pendiente', 'Parcial') AND c.fecha_vencimiento < CURDATE() THEN 0
                        WHEN c.estado IN ('Pendiente', 'Parcial', 'Vencida') THEN 1
                        ELSE 2
                    END,
                    c.fecha_vencimiento ASC,
                    c.numero_cuota ASC
            """)
            cuotas = cursor.fetchall()

            if cuotas:
                conexion_seg = ConexionBD.obtener_conexion_seguridad()
                cursor_seg = conexion_seg.cursor(dictionary=True)
                cursor_seg.execute("SELECT cedula_usuario, nombre, apellido FROM t_usuario")
                mapa = {
                    str(u["cedula_usuario"]).strip(): f"{u['nombre']} {u['apellido']}".strip()
                    for u in cursor_seg.fetchall()
                }
                for c in cuotas:
                    c["nombre_cliente"] = mapa.get(str(c["cedula_usuario"]).strip(), "Cliente")

            return cuotas
        except Exception as e:
            print(f"Error al obtener cuotas admin: {e}")
            return []
        finally:
            if cursor_seg: cursor_seg.close()
            if conexion_seg: conexion_seg.close()
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # PROCESAR ABONO (CON APLICACIÓN A CUOTAS)
    # ==========================================================
    def procesar_abono(self, cedula_usuario):
        from utils.validaciones_pagos import validar_abono_pago
        conexion = None
        cursor = None

        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            # 1. BLOQUEAR CUENTA Y OBTENER PROPIETARIO REAL
            cursor.execute("""
                SELECT cxc.cod_cuentas, cxc.deuda_total, cxc.deuda, cxc.estado, v.cedula_usuario AS cedula_cliente
                FROM cuentas_por_cobrar cxc
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                WHERE cxc.cod_cuentas = %s
                FOR UPDATE
            """, (self.__cod_cuentas,))
            cuenta = cursor.fetchone()

            if not cuenta:
                return {"status": False, "error": "La cuenta por cobrar no existe."}
            if str(cuenta["estado"]).lower() != "pendiente":
                return {"status": False, "error": "La cuenta seleccionada no tiene una deuda pendiente."}

            saldo_real_usd = float(cuenta["deuda"] or 0)
            if saldo_real_usd <= 0:
                return {"status": False, "error": "La cuenta seleccionada ya está pagada."}

            # 2. VALIDACIONES
            validacion = validar_abono_pago(self, validar_monto=False)
            if not validacion["status"]:
                return validacion

            metodo = str(self.__cod_metodo)

            # 3. CONVERTIR A USD
            monto_usd, tasa_usada = self.convertir_a_usd(self.__monto_pago, self.__cod_moneda, cursor)
            if monto_usd <= 0:
                return {"status": False, "error": "El monto convertido a USD debe ser mayor a cero."}

            if monto_usd > saldo_real_usd + 0.02:
                return {
                    "status": False,
                    "error": f"El monto equivale a ${monto_usd:,.2f} USD, pero la deuda pendiente es ${saldo_real_usd:,.2f} USD."
                }

            monto_aplicar_total = min(round(monto_usd, 2), saldo_real_usd)

            # 4. REGISTRAR EN PAGO_CUENTAS
            referencia = (self.__referencia or "").strip()
            if metodo == self.METODO_EFECTIVO:
                referencia = None

            cursor.execute("""
                INSERT INTO pago_cuentas (monto_abonado, fecha_pago, referencia, estado, cod_cuentas)
                VALUES (%s, NOW(), %s, %s, %s)
            """, (monto_aplicar_total, referencia, "Procesado", self.__cod_cuentas))
            cod_pagos = cursor.lastrowid

            # 5. DET_PAGO
            cod_moneda = self.__cod_moneda if (metodo == self.METODO_EFECTIVO or metodo in self.METODOS_BANCARIOS) else None
            descripcion = (self.__descripcion or "").strip()
            if tasa_usada:
                descripcion = f"{descripcion} | Monto recibido: {self.__monto_pago:.2f} Bs. | Tasa: {tasa_usada:.6f} Bs/USD | Equivalente USD: ${monto_aplicar_total:.2f}".strip(" |")
            elif not descripcion:
                descripcion = "Abono de cuenta"

            cursor.execute("""
                INSERT INTO det_pago (tipo_pago, fecha_det_pago, descripcion, cod_pagos, cod_metodo, cod_moneda)
                VALUES (%s, NOW(), %s, %s, %s, %s)
            """, ("abono", descripcion, cod_pagos, self.__cod_metodo, cod_moneda))
            cod_det_pago = cursor.lastrowid

            # 6. DETALLES SEGÚN MÉTODO DE PAGO
            if metodo in self.METODOS_DIGITALES:
                if not self.__cod_mon_digital:
                    raise ValueError("Debe seleccionar la moneda/plataforma digital.")
                cursor.execute(
                    "INSERT INTO det_nom_digital (monto, referencia, cod_mon_digital, cod_det_pago) VALUES (%s, %s, %s, %s)",
                    (self.__monto_pago, referencia, self.__cod_mon_digital, cod_det_pago)
                )
            elif metodo in self.METODOS_BANCARIOS:
                if not self.__cod_banco:
                    raise ValueError("Debe seleccionar el banco.")
                cursor.execute(
                    "INSERT INTO det_banco (monto, referencia, cod_banco, cod_det_pago) VALUES (%s, %s, %s, %s)",
                    (self.__monto_pago, referencia, self.__cod_banco, cod_det_pago)
                )
            elif metodo != self.METODO_EFECTIVO:
                raise ValueError(f"Método de pago no reconocido: {metodo}")

            # 7. APLICAR EL PAGO A LAS CUOTAS DE LA CUENTA (Específica o FIFO)
            cod_cuota_obj = int(self.__cod_cuota) if self.__cod_cuota else 0
            cursor.execute("""
                SELECT cod_cuota, numero_cuota, monto_cuota, monto_pagado
                FROM cuotas
                WHERE cod_cuentas = %s
                  AND estado IN ('Pendiente', 'Parcial', 'Vencida')
                ORDER BY
                  CASE WHEN %s > 0 AND cod_cuota = %s THEN 0 ELSE 1 END,
                  numero_cuota ASC
                FOR UPDATE
            """, (self.__cod_cuentas, cod_cuota_obj, cod_cuota_obj))
            cuotas_pendientes = cursor.fetchall()

            restante = monto_aplicar_total
            cuotas_tocadas = []
            for c in cuotas_pendientes:
                if restante <= 0.0001:
                    break
                m_cuota = float(c["monto_cuota"] or 0)
                m_pagado = float(c["monto_pagado"] or 0)
                saldo_c = round(max(0.0, m_cuota - m_pagado), 2)
                if saldo_c <= 0:
                    continue

                aplicar = round(min(restante, saldo_c), 2)
                nuevo_pagado = round(m_pagado + aplicar, 2)
                est_cuota = "Pagada" if nuevo_pagado >= m_cuota - 0.009 else "Parcial"

                cursor.execute("""
                    INSERT INTO pago_cuota_detalle (cod_pagos, cod_cuota, monto_aplicado)
                    VALUES (%s, %s, %s)
                """, (cod_pagos, c["cod_cuota"], aplicar))

                cursor.execute("""
                    UPDATE cuotas
                    SET monto_pagado = %s,
                        estado = %s,
                        fecha_pago = IF(%s = 'Pagada', NOW(), fecha_pago)
                    WHERE cod_cuota = %s
                """, (nuevo_pagado, est_cuota, est_cuota, c["cod_cuota"]))

                cuotas_tocadas.append(f"Cuota #{c['numero_cuota']}")
                restante = round(restante - aplicar, 2)

            # 8. ACTUALIZAR DEUDA GENERAL EN CUENTAS_POR_COBRAR
            nuevo_saldo = round(max(0.0, saldo_real_usd - monto_aplicar_total), 2)
            nuevo_estado = "Pagado" if nuevo_saldo <= 0 else "Pendiente"
            cursor.execute(
                "UPDATE cuentas_por_cobrar SET deuda = %s, estado = %s WHERE cod_cuentas = %s",
                (nuevo_saldo, nuevo_estado, self.__cod_cuentas)
            )

            # 9. BITÁCORA Y COMMIT
            Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=15)
            conexion.commit()

            detalle_cuotas = f" ({', '.join(cuotas_tocadas)})" if cuotas_tocadas else ""
            return {
                "status": True,
                "message": f"Abono registrado correctamente{detalle_cuotas}.",
                "cod_pagos": cod_pagos,
                "monto_usd": monto_aplicar_total,
                "nuevo_saldo": nuevo_saldo,
                "saldo_restante": nuevo_saldo,
                "cedula_cliente": cuenta["cedula_cliente"],
                "tasa": tasa_usada
            }

        except Exception as e:
            if conexion: conexion.rollback()
            print(f"Error detectado en el modelo de pagos: {e}")
            return {"status": False, "error": str(e)}
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # ANULAR PAGO (RESTAURAR DEUDA Y CUOTAS SIN ANULAR LA VENTA)
    # ==========================================================
    @staticmethod
    def anular(cod_pagos, cedula_usuario, motivo):
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT p.cod_pagos, p.cod_cuentas, p.monto_abonado, p.estado,
                       c.deuda, c.deuda_total, c.cod_venta, v.cedula_usuario AS cedula_cliente
                FROM pago_cuentas p
                INNER JOIN cuentas_por_cobrar c ON p.cod_cuentas = c.cod_cuentas
                INNER JOIN ventas v ON c.cod_venta = v.cod_venta
                WHERE p.cod_pagos = %s
                FOR UPDATE
            """, (cod_pagos,))
            pago = cursor.fetchone()

            if not pago or str(pago["estado"]).lower() == "anulado":
                return False

            monto_anulado = float(pago["monto_abonado"] or 0)
            deuda_actual = float(pago["deuda"] or 0)
            deuda_total = float(pago["deuda_total"] or 0)
            nuevo_saldo = round(min(deuda_total, deuda_actual + monto_anulado), 2)
            nuevo_estado_cuenta = "Pagado" if nuevo_saldo <= 0 else "Pendiente"

            # Al pasar pago_cuentas.estado a 'Anulado', el trigger trg_after_update_pago_anulado
            # revierte automáticamente monto_pagado y estado en las cuotas vinculadas.
            cursor.execute("UPDATE pago_cuentas SET estado = 'Anulado' WHERE cod_pagos = %s", (cod_pagos,))

            motivo = (motivo or "Sin motivo especificado").strip()
            cursor.execute(
                "UPDATE det_pago SET descripcion = CONCAT(IFNULL(descripcion, ''), '\n[ANULADO] Motivo: ', %s) WHERE cod_pagos = %s",
                (motivo, cod_pagos)
            )

            cursor.execute(
                "UPDATE cuentas_por_cobrar SET deuda = %s, estado = %s WHERE cod_cuentas = %s",
                (nuevo_saldo, nuevo_estado_cuenta, pago["cod_cuentas"])
            )

            Bitacora.registrar(cedula_usuario, cod_accion=4, cod_modulo=15)
            conexion.commit()
            return {"status": True, "cedula_cliente": pago["cedula_cliente"], "nuevo_saldo": nuevo_saldo}

        except Exception as e:
            if conexion: conexion.rollback()
            print(f"Error al anular pago: {e}")
            return False
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # DATOS COMPLETOS PARA COMPROBANTE PDF DE PAGO
    # ==========================================================
    @staticmethod
    def obtener_datos_factura(cod_pagos):
        conexion = None
        cursor = None
        conexion_seguridad = None
        cursor_cliente = None

        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    pc.cod_pagos,
                    pc.monto_abonado,
                    pc.fecha_pago,
                    pc.referencia AS referencia_pago,
                    pc.estado AS estado_pago,
                    cxc.cod_cuentas,
                    cxc.deuda_total,
                    cxc.deuda AS saldo_pendiente,
                    cxc.fecha_emision,
                    cxc.fecha_vencimiento,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    cxc.estado AS estado_cuenta,
                    v.cod_venta,
                    v.fecha_venta,
                    v.tipo_venta,
                    v.estado AS estado_venta,
                    v.cedula_usuario AS cedula_cliente,
                    dv.placa,
                    dv.precio,
                    dv.poder,
                    dv.traspaso_papel,
                    vh.anio,
                    vh.color,
                    mrc.nombre_marca AS marca,
                    mo.nombre_modelo AS modelo,
                    tv.nombre_tipo AS tipo_vehiculo,
                    dp.cod_det_pago,
                    dp.tipo_pago,
                    dp.fecha_det_pago,
                    dp.descripcion,
                    dp.cod_metodo,
                    dp.cod_moneda,
                    mp.nombre_metodo,
                    m.nombre_moneda,
                    m.simbolo,
                    db.monto AS monto_banco,
                    db.referencia AS referencia_banco,
                    db.cod_banco,
                    b.nombre_banco,
                    dnd.monto AS monto_digital,
                    dnd.referencia AS referencia_digital,
                    dnd.cod_mon_digital,
                    md.nombre_digital,
                    md.simbolo_digital
                FROM pago_cuentas pc
                INNER JOIN cuentas_por_cobrar cxc ON pc.cod_cuentas = cxc.cod_cuentas
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                INNER JOIN vehiculo vh ON dv.placa = vh.placa
                INNER JOIN modelo mo ON vh.cod_modelo = mo.cod_modelo
                INNER JOIN marca mrc ON mo.cod_marca = mrc.cod_marca
                INNER JOIN tipo_vehiculo tv ON vh.cod_tipo = tv.cod_tipo
                LEFT JOIN det_pago dp ON pc.cod_pagos = dp.cod_pagos
                LEFT JOIN metodo_pago mp ON dp.cod_metodo = mp.cod_metodo
                LEFT JOIN moneda m ON dp.cod_moneda = m.cod_moneda
                LEFT JOIN det_banco db ON dp.cod_det_pago = db.cod_det_pago
                LEFT JOIN banco b ON db.cod_banco = b.cod_banco
                LEFT JOIN det_nom_digital dnd ON dp.cod_det_pago = dnd.cod_det_pago
                LEFT JOIN moneda_digital md ON dnd.cod_mon_digital = md.cod_mon_digital
                WHERE pc.cod_pagos = %s
                LIMIT 1
            """, (cod_pagos,))
            pago = cursor.fetchone()
            if not pago:
                return None

            # Cuotas cubiertas por este pago
            cursor.execute("""
                SELECT c.numero_cuota, c.fecha_vencimiento, c.monto_cuota, pcd.monto_aplicado, c.estado
                FROM pago_cuota_detalle pcd
                INNER JOIN cuotas c ON pcd.cod_cuota = c.cod_cuota
                WHERE pcd.cod_pagos = %s
                ORDER BY c.numero_cuota ASC
            """, (cod_pagos,))
            cuotas_aplicadas = cursor.fetchall()

            cursor.execute("""
                SELECT IFNULL(SUM(CASE WHEN LOWER(pc.estado) = 'procesado' THEN pc.monto_abonado ELSE 0 END), 0) AS total_pagado
                FROM pago_cuentas pc
                WHERE pc.cod_cuentas = %s
            """, (pago["cod_cuentas"],))
            resultado_total = cursor.fetchone()
            total_pagado = float(resultado_total["total_pagado"] if resultado_total else 0)

            monto_pago = float(pago["monto_abonado"] or 0)
            saldo_actual = float(pago["saldo_pendiente"] or 0)
            estado_pago = str(pago["estado_pago"] or "").lower()

            if estado_pago == "anulado":
                saldo_antes = saldo_actual
                saldo_despues = round(saldo_actual, 2)
            else:
                saldo_despues = saldo_actual
                saldo_antes = round(saldo_actual + monto_pago, 2)

            conexion_seguridad = ConexionBD.obtener_conexion_seguridad()
            cursor_cliente = conexion_seguridad.cursor(dictionary=True)
            cursor_cliente.execute("""
                SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo
                FROM t_usuario
                WHERE cedula_usuario = %s
                LIMIT 1
            """, (pago["cedula_cliente"],))
            cliente = cursor_cliente.fetchone() or {
                "cedula_usuario": pago["cedula_cliente"],
                "nombre": "Cliente",
                "apellido": "no disponible",
                "telefono": "",
                "direccion": "",
                "correo": ""
            }

            pago["moneda"] = pago.get("nombre_moneda") or pago.get("nombre_digital") or "N/D"
            pago["simbolo_moneda"] = pago.get("simbolo") or pago.get("simbolo_digital") or ""
            pago["metodo_pago"] = pago.get("nombre_metodo") or "N/D"
            pago["referencia"] = (
                pago.get("referencia_banco")
                or pago.get("referencia_digital")
                or pago.get("referencia_pago")
                or "N/D"
            )

            if pago.get("monto_banco") is not None:
                pago["monto_recibido"] = float(pago["monto_banco"])
            elif pago.get("monto_digital") is not None:
                pago["monto_recibido"] = float(pago["monto_digital"])
            else:
                pago["monto_recibido"] = monto_pago

            pago["monto_abonado"] = monto_pago
            pago["deuda_total"] = float(pago["deuda_total"] or 0)
            pago["saldo_pendiente"] = saldo_despues
            pago["saldo_antes"] = saldo_antes
            pago["total_pagado"] = total_pagado
            pago["precio"] = float(pago["precio"] or 0)

            return {"pago": pago, "cliente": cliente, "cuotas_aplicadas": cuotas_aplicadas}

        except Exception as e:
            print(f"Error al obtener datos para comprobante de pago #{cod_pagos}: {e}")
            return None
        finally:
            if cursor_cliente: cursor_cliente.close()
            if conexion_seguridad: conexion_seguridad.close()
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # LISTAR PAGOS DEL CLIENTE
    # ==========================================================
    @staticmethod
    def obtener_todos(cedula_usuario):
        conexion = None
        cursor = None
        sql = """
            SELECT
                pc.cod_pagos,
                pc.monto_abonado,
                pc.fecha_pago,
                pc.referencia AS referencia_pago,
                pc.estado AS estado_pago,
                dv.placa,
                cxc.estado AS estado_cuenta,
                cxc.deuda_total,
                cxc.fecha_vencimiento,
                cxc.deuda,
                cxc.frecuencia_pago,
                cxc.cantidad_cuotas,
                dp.tipo_pago,
                dp.descripcion,
                dp.fecha_det_pago,
                mp.nombre_metodo,
                m.nombre_moneda,
                m.simbolo,
                md.nombre_digital,
                md.simbolo_digital,
                COALESCE(db.referencia, dnd.referencia, pc.referencia) AS referencia,
                COALESCE(db.monto, dnd.monto) AS monto_detalle,
                b.nombre_banco,
                (
                    SELECT GROUP_CONCAT(CONCAT('Cuota #', c.numero_cuota) ORDER BY c.numero_cuota SEPARATOR ', ')
                    FROM pago_cuota_detalle pcd
                    INNER JOIN cuotas c ON pcd.cod_cuota = c.cod_cuota
                    WHERE pcd.cod_pagos = pc.cod_pagos
                ) AS cuotas_aplicadas
            FROM pago_cuentas pc
            INNER JOIN cuentas_por_cobrar cxc ON pc.cod_cuentas = cxc.cod_cuentas
            INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            INNER JOIN det_pago dp ON pc.cod_pagos = dp.cod_pagos
            INNER JOIN metodo_pago mp ON dp.cod_metodo = mp.cod_metodo
            LEFT JOIN moneda m ON dp.cod_moneda = m.cod_moneda
            LEFT JOIN det_banco db ON dp.cod_det_pago = db.cod_det_pago
            LEFT JOIN banco b ON db.cod_banco = b.cod_banco
            LEFT JOIN det_nom_digital dnd ON dp.cod_det_pago = dnd.cod_det_pago
            LEFT JOIN moneda_digital md ON dnd.cod_mon_digital = md.cod_mon_digital
            WHERE v.cedula_usuario = %s
            ORDER BY pc.fecha_pago DESC, pc.cod_pagos DESC
        """
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(sql, (cedula_usuario,))
            Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=15)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener pagos: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # DEUDAS PENDIENTES
    # ==========================================================
    @staticmethod
    def obtener_deudas_pendientes(cedula_usuario):
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    cxc.cod_cuentas,
                    dv.placa,
                    cxc.deuda_total,
                    cxc.deuda AS saldo_pendiente,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    v.cod_venta
                FROM cuentas_por_cobrar cxc
                INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
                INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                WHERE v.cedula_usuario = %s
                  AND LOWER(cxc.estado) = 'pendiente'
                  AND cxc.deuda > 0
                ORDER BY dv.placa
            """, (cedula_usuario,))
            return cursor.fetchall()
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    # ==========================================================
    # LISTAR ADMIN
    # ==========================================================
    @staticmethod
    def obtener_todos_admin():
        conexion = None
        cursor = None
        sql = """
            SELECT
                pc.cod_pagos,
                pc.monto_abonado,
                pc.fecha_pago,
                pc.referencia AS referencia_pago,
                pc.estado AS estado_pago,
                dv.placa,
                cxc.estado AS estado_cuenta,
                cxc.deuda_total,
                cxc.deuda AS saldo_pendiente,
                cxc.fecha_vencimiento,
                cxc.frecuencia_pago,
                cxc.cantidad_cuotas,
                dp.tipo_pago,
                dp.descripcion,
                dp.fecha_det_pago,
                mp.nombre_metodo,
                m.nombre_moneda,
                m.simbolo,
                md.nombre_digital,
                md.simbolo_digital,
                COALESCE(db.referencia, dnd.referencia, pc.referencia) AS referencia,
                COALESCE(db.monto, dnd.monto) AS monto_detalle,
                b.nombre_banco,
                v.cedula_usuario,
                (
                    SELECT GROUP_CONCAT(CONCAT('Cuota #', c.numero_cuota) ORDER BY c.numero_cuota SEPARATOR ', ')
                    FROM pago_cuota_detalle pcd
                    INNER JOIN cuotas c ON pcd.cod_cuota = c.cod_cuota
                    WHERE pcd.cod_pagos = pc.cod_pagos
                ) AS cuotas_aplicadas
            FROM pago_cuentas pc
            INNER JOIN cuentas_por_cobrar cxc ON pc.cod_cuentas = cxc.cod_cuentas
            INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            INNER JOIN det_pago dp ON pc.cod_pagos = dp.cod_pagos
            INNER JOIN metodo_pago mp ON dp.cod_metodo = mp.cod_metodo
            LEFT JOIN moneda m ON dp.cod_moneda = m.cod_moneda
            LEFT JOIN det_banco db ON dp.cod_det_pago = db.cod_det_pago
            LEFT JOIN banco b ON db.cod_banco = b.cod_banco
            LEFT JOIN det_nom_digital dnd ON dp.cod_det_pago = dnd.cod_det_pago
            LEFT JOIN moneda_digital md ON dnd.cod_mon_digital = md.cod_mon_digital
            ORDER BY pc.fecha_pago DESC, pc.cod_pagos DESC
        """
        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(sql)
            pagos = cursor.fetchall()
            if not pagos:
                return []

            ids_clientes = list({p["cedula_usuario"] for p in pagos if p.get("cedula_usuario")})
            if ids_clientes:
                conexion_seg = None
                cursor_seg = None
                try:
                    conexion_seg = ConexionBD.obtener_conexion_seguridad()
                    cursor_seg = conexion_seg.cursor(dictionary=True)
                    format_strings = ",".join(["%s"] * len(ids_clientes))
                    cursor_seg.execute(f"""
                        SELECT cedula_usuario, nombre, apellido, telefono, direccion
                        FROM t_usuario
                        WHERE cedula_usuario IN ({format_strings})
                    """, tuple(ids_clientes))
                    mapa = {str(u["cedula_usuario"]).strip(): u for u in cursor_seg.fetchall()}

                    for p in pagos:
                        cedula = str(p["cedula_usuario"]).strip()
                        usuario = mapa.get(cedula, {})
                        p["cedula"] = usuario.get("cedula_usuario", p.get("cedula_usuario", "Sin Cédula"))
                        p["nombre"] = usuario.get("nombre", "Sin Nombre")
                        p["apellido"] = usuario.get("apellido", "")
                        p["telefono"] = usuario.get("telefono", "Sin Teléfono")
                        p["direccion"] = usuario.get("direccion", "Sin Dirección")
                finally:
                    if cursor_seg: cursor_seg.close()
                    if conexion_seg: conexion_seg.close()

            return pagos
        except Exception as e:
            print(f"Error al obtener pagos admin: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    @staticmethod
    def obtener_todos_clientes():
        conexion = None
        cursor = None
        try:
            conexion = ConexionBD.obtener_conexion_seguridad()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT cedula_usuario, nombre, apellido FROM t_usuario WHERE estado = 1")
            return cursor.fetchall()
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()