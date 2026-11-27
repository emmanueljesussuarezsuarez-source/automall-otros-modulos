import random
import re
from datetime import date, timedelta
import requests
from locust import HttpUser, task, between, events

# ==============================================================================
# CONFIGURACIÓN DE DATOS DE PRUEBA
# ==============================================================================
CREDENCIALES = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}

PLACAS_RESPALDO = ["MN012OP", "QR345ST", "UV678WX"]

# Estado compartido preparado antes de iniciar los usuarios virtuales
CTX_PAGOS = {
    "host": "http://127.0.0.1:5000",
    "cedula_cliente": None,
    "cod_cuentas": None,
    "cod_venta_temporal": None,
    "cod_metodo_binance": "1",
    "cod_moneda_usd": "1",
    "cod_banco_provincial": "1",
    "cod_mon_digital_usdt": "1",
    "clientes": [],
}


def extraer_option_por_texto(html, select_id, texto_buscar, default="1"):
    patron_select = rf'<select[^>]*id=["\']{select_id}["\'][^>]*>(.*?)</select>'
    bloque = re.search(patron_select, html, re.IGNORECASE | re.DOTALL)
    if not bloque:
        return default

    opciones = re.findall(
        r'<option[^>]*value=["\']([^"\']+)["\'][^>]*>(.*?)</option>',
        bloque.group(1),
        re.IGNORECASE | re.DOTALL,
    )
    for val, label in opciones:
        if texto_buscar.lower() in label.lower():
            return val.strip()

    for val, _ in opciones:
        if val.strip():
            return val.strip()
    return default


def extraer_lista_clientes(html):
    patron_select = r'<select[^>]*id=["\']select_cliente_lista["\'][^>]*>(.*?)</select>'
    bloque = re.search(patron_select, html, re.IGNORECASE | re.DOTALL)
    if not bloque:
        return []
    valores = re.findall(r'<option[^>]*value=["\']([^"\']+)["\']', bloque.group(1))
    return [v.strip() for v in valores if v.strip()]


@events.test_start.add_listener
def preparar_cuenta_para_pagos(environment, **kwargs):
    """Garantiza que exista al menos una cuenta a crédito pendiente para probar pagos."""
    host = (environment.host or "http://127.0.0.1:5000").rstrip("/")
    CTX_PAGOS["host"] = host
    CTX_PAGOS["cod_venta_temporal"] = None
    CTX_PAGOS["cod_cuentas"] = None
    CTX_PAGOS["cedula_cliente"] = None

    s = requests.Session()
    resp_login = s.post(f"{host}/login", json=CREDENCIALES, timeout=10)
    if resp_login.status_code != 200 or resp_login.json().get("status") != "success":
        print("⚠️ No se pudo iniciar sesión en test_start para preparar datos de Pagos.")
        return

    # 1. Obtener catálogos reales y lista de clientes
    resp_vista = s.get(f"{host}/ventas/registrar_venta", timeout=10)
    if resp_vista.status_code == 200:
        html = resp_vista.text
        CTX_PAGOS["clientes"] = extraer_lista_clientes(html)
        CTX_PAGOS["cod_metodo_binance"] = extraer_option_por_texto(html, "cod_metodo", "Binance", "1")
        CTX_PAGOS["cod_moneda_usd"] = extraer_option_por_texto(html, "cod_moneda", "Dolar", "1")
        CTX_PAGOS["cod_banco_provincial"] = extraer_option_por_texto(html, "cod_banco", "Provincial", "1")
        CTX_PAGOS["cod_mon_digital_usdt"] = extraer_option_por_texto(html, "cod_mon_digital", "USDT", "1")

    # 2. Buscar si algún cliente ya tiene una deuda pendiente >= $50
    for ced in CTX_PAGOS["clientes"][:15]:
        r_deudas = s.get(f"{host}/pagos/obtener_deudas/{ced}", timeout=10)
        if r_deudas.status_code == 200:
            deudas = r_deudas.json()
            for d in deudas:
                if float(d.get("saldo_pendiente") or 0) >= 50:
                    CTX_PAGOS["cedula_cliente"] = str(ced)
                    CTX_PAGOS["cod_cuentas"] = d["cod_cuentas"]
                    print(f"✅ Usando deuda existente cod_cuentas={d['cod_cuentas']} del cliente {ced}")
                    return

    # 3. Si no hay deudas activas, crear 1 venta temporal a crédito para probar Pagos
    if not CTX_PAGOS["clientes"]:
        print("⚠️ No hay clientes disponibles en BD para crear deuda temporal.")
        return

    cedula_cliente = str(CTX_PAGOS["clientes"][0])
    for placa in PLACAS_RESPALDO:
        r_veh = s.get(f"{host}/ventas/api/vehiculo/{placa}", timeout=10)
        if r_veh.status_code == 200:
            precio = float(r_veh.json().get("vehiculo", {}).get("precio") or 10000.0)
            inicial = round(precio * 0.20, 2)
            deuda_pend = round((precio - inicial) * 1.05, 2)
            hoy = date.today()
            payload_venta = {
                "cedula_cliente": cedula_cliente,
                "placa": placa,
                "tipo_venta": "credito",
                "poder": 1,
                "traspaso_papel": 1,
                "precio_vehiculo": precio,
                "monto_recibido": inicial,
                "deuda_pendiente": deuda_pend,
                "tasa_interes": 5.0,
                "frecuencia_pago": "Mensual",
                "cantidad_cuotas": 4,
                "fecha_inicio_cuotas": (hoy + timedelta(days=30)).strftime("%Y-%m-%d"),
                "fecha_vencimiento": (hoy + timedelta(days=120)).strftime("%Y-%m-%d"),
                "cod_metodo": CTX_PAGOS["cod_metodo_binance"],
                "cod_moneda": CTX_PAGOS["cod_moneda_usd"],
                "cod_banco": CTX_PAGOS["cod_banco_provincial"],
                "cod_mon_digital": CTX_PAGOS["cod_mon_digital_usdt"],
                "referencia": str(random.randint(10000000, 99999999)),
            }
            r_crear = s.post(f"{host}/ventas/registrar_venta", json=payload_venta, timeout=10)
            if r_crear.status_code == 200 and r_crear.json().get("exito"):
                cod_venta_temp = r_crear.json().get("cod_venta")
                CTX_PAGOS["cod_venta_temporal"] = cod_venta_temp
                r_deudas = s.get(f"{host}/pagos/obtener_deudas/{cedula_cliente}", timeout=10)
                if r_deudas.status_code == 200:
                    for d in r_deudas.json():
                        if d.get("cod_venta") == cod_venta_temp:
                            CTX_PAGOS["cedula_cliente"] = cedula_cliente
                            CTX_PAGOS["cod_cuentas"] = d["cod_cuentas"]
                            print(f"✅ Creada venta temporal a crédito #{cod_venta_temp} (cod_cuentas={d['cod_cuentas']}) para probar Pagos")
                            return


@events.test_stop.add_listener
def limpiar_venta_temporal(environment, **kwargs):
    """Si creamos una venta temporal a crédito para la prueba, la anulamos al finalizar."""
    cod_venta_temp = CTX_PAGOS.get("cod_venta_temporal")
    if not cod_venta_temp:
        return
    host = CTX_PAGOS["host"]
    s = requests.Session()
    r_login = s.post(f"{host}/login", json=CREDENCIALES, timeout=10)
    if r_login.status_code == 200 and r_login.json().get("status") == "success":
        s.post(f"{host}/ventas/eliminar/{cod_venta_temp}", timeout=10)
        print(f"🧹 Venta temporal #{cod_venta_temp} anulada y vehículo liberado.")


class UsuarioPagos(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.facturas_pagos = []
        with self.client.post(
            "/login",
            json=CREDENCIALES,
            name="POST /login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code} en login")
                return
            data = resp.json()
            if data.get("status") == "success":
                resp.success()
            else:
                resp.failure(f"Login rechazado: {data.get('message')}")

    # ==========================================================================
    # CASO 1: Vistas principales (Listar Cliente, Listar Admin y Registrar Pago)
    # ==========================================================================
    @task(3)
    def listar_pagos_cliente(self):
        with self.client.get(
            "/pagos/listar_pagos",
            name="GET /pagos/listar_pagos",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} en listar_pagos")

    @task(4)
    def listar_pagos_admin(self):
        with self.client.get(
            "/pagos/listar_admin",
            name="GET /pagos/listar_admin",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                ids = [i for i in re.findall(r"/pagos/factura/(\d+)", resp.text) if int(i) > 0]
                if ids:
                    self.facturas_pagos = list(set(ids))
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} en listar_admin")

    @task(3)
    def ver_formulario_registrar_pago(self):
        with self.client.get(
            "/pagos/registrar_pago",
            name="GET /pagos/registrar_pago",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} en registrar_pago")

    # ==========================================================================
    # CASO 2: Consultas API de Deudas y Cuotas
    # ==========================================================================
    @task(3)
    def api_obtener_deudas_cliente(self):
        cedula = CTX_PAGOS.get("cedula_cliente") or (
            random.choice(CTX_PAGOS["clientes"]) if CTX_PAGOS["clientes"] else None
        )
        if not cedula:
            return
        with self.client.get(
            f"/pagos/obtener_deudas/{cedula}",
            name="GET /pagos/obtener_deudas/[cedula]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and isinstance(resp.json(), list):
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} consultando deudas de {cedula}")

    @task(3)
    def api_obtener_cuotas_cuenta(self):
        cod_cuentas = CTX_PAGOS.get("cod_cuentas")
        if not cod_cuentas:
            return
        with self.client.get(
            f"/pagos/api/cuotas/{cod_cuentas}",
            name="GET /pagos/api/cuotas/[cod_cuentas]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and resp.json().get("exito"):
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} consultando cuotas de cuenta #{cod_cuentas}")

    @task(1)
    def api_cuotas_inexistente(self):
        """Caso negativo controlado: cuenta inexistente debe devolver 404."""
        with self.client.get(
            "/pagos/api/cuotas/9999999",
            name="GET /pagos/api/cuotas/[no_existe_404]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()
            else:
                resp.failure(f"Se esperaba 404 y devolvió {resp.status_code}")

    # ==========================================================================
    # CASO 3: Generación de Comprobante PDF de Pago
    # ==========================================================================
    @task(2)
    def generar_pdf_pago_existente(self):
        if not self.facturas_pagos:
            return
        cod_pagos = random.choice(self.facturas_pagos)
        with self.client.get(
            f"/pagos/factura/{cod_pagos}",
            name="GET /pagos/factura/[cod_pagos] (PDF)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and "application/pdf" in resp.headers.get("Content-Type", ""):
                resp.success()
            else:
                resp.failure(f"Error generando PDF pago #{cod_pagos}: HTTP {resp.status_code}")

    # ==========================================================================
    # CASO 4: Flujo Transaccional Completo (Procesar Abono -> PDF -> Anular)
    # ==========================================================================
    @task(3)
    def flujo_procesar_y_anular_pago(self):
        cod_cuentas = CTX_PAGOS.get("cod_cuentas")
        if not cod_cuentas:
            return

        cod_pago_creado = None
        try:
            payload_pago = {
                "cod_cuentas": cod_cuentas,
                "monto_pago": 1.00,  # $1.00 USD para permitir alta concurrencia sin agotar saldo
                "cod_metodo": CTX_PAGOS["cod_metodo_binance"],
                "cod_moneda": CTX_PAGOS["cod_moneda_usd"],
                "cod_banco": CTX_PAGOS["cod_banco_provincial"],
                "cod_mon_digital": CTX_PAGOS["cod_mon_digital_usdt"],
                "referencia": str(random.randint(10000000, 99999999)),
                "descripcion": "Abono prueba de rendimiento Locust",
            }

            # 1. Procesar el abono (POST JSON)
            with self.client.post(
                "/pagos/procesar",
                json=payload_pago,
                name="POST /pagos/procesar",
                catch_response=True,
            ) as resp_proc:
                if resp_proc.status_code != 200:
                    try:
                        err = resp_proc.json().get("error", resp_proc.text)
                    except Exception:
                        err = resp_proc.text
                    resp_proc.failure(f"HTTP {resp_proc.status_code}: {err}")
                    return

                res = resp_proc.json()
                if not res.get("success"):
                    resp_proc.failure(f"Pago rechazado: {res.get('error')}")
                    return

                cod_pago_creado = res.get("cod_pagos")
                resp_proc.success()

            # 2. Descargar comprobante PDF del pago recién procesado
            if cod_pago_creado:
                with self.client.get(
                    f"/pagos/factura/{cod_pago_creado}",
                    name="GET /pagos/factura/[cod_pagos] (PDF)",
                    catch_response=True,
                ) as resp_pdf:
                    if resp_pdf.status_code == 200 and "application/pdf" in resp_pdf.headers.get("Content-Type", ""):
                        resp_pdf.success()
                    else:
                        resp_pdf.failure(f"Error PDF pago #{cod_pago_creado}: HTTP {resp_pdf.status_code}")

        finally:
            # 3. Anular el pago de prueba (POST Formulario HTML) para restaurar cuotas y deuda
            if cod_pago_creado:
                with self.client.post(
                    "/pagos/anular",
                    data={
                        "cod_pagos": str(cod_pago_creado),
                        "motivo": "Prueba de rendimiento Locust",
                    },
                    name="POST /pagos/anular (form)",
                    catch_response=True,
                ) as resp_anular:
                    if resp_anular.status_code != 200:
                        resp_anular.failure(f"HTTP {resp_anular.status_code} al anular pago #{cod_pago_creado}")
                    elif "No se pudo procesar la anulación" in resp_anular.text or "No se especificó el pago" in resp_anular.text:
                        resp_anular.failure(f"Falló la anulación del pago #{cod_pago_creado}")
                    else:
                        resp_anular.success()