import calendar
import json
from datetime import datetime, date, timedelta
from models.db import ConexionBD
from models.bitacora import Bitacora


def _sumar_mes_seguro(fecha_base, meses):
    mes_destino = fecha_base.month - 1 + meses
    anio = fecha_base.year + mes_destino // 12
    mes = mes_destino % 12 + 1
    dia = min(fecha_base.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def _parsear_fecha_segura(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _generar_lista_cuotas(saldo_financiar, cantidad_cuotas, frecuencia, fecha_inicio):
    saldo = round(float(saldo_financiar or 0), 2)
    cantidad = max(1, int(cantidad_cuotas or 1))
    frec_norm = (frecuencia or 'Mensual').strip().lower()
    fecha_base = _parsear_fecha_segura(fecha_inicio)

    if not fecha_base:
        hoy = date.today()
        if frec_norm == 'semanal':
            fecha_base = hoy + timedelta(days=7)
        elif frec_norm == 'quincenal':
            fecha_base = hoy + timedelta(days=15)
        else:
            fecha_base = _sumar_mes_seguro(hoy, 1)

    if saldo <= 0:
        return []

    cuota_base = round(saldo / cantidad, 2)
    lista = []

    for i in range(1, cantidad + 1):
        if i == cantidad:
            monto = round(saldo - (cuota_base * (cantidad - 1)), 2)
        else:
            monto = cuota_base

        if frec_norm == 'semanal':
            fecha_venc = fecha_base + timedelta(days=(i - 1) * 7)
        elif frec_norm == 'quincenal':
            fecha_venc = fecha_base + timedelta(days=(i - 1) * 15)
        else:
            fecha_venc = _sumar_mes_seguro(fecha_base, i - 1)

        lista.append({
            'numero_cuota': i,
            'monto_cuota': monto,
            'fecha_vencimiento': fecha_venc.strftime('%Y-%m-%d')
        })

    return lista


class Ventas:
    def __init__(self, data):
        self.__cedula_cliente = data.get('cedula_cliente')
        self.__placa = data.get('placa')
        self.__tipo_venta = (data.get('tipo_venta') or '').strip().lower()
        self.__poder = 1 if data.get('poder') else 0
        self.__traspaso_papel = 1 if data.get('traspaso_papel') else 0
        self.__monto_recibido = float(data.get('monto_recibido') or 0)
        self.__precio_total = float(data.get('precio_vehiculo') or 0)
        self.__deuda_pendiente = float(data.get('deuda_pendiente') or 0)
        self.__fecha_vencimiento = data.get('fecha_vencimiento') or None

        # Campos del plan de cuotas
        self.__tasa_interes = float(data.get('tasa_interes') or 0)
        frec_raw = (data.get('frecuencia_pago') or 'Mensual').strip()
        self.__frecuencia_pago = frec_raw.capitalize() if self.__tipo_venta == 'credito' else 'Contado'
        self.__cantidad_cuotas = int(data.get('cantidad_cuotas') or 1) if self.__tipo_venta == 'credito' else 1
        self.__fecha_inicio_cuotas = data.get('fecha_inicio_cuotas') or None

        cuotas_raw = data.get('cuotas')
        if isinstance(cuotas_raw, str):
            try:
                cuotas_raw = json.loads(cuotas_raw)
            except Exception:
                cuotas_raw = []
        self.__cuotas = cuotas_raw if isinstance(cuotas_raw, list) else []

        # Datos del Pago inicial
        self.__cod_metodo = data.get('cod_metodo')
        self.__cod_moneda = data.get('cod_moneda')
        self.__cod_banco = data.get('cod_banco')
        self.__cod_mon_digital = data.get('cod_mon_digital')
        self.__referencia = data.get('referencia', data.get('refencia', ''))

    # =========================================================================
    # GETTERS
    # =========================================================================
    @property
    def cedula_cliente(self): return self.__cedula_cliente

    @property
    def placa(self): return self.__placa

    @property
    def tipo_venta(self): return self.__tipo_venta

    @property
    def poder(self): return self.__poder

    @property
    def traspaso_papel(self): return self.__traspaso_papel

    @property
    def monto_recibido(self): return self.__monto_recibido

    @property
    def precio_total(self): return self.__precio_total

    @property
    def deuda_pendiente(self): return self.__deuda_pendiente

    @property
    def fecha_vencimiento(self): return self.__fecha_vencimiento

    @property
    def tasa_interes(self): return self.__tasa_interes

    @property
    def frecuencia_pago(self): return self.__frecuencia_pago

    @property
    def cantidad_cuotas(self): return self.__cantidad_cuotas

    @property
    def fecha_inicio_cuotas(self): return self.__fecha_inicio_cuotas

    @property
    def cuotas(self): return self.__cuotas

    @property
    def cod_metodo(self): return self.__cod_metodo

    @property
    def cod_moneda(self): return self.__cod_moneda

    @property
    def cod_banco(self): return self.__cod_banco

    @property
    def cod_mon_digital(self): return self.__cod_mon_digital

    @property
    def referencia(self): return self.__referencia

    # =========================================================================
    # CATÁLOGOS AUXILIARES
    # =========================================================================
    @staticmethod
    def obtener_tasa_actual():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT valor FROM tasa_cambio ORDER BY fecha DESC, id DESC LIMIT 1")
            fila = cursor.fetchone()
            return float(fila['valor']) if fila and fila.get('valor') is not None else 0.0
        except Exception as e:
            print(f"Error al obtener tasa actual: {e}")
            return 0.0
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_bancos():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM banco WHERE estado = 'Activo'")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_metodos_pago():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM metodo_pago WHERE estado = 'Activo'")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_monedas():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM moneda WHERE estado = 'Activo'")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_moneda_digital():
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM moneda_digital WHERE estado = 1")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_clientes():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT cedula_usuario, nombre, apellido FROM t_usuario WHERE estado = 1")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def buscar_por_placa(placa):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            sql = """
                SELECT v.placa,
                       m.nombre_marca AS marca,
                       mo.nombre_modelo AS modelo,
                       v.anio,
                       v.color,
                       tv.nombre_tipo AS tipo,
                       c.precio,
                       c.estado,
                       i.URL AS foto
                FROM vehiculo v
                INNER JOIN catalogo c ON v.placa = c.placa
                INNER JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
                INNER JOIN marca m ON mo.cod_marca = m.cod_marca
                INNER JOIN tipo_vehiculo tv ON v.cod_tipo = tv.cod_tipo
                LEFT JOIN imagen i ON v.placa = i.placa
                WHERE v.placa = %s AND v.estado = 'Disponible'
                LIMIT 1
            """
            cursor.execute(sql, (placa.strip().upper(),))
            vehiculo = cursor.fetchone()
            if vehiculo:
                vehiculo['precio'] = float(vehiculo['precio'])
                return {'exito': True, 'vehiculo': vehiculo}
            return None
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def buscar_cliente(termino):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        try:
            sql = """
                SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo
                FROM t_usuario
                WHERE (
                    CAST(cedula_usuario AS CHAR) LIKE %s
                    OR nombre LIKE %s
                    OR apellido LIKE %s
                    OR CONCAT(nombre, ' ', apellido) LIKE %s
                )
            """
            busqueda = f"%{termino}%"
            cursor.execute(sql, (busqueda, busqueda, busqueda, busqueda))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    # =========================================================================
    # REGISTRO TRANSACCIONAL DE VENTA Y CUOTAS
    # =========================================================================
    def registrar(self, cedula_usuario):
        from utils.validaciones_ventas import validar_registro_venta

        verificacion = validar_registro_venta(self)
        if not verificacion["status"]:
            return verificacion

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()

        try:
            metodo = str(self.__cod_metodo or '')
            METODO_EFECTIVO = '2'
            METODOS_BANCARIOS = {'3', '5'}
            METODOS_DIGITALES = {'1', '4', '6'}

            # 1. REGISTRAR VENTA
            sql_venta = "INSERT INTO ventas (estado, fecha_venta, tipo_venta, cedula_usuario) VALUES (%s, CURDATE(), %s, %s)"
            cursor.execute(sql_venta, ('procesada', self.__tipo_venta, self.__cedula_cliente))
            cod_venta = cursor.lastrowid

            # 2. REGISTRAR DETALLE DE VENTA
            sql_det_venta = "INSERT INTO det_venta (poder, traspaso_papel, precio, placa, cod_venta) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_det_venta, (self.__poder, self.__traspaso_papel, self.__precio_total, self.__placa, cod_venta))

            # 3. CALCULAR MONTOS Y REGISTRAR CUENTA POR COBRAR
            if self.__tipo_venta == 'credito':
                saldo_base = max(0.0, self.__precio_total - self.__monto_recibido)
                monto_interes = round(saldo_base * (self.__tasa_interes / 100.0), 2)
                deuda_total_guardar = round(self.__precio_total + monto_interes, 2)
                deuda_restante = max(0.0, round(saldo_base + monto_interes, 2))
                monto_inicial_guardar = round(self.__monto_recibido, 2)

                # Preparar lista de cuotas (personalizadas o generadas)
                if self.__cuotas and len(self.__cuotas) == self.__cantidad_cuotas:
                    lista_cuotas = [
                        {
                            'numero_cuota': int(c.get('numero_cuota') or idx + 1),
                            'monto_cuota': round(float(c['monto_cuota']), 2),
                            'fecha_vencimiento': str(c['fecha_vencimiento'])[:10]
                        }
                        for idx, c in enumerate(self.__cuotas)
                    ]
                else:
                    lista_cuotas = _generar_lista_cuotas(
                        deuda_restante,
                        self.__cantidad_cuotas,
                        self.__frecuencia_pago,
                        self.__fecha_inicio_cuotas
                    )

                fecha_inicio_guardar = (
                    self.__fecha_inicio_cuotas
                    or (lista_cuotas[0]['fecha_vencimiento'] if lista_cuotas else None)
                )
                fecha_venc_final = (
                    lista_cuotas[-1]['fecha_vencimiento']
                    if lista_cuotas
                    else self.__fecha_vencimiento
                )
                fecha_venc_dt = f"{fecha_venc_final} 23:59:59" if fecha_venc_final else None
            else:
                deuda_total_guardar = round(self.__precio_total, 2)
                monto_inicial_guardar = round(self.__precio_total, 2)
                deuda_restante = 0.0
                fecha_inicio_guardar = None
                fecha_venc_dt = None
                lista_cuotas = []

            estado_cuenta = 'pagado' if deuda_restante <= 0 else 'pendiente'
            sql_cxc = """
                INSERT INTO cuentas_por_cobrar (
                    deuda_total, monto_inicial, tasa_interes, frecuencia_pago,
                    cantidad_cuotas, deuda, fecha_emision, fecha_inicio_cuotas,
                    fecha_vencimiento, estado, cod_venta
                ) VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, %s, %s, %s)
            """
            cursor.execute(sql_cxc, (
                deuda_total_guardar,
                monto_inicial_guardar,
                self.__tasa_interes if self.__tipo_venta == 'credito' else 0.0,
                self.__frecuencia_pago,
                self.__cantidad_cuotas,
                deuda_restante,
                fecha_inicio_guardar,
                fecha_venc_dt,
                estado_cuenta,
                cod_venta
            ))
            cod_cuentas = cursor.lastrowid

            # 4. INSERTAR CUOTAS SI ES CRÉDITO
            if self.__tipo_venta == 'credito' and lista_cuotas:
                sql_cuota = """
                    INSERT INTO cuotas (
                        cod_cuentas, numero_cuota, monto_cuota, monto_pagado, fecha_vencimiento, estado
                    ) VALUES (%s, %s, %s, 0.00, %s, 'Pendiente')
                """
                for cuota in lista_cuotas:
                    cursor.execute(sql_cuota, (
                        cod_cuentas,
                        cuota['numero_cuota'],
                        cuota['monto_cuota'],
                        cuota['fecha_vencimiento']
                    ))

            # 5. REGISTRAR PAGO INICIAL (si recibió monto > 0)
            if self.__monto_recibido > 0:
                referencia = self.__referencia or ''
                sql_pago_c = "INSERT INTO pago_cuentas (monto_abonado, fecha_pago, referencia, estado, cod_cuentas) VALUES (%s, NOW(), %s, %s, %s)"
                cursor.execute(sql_pago_c, (self.__monto_recibido, referencia, 'Procesado', cod_cuentas))
                cod_pagos = cursor.lastrowid

                cod_moneda = self.__cod_moneda if (metodo == METODO_EFECTIVO or metodo in METODOS_BANCARIOS) else None

                sql_det_pago = "INSERT INTO det_pago (tipo_pago, fecha_det_pago, descripcion, cod_pagos, cod_metodo, cod_moneda) VALUES (%s, NOW(), %s, %s, %s, %s)"
                descripcion = f"Pago inicial - Venta {self.__tipo_venta}"
                cursor.execute(sql_det_pago, (self.__tipo_venta, descripcion, cod_pagos, self.__cod_metodo, cod_moneda))
                cod_det_pago = cursor.lastrowid

                if metodo in METODOS_DIGITALES:
                    sql_digital = "INSERT INTO det_nom_digital (monto, referencia, cod_mon_digital, cod_det_pago) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_digital, (self.__monto_recibido, referencia, self.__cod_mon_digital, cod_det_pago))
                elif metodo in METODOS_BANCARIOS:
                    sql_banco = "INSERT INTO det_banco (monto, referencia, cod_banco, cod_det_pago) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_banco, (self.__monto_recibido, referencia, self.__cod_banco, cod_det_pago))
                elif metodo == METODO_EFECTIVO:
                    pass
                else:
                    raise ValueError(f"Método de pago no reconocido: {self.__cod_metodo}")

            # 6. ACTUALIZAR ESTADO DEL VEHÍCULO
            cursor.execute("UPDATE vehiculo SET estado = 'Vendido' WHERE placa = %s", (self.__placa,))

            # 7. BITÁCORA
            Bitacora.registrar(cedula_usuario, cod_accion=1, cod_modulo=14)

            conexion.commit()
            return {"status": True, "cod_venta": cod_venta}

        except Exception as e:
            conexion.rollback()
            print(f"ERROR TRANSACCIONAL: {str(e)}")
            return {"status": False, "error": str(e)}

        finally:
            cursor.close()
            conexion.close()

    # =========================================================================
    # OBTENER DATOS COMPLETOS PARA COMPROBANTE PDF
    # =========================================================================
    @staticmethod
    def obtener_datos_factura(cod_venta):
        conexion = None
        cursor = None
        conexion_seguridad = None
        cursor_cliente = None

        try:
            conexion = ConexionBD.obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            sql_venta = """
                SELECT
                    v.cod_venta,
                    v.estado AS estado_venta,
                    v.fecha_venta,
                    v.tipo_venta,
                    v.cedula_usuario AS cedula_cliente,
                    dv.placa,
                    dv.poder,
                    dv.traspaso_papel,
                    dv.precio,
                    vh.anio,
                    vh.color,
                    m.nombre_marca AS marca,
                    mo.nombre_modelo AS modelo,
                    tv.nombre_tipo AS tipo_vehiculo,
                    cxc.cod_cuentas,
                    cxc.deuda_total,
                    cxc.monto_inicial,
                    cxc.tasa_interes,
                    cxc.frecuencia_pago,
                    cxc.cantidad_cuotas,
                    cxc.fecha_inicio_cuotas,
                    cxc.deuda AS saldo_pendiente,
                    cxc.fecha_emision,
                    cxc.fecha_vencimiento,
                    cxc.estado AS estado_cuenta,
                    doc.original_totalPropiedad,
                    doc.experticia_transito,
                    doc.certificado_origen,
                    doc.carnet_circulacion,
                    doc.reserva_dominio,
                    doc.garantia_vehiculo,
                    doc.certificado_garantia,
                    doc.manual_vehiculoGarantia,
                    doc.finiquito,
                    doc.resguardo,
                    doc.fecha_transferencia,
                    doc.seguro,
                    doc.factura_compra,
                    doc.otro_documento
                FROM ventas v
                INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
                INNER JOIN vehiculo vh ON dv.placa = vh.placa
                INNER JOIN modelo mo ON vh.cod_modelo = mo.cod_modelo
                INNER JOIN marca m ON mo.cod_marca = m.cod_marca
                INNER JOIN tipo_vehiculo tv ON vh.cod_tipo = tv.cod_tipo
                LEFT JOIN cuentas_por_cobrar cxc ON v.cod_venta = cxc.cod_venta
                LEFT JOIN documentacion doc ON vh.cod_documento = doc.cod_documento
                WHERE v.cod_venta = %s
                LIMIT 1
            """
            cursor.execute(sql_venta, (cod_venta,))
            venta = cursor.fetchone()
            if not venta:
                return None

            # TOTAL PAGADO (excluyendo pagos anulados)
            sql_total_pagado = """
                SELECT IFNULL(SUM(pc.monto_abonado), 0) AS total_pagado
                FROM cuentas_por_cobrar cxc
                LEFT JOIN pago_cuentas pc
                    ON cxc.cod_cuentas = pc.cod_cuentas AND pc.estado <> 'Anulado'
                WHERE cxc.cod_venta = %s
            """
            cursor.execute(sql_total_pagado, (cod_venta,))
            resultado_total = cursor.fetchone()
            total_pagado = float(resultado_total['total_pagado']) if resultado_total else 0.0

            # PAGOS REALIZADOS (excluyendo anulados)
            sql_pagos = """
                SELECT
                    pc.cod_pagos,
                    pc.monto_abonado,
                    pc.fecha_pago,
                    pc.referencia,
                    dp.tipo_pago,
                    dp.descripcion,
                    dp.cod_moneda,
                    dp.cod_metodo,
                    db.cod_banco,
                    dnd.cod_mon_digital
                FROM cuentas_por_cobrar cxc
                INNER JOIN pago_cuentas pc ON cxc.cod_cuentas = pc.cod_cuentas
                LEFT JOIN det_pago dp ON pc.cod_pagos = dp.cod_pagos
                LEFT JOIN det_banco db ON dp.cod_det_pago = db.cod_det_pago
                LEFT JOIN det_nom_digital dnd ON dp.cod_det_pago = dnd.cod_det_pago
                WHERE cxc.cod_venta = %s AND pc.estado <> 'Anulado'
                ORDER BY pc.fecha_pago ASC, pc.cod_pagos ASC
            """
            cursor.execute(sql_pagos, (cod_venta,))
            pagos = cursor.fetchall()

            # CUOTAS DEL CRÉDITO
            cuotas = []
            if venta.get('cod_cuentas'):
                cursor.execute("""
                    SELECT
                        cod_cuota,
                        numero_cuota,
                        monto_cuota,
                        monto_pagado,
                        fecha_vencimiento,
                        fecha_pago,
                        estado,
                        CASE
                            WHEN estado IN ('Pendiente', 'Parcial') AND fecha_vencimiento < CURDATE() THEN 'Vencida'
                            ELSE estado
                        END AS estado_actual
                    FROM cuotas
                    WHERE cod_cuentas = %s
                    ORDER BY numero_cuota ASC
                """, (venta['cod_cuentas'],))
                cuotas = cursor.fetchall()

            # CLIENTE
            conexion_seguridad = ConexionBD.obtener_conexion_seguridad()
            cursor_cliente = conexion_seguridad.cursor(dictionary=True)
            cursor_cliente.execute("""
                SELECT cedula_usuario, nombre, apellido, telefono, direccion, correo
                FROM t_usuario
                WHERE cedula_usuario = %s
                LIMIT 1
            """, (venta['cedula_cliente'],))
            cliente = cursor_cliente.fetchone()

            if not cliente:
                cliente = {
                    'cedula_usuario': venta['cedula_cliente'],
                    'nombre': 'Cliente',
                    'apellido': 'no disponible',
                    'telefono': '',
                    'direccion': '',
                    'correo': ''
                }

            venta['precio'] = float(venta['precio'] or 0)
            venta['deuda_total'] = float(venta['deuda_total'] or 0)
            venta['saldo_pendiente'] = float(venta['saldo_pendiente'] or 0)
            venta['total_pagado'] = total_pagado

            for pago in pagos:
                pago['monto_abonado'] = float(pago['monto_abonado'] or 0)

            return {
                'venta': venta,
                'cliente': cliente,
                'pagos': pagos,
                'cuotas': cuotas
            }

        except Exception as e:
            print(f"Error al obtener datos para comprobante de venta #{cod_venta}: {e}")
            return None

        finally:
            if cursor_cliente: cursor_cliente.close()
            if conexion_seguridad: conexion_seguridad.close()
            if cursor: cursor.close()
            if conexion: conexion.close()

    # =========================================================================
    # LISTADO DE VENTAS (CON PLAN DE CUOTAS)
    # =========================================================================
    @staticmethod
    def obtener_todas(cedula_usuario):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        conexion_seg = None
        cursor_seg = None

        sql = """
            SELECT
                v.cod_venta,
                v.fecha_venta,
                v.estado AS estado_venta,
                v.tipo_venta,
                v.cedula_usuario,
                dv.placa,
                veh.color AS color_vehiculo,
                veh.anio AS anio_vehiculo,
                veh.kilometraje AS kilometraje_vehiculo,
                veh.estado AS estado_vehiculo,
                m.nombre_modelo AS modelo_vehiculo,
                mar.nombre_marca AS marca_vehiculo,
                cxc.cod_cuentas,
                cxc.fecha_vencimiento,
                cxc.fecha_inicio_cuotas,
                cxc.deuda_total,
                cxc.monto_inicial,
                cxc.tasa_interes,
                cxc.frecuencia_pago,
                cxc.cantidad_cuotas,
                cxc.deuda AS saldo_pendiente,
                cxc.estado AS estado_cuenta,
                IFNULL(SUM(CASE WHEN pc.estado <> 'Anulado' THEN pc.monto_abonado ELSE 0 END), 0) AS monto_abonado,
                MAX(CASE WHEN pc.estado <> 'Anulado' THEN pc.fecha_pago ELSE NULL END) AS ultimo_pago
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            LEFT JOIN vehiculo veh ON dv.placa = veh.placa
            LEFT JOIN modelo m ON veh.cod_modelo = m.cod_modelo
            LEFT JOIN marca mar ON m.cod_marca = mar.cod_marca
            INNER JOIN cuentas_por_cobrar cxc ON v.cod_venta = cxc.cod_venta
            LEFT JOIN pago_cuentas pc ON cxc.cod_cuentas = pc.cod_cuentas
            GROUP BY
                v.cod_venta, v.fecha_venta, v.estado, v.tipo_venta,
                v.cedula_usuario, dv.placa, veh.color, veh.anio,
                veh.kilometraje, veh.estado, m.nombre_modelo, mar.nombre_marca,
                cxc.cod_cuentas, cxc.fecha_vencimiento, cxc.fecha_inicio_cuotas,
                cxc.deuda_total, cxc.monto_inicial, cxc.tasa_interes,
                cxc.frecuencia_pago, cxc.cantidad_cuotas, cxc.deuda, cxc.estado
            ORDER BY v.fecha_venta DESC, v.cod_venta DESC
        """
        try:
            cursor.execute(sql)
            ventas = cursor.fetchall()

            # Cargar cuotas agrupadas por cuenta para mostrar cronograma en detalle
            cuotas_por_cuenta = {}
            cods_cuentas = [v['cod_cuentas'] for v in ventas if v.get('cod_cuentas')]
            if cods_cuentas:
                placeholders = ','.join(['%s'] * len(cods_cuentas))
                cursor.execute(f"""
                    SELECT
                        cod_cuota,
                        cod_cuentas,
                        numero_cuota,
                        monto_cuota,
                        monto_pagado,
                        fecha_vencimiento,
                        fecha_pago,
                        estado,
                        CASE
                            WHEN estado IN ('Pendiente', 'Parcial') AND fecha_vencimiento < CURDATE() THEN 'Vencida'
                            ELSE estado
                        END AS estado_actual
                    FROM cuotas
                    WHERE cod_cuentas IN ({placeholders})
                    ORDER BY cod_cuentas, numero_cuota ASC
                """, tuple(cods_cuentas))
                for c in cursor.fetchall():
                    cuotas_por_cuenta.setdefault(c['cod_cuentas'], []).append(c)

            # Cargar nombres de clientes
            mapa_clientes = {}
            try:
                conexion_seg = ConexionBD.obtener_conexion_seguridad()
                cursor_seg = conexion_seg.cursor(dictionary=True)
                cursor_seg.execute("SELECT cedula_usuario, nombre, apellido FROM t_usuario")
                for u in cursor_seg.fetchall():
                    mapa_clientes[str(u['cedula_usuario'])] = f"{u['nombre']} {u['apellido']}".strip()
            except Exception as e_seg:
                print(f"Advertencia cargando nombres de clientes: {e_seg}")

            for v in ventas:
                lista_c = cuotas_por_cuenta.get(v.get('cod_cuentas'), [])
                v['cuotas'] = lista_c
                v['cuotas_pagadas'] = sum(1 for c in lista_c if str(c.get('estado', '')).lower() == 'pagada')
                v['cuotas_vencidas'] = sum(1 for c in lista_c if str(c.get('estado_actual', '')).lower() == 'vencida')
                v['nombre_cliente'] = mapa_clientes.get(str(v.get('cedula_usuario')), '')

            Bitacora.registrar(cedula_usuario, cod_accion=2, cod_modulo=14)
            return ventas
        except Exception as e:
            print(f"Error al listar ventas: {e}")
            return []
        finally:
            if cursor_seg: cursor_seg.close()
            if conexion_seg: conexion_seg.close()
            cursor.close()
            conexion.close()

    # =========================================================================
    # ELIMINADO LÓGICO DE VENTA
    # =========================================================================
    @staticmethod
    def eliminar(cod_venta, cedula_usuario):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT placa FROM det_venta WHERE cod_venta = %s", (cod_venta,))
            res = cursor.fetchone()
            if res:
                placa = res['placa']
                cursor.execute("UPDATE vehiculo SET estado = 'Disponible' WHERE placa = %s", (placa,))
                cursor.execute("UPDATE catalogo SET estado = 'Activo' WHERE placa = %s", (placa,))

            cursor.execute("UPDATE ventas SET estado = 'Anulada' WHERE cod_venta = %s", (cod_venta,))
            cursor.execute(
                "UPDATE cuentas_por_cobrar SET estado = 'anulada', deuda = 0 WHERE cod_venta = %s",
                (cod_venta,)
            )
            cursor.execute("""
                UPDATE pago_cuentas pc
                INNER JOIN cuentas_por_cobrar cxc ON pc.cod_cuentas = cxc.cod_cuentas
                SET pc.estado = 'Anulado'
                WHERE cxc.cod_venta = %s AND pc.estado <> 'Anulado'
            """, (cod_venta,))

            Bitacora.registrar(cedula_usuario, cod_accion=4, cod_modulo=14)
            conexion.commit()
            return True
        except Exception as e:
            conexion.rollback()
            print(f"Error al aplicar eliminado lógico en venta: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()

    # =========================================================================
    # ACTUALIZACIÓN DE VENTA A CRÉDITO Y SU PLAN DE CUOTAS
    # =========================================================================
    @staticmethod
    def actualizar(data, cedula_usuario):
        from utils.validaciones_ventas import validar_actualizacion_venta

        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT v.tipo_venta, cxc.cod_cuentas, cxc.deuda_total, cxc.frecuencia_pago,
                       cxc.cantidad_cuotas, cxc.fecha_inicio_cuotas
                FROM ventas v
                INNER JOIN cuentas_por_cobrar cxc ON v.cod_venta = cxc.cod_venta
                WHERE v.cod_venta = %s
                LIMIT 1
            """, (data.get('cod_venta'),))
            venta_actual = cursor.fetchone()
            if not venta_actual:
                return {"status": False, "error": "La venta indicada no existe."}

            data['tipo_venta'] = venta_actual['tipo_venta']
            verificacion = validar_actualizacion_venta(data)
            if not verificacion["status"]:
                return verificacion

            if venta_actual['tipo_venta'] != 'credito':
                return {"status": False, "error": "Solo se pueden editar ventas a crédito."}

            cod_cuentas = venta_actual['cod_cuentas']

            # Total abonado válido (sin anulados)
            cursor.execute("""
                SELECT IFNULL(SUM(monto_abonado), 0) AS total_pagado
                FROM pago_cuentas
                WHERE cod_cuentas = %s AND estado <> 'Anulado'
            """, (cod_cuentas,))
            res_pagos = cursor.fetchone()
            total_pagado = float(res_pagos['total_pagado']) if res_pagos else 0.0

            nueva_deuda_total = round(float(data['deuda_total']), 2)
            if nueva_deuda_total < total_pagado:
                return {
                    "status": False,
                    "error": f"La deuda total no puede ser menor al monto ya pagado (${total_pagado:,.2f})."
                }

            nueva_deuda_pendiente = max(0.0, round(nueva_deuda_total - total_pagado, 2))
            nuevo_estado = 'pagado' if nueva_deuda_pendiente <= 0 else 'pendiente'

            # Verificar si ya existen cuotas con abonos aplicados
            cursor.execute("""
                SELECT COUNT(*) AS con_pagos
                FROM cuotas
                WHERE cod_cuentas = %s AND monto_pagado > 0
            """, (cod_cuentas,))
            cuotas_con_pagos = int(cursor.fetchone()['con_pagos'])

            nueva_frec = (data.get('frecuencia_pago') or venta_actual.get('frecuencia_pago') or 'Mensual').strip().capitalize()
            nueva_cant = int(data.get('cantidad_cuotas') or venta_actual.get('cantidad_cuotas') or 1)
            nueva_inicio = data.get('fecha_inicio_cuotas') or venta_actual.get('fecha_inicio_cuotas')
            fecha_venc = data.get('fecha_vencimiento') or None

            if cuotas_con_pagos == 0 and nueva_deuda_pendiente > 0:
                lista_cuotas = _generar_lista_cuotas(
                    nueva_deuda_pendiente,
                    nueva_cant,
                    nueva_frec,
                    nueva_inicio
                )
                cursor.execute("DELETE FROM cuotas WHERE cod_cuentas = %s", (cod_cuentas,))
                for c in lista_cuotas:
                    cursor.execute("""
                        INSERT INTO cuotas (cod_cuentas, numero_cuota, monto_cuota, monto_pagado, fecha_vencimiento, estado)
                        VALUES (%s, %s, %s, 0.00, %s, 'Pendiente')
                    """, (cod_cuentas, c['numero_cuota'], c['monto_cuota'], c['fecha_vencimiento']))

                if not fecha_venc and lista_cuotas:
                    fecha_venc = lista_cuotas[-1]['fecha_vencimiento']
                if not nueva_inicio and lista_cuotas:
                    nueva_inicio = lista_cuotas[0]['fecha_vencimiento']

                cursor.execute("""
                    UPDATE cuentas_por_cobrar
                    SET deuda_total = %s,
                        deuda = %s,
                        frecuencia_pago = %s,
                        cantidad_cuotas = %s,
                        fecha_inicio_cuotas = %s,
                        fecha_vencimiento = %s,
                        estado = %s
                    WHERE cod_venta = %s
                """, (
                    nueva_deuda_total,
                    nueva_deuda_pendiente,
                    nueva_frec,
                    nueva_cant,
                    nueva_inicio,
                    f"{fecha_venc} 23:59:59" if fecha_venc else None,
                    nuevo_estado,
                    data['cod_venta']
                ))
            else:
                # Si ya tiene pagos aplicados a cuotas, solo actualiza montos/fecha límite sin destruir el historial de cuotas
                cursor.execute("""
                    UPDATE cuentas_por_cobrar
                    SET deuda_total = %s,
                        deuda = %s,
                        fecha_vencimiento = %s,
                        estado = %s
                    WHERE cod_venta = %s
                """, (
                    nueva_deuda_total,
                    nueva_deuda_pendiente,
                    f"{fecha_venc} 23:59:59" if fecha_venc else None,
                    nuevo_estado,
                    data['cod_venta']
                ))

            Bitacora.registrar(cedula_usuario, cod_accion=3, cod_modulo=14)
            conexion.commit()
            return {"status": True}

        except Exception as e:
            conexion.rollback()
            print(f"Error al editar venta: {e}")
            return {"status": False, "error": str(e)}
        finally:
            cursor.close()
            conexion.close()