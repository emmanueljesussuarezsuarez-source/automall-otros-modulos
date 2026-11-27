import random
import re
import string
from datetime import date, timedelta
from queue import Queue, Empty
from locust import HttpUser, task, between

# ==============================================================================
# CONFIGURACIÓN DE DATOS DE PRUEBA
# ==============================================================================
CREDENCIALES = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}

PLACAS_PRUEBA = ["MN012OP", "QR345ST", "UV678WX"]

# Cola thread-safe para que dos usuarios concurrentes no vendan la misma placa a la vez
placas_queue = Queue()
for p in PLACAS_PRUEBA:
    placas_queue.put(p)


def extraer_option_por_texto(html, select_id, texto_buscar, default="1"):
    """Busca un <select id='...'> en el HTML y extrae el value del option que coincida."""
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
    """Extrae las cédulas de clientes disponibles en el select de registrar_venta."""
    patron_select = r'<select[^>]*id=["\']select_cliente_lista["\'][^>]*>(.*?)</select>'
    bloque = re.search(patron_select, html, re.IGNORECASE | re.DOTALL)
    if not bloque:
        return []
    valores = re.findall(r'<option[^>]*value=["\']([^"\']+)["\']', bloque.group(1))
    return [v.strip() for v in valores if v.strip()]


class UsuarioVentas(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.clientes_disponibles = []
        self.cod_metodo_binance = "1"
        self.cod_moneda_usd = "1"
        self.cod_banco_provincial = "1"
        self.cod_mon_digital_usdt = "1"
        self.facturas_existentes = []

        with self.client.post(
            "/login",
            json=CREDENCIALES,
            name="POST /login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code} en login")
                return
            try:
                data = resp.json()
                if data.get("status") == "success":
                    resp.success()
                else:
                    resp.failure(f"Login rechazado: {data.get('message')}")
                    return
            except Exception as e:
                resp.failure(f"Respuesta de login no es JSON válido: {e}")
                return

        self._cargar_catalogos_vista()

    def _cargar_catalogos_vista(self):
        with self.client.get(
            "/ventas/registrar_venta",
            name="GET /ventas/registrar_venta",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error cargando vista ventas: HTTP {resp.status_code}")
                return
            html = resp.text
            self.clientes_disponibles = extraer_lista_clientes(html)
            self.cod_metodo_binance = extraer_option_por_texto(html, "cod_metodo", "Binance", "1")
            self.cod_moneda_usd = extraer_option_por_texto(html, "cod_moneda", "Dolar", "1")
            self.cod_banco_provincial = extraer_option_por_texto(html, "cod_banco", "Provincial", "1")
            self.cod_mon_digital_usdt = extraer_option_por_texto(html, "cod_mon_digital", "USDT", "1")
            resp.success()

    # ==========================================================================
    # CASO 1: Carga de vistas HTML (Catálogos y Listado)
    # ==========================================================================
    @task(3)
    def ver_formulario_registro(self):
        self._cargar_catalogos_vista()

    @task(4)
    def listar_ventas(self):
        with self.client.get(
            "/ventas/lista_ventas",
            name="GET /ventas/lista_ventas",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                ids = re.findall(r"/ventas/factura/(\d+)", resp.text)
                if ids:
                    self.facturas_existentes = list(set(ids))
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} al listar ventas")

    # ==========================================================================
    # CASO 2: Búsquedas API en tiempo real
    # ==========================================================================
    @task(3)
    def buscar_cliente_api(self):
        if not self.clientes_disponibles:
            return
        cedula = random.choice(self.clientes_disponibles)
        with self.client.get(
            f"/ventas/api/cliente/{cedula}",
            name="GET /ventas/api/cliente/[termino]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and resp.json().get("exito"):
                resp.success()
            else:
                resp.failure(f"Fallo buscando cliente {cedula}: HTTP {resp.status_code}")

    @task(1)
    def buscar_cliente_inexistente_api(self):
        with self.client.get(
            "/ventas/api/cliente/NOEXISTE_999999",
            name="GET /ventas/api/cliente/[no_existe_404]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()
            else:
                resp.failure(f"Se esperaba 404 y devolvió {resp.status_code}")

    @task(2)
    def buscar_vehiculo_api(self):
        placa = random.choice(PLACAS_PRUEBA)
        with self.client.get(
            f"/ventas/api/vehiculo/{placa}",
            name="GET /ventas/api/vehiculo/[placa]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Error inesperado buscando placa {placa}: HTTP {resp.status_code}")

    # ==========================================================================
    # CASO 3: Generación de Factura PDF (FPDF)
    # ==========================================================================
    @task(2)
    def generar_pdf_existente(self):
        if not self.facturas_existentes:
            return
        cod_venta = random.choice(self.facturas_existentes)
        with self.client.get(
            f"/ventas/factura/{cod_venta}",
            name="GET /ventas/factura/[cod_venta] (PDF)",
            catch_response=True,
        ) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and "application/pdf" in content_type:
                resp.success()
            else:
                resp.failure(f"Error generando PDF #{cod_venta}: HTTP {resp.status_code}")

    # ==========================================================================
    # CASO 4: Registro rápido de cliente (SOLO LETRAS en nombre y apellido)
    # ==========================================================================
    @task(1)
    def registrar_cliente_rapido(self):
        sufijo = random.randint(100000, 999999)
        letras = "".join(random.choices(string.ascii_lowercase, k=6))
        cedula = f"30{sufijo}"
        payload = {
            "cedula": cedula,
            "nombre": "Cliente",
            "apellido": f"Prueba{letras}",  # Solo letras, sin números
            "telefono": f"04141{sufijo}",
            "direccion": "Av. Bolivar, Valencia, Carabobo",
            "correo": f"cliente_{sufijo}_{letras}@prueba.com",
            "password": "Admin1234*",
        }
        with self.client.post(
            "/ventas/api/cliente/registrar",
            json=payload,
            name="POST /ventas/api/cliente/registrar",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201 and resp.json().get("exito"):
                self.clientes_disponibles.append(cedula)
                resp.success()
            else:
                resp.failure(f"Fallo creando cliente rápido: HTTP {resp.status_code} - {resp.text}")

    # ==========================================================================
    # CASO 5: Flujo Transaccional Completo (Registrar -> PDF -> Editar -> Anular)
    # ==========================================================================
    @task(2)
    def flujo_completo_venta(self):
        if not self.clientes_disponibles:
            self._cargar_catalogos_vista()
            if not self.clientes_disponibles:
                return

        try:
            placa = placas_queue.get(timeout=1)
        except Empty:
            return

        cod_venta_creada = None
        try:
            # 1. Consultar precio real del vehículo
            resp_veh = self.client.get(
                f"/ventas/api/vehiculo/{placa}",
                name="GET /ventas/api/vehiculo/[placa] (flujo)",
            )
            if resp_veh.status_code != 200:
                return

            veh_data = resp_veh.json().get("vehiculo", {})
            precio = float(veh_data.get("precio") or 10000.0)
            cedula_cliente = random.choice(self.clientes_disponibles)

            tipo_venta = random.choice(["contado", "credito"])
            referencia = str(random.randint(10000000, 99999999))

            if tipo_venta == "contado":
                monto_recibido = precio
                deuda_pendiente = 0.0
                tasa_interes = 0.0
                frecuencia_pago = "Contado"
                cantidad_cuotas = 1
                fecha_inicio = None
                fecha_venc = None
            else:
                monto_recibido = round(precio * 0.30, 2)
                tasa_interes = 5.0
                saldo_base = precio - monto_recibido
                deuda_pendiente = round(saldo_base * (1 + tasa_interes / 100.0), 2)
                frecuencia_pago = "Mensual"
                cantidad_cuotas = 3
                hoy = date.today()
                fecha_inicio = (hoy + timedelta(days=30)).strftime("%Y-%m-%d")
                fecha_venc = (hoy + timedelta(days=95)).strftime("%Y-%m-%d")

            payload_venta = {
                "cedula_cliente": cedula_cliente,
                "placa": placa,
                "tipo_venta": tipo_venta,
                "poder": 1,
                "traspaso_papel": 1,
                "precio_vehiculo": precio,
                "monto_recibido": monto_recibido,
                "deuda_pendiente": deuda_pendiente,
                "tasa_interes": tasa_interes,
                "frecuencia_pago": frecuencia_pago,
                "cantidad_cuotas": cantidad_cuotas,
                "fecha_inicio_cuotas": fecha_inicio,
                "fecha_vencimiento": fecha_venc,
                "cod_metodo": self.cod_metodo_binance,
                "cod_moneda": self.cod_moneda_usd,
                "cod_banco": self.cod_banco_provincial,
                "cod_mon_digital": self.cod_mon_digital_usdt,
                "referencia": referencia,
            }

            # 2. Registrar la venta
            with self.client.post(
                "/ventas/registrar_venta",
                json=payload_venta,
                name=f"POST /ventas/registrar_venta ({tipo_venta})",
                catch_response=True,
            ) as resp_venta:
                if resp_venta.status_code != 200:
                    resp_venta.failure(f"HTTP {resp_venta.status_code}: {resp_venta.text}")
                    return

                res_json = resp_venta.json()
                if not res_json.get("exito"):
                    resp_venta.failure(f"Venta rechazada: {res_json.get('mensaje')}")
                    return

                cod_venta_creada = res_json.get("cod_venta")
                resp_venta.success()

            # 3. Generar PDF de la venta recién creada
            if cod_venta_creada:
                with self.client.get(
                    f"/ventas/factura/{cod_venta_creada}",
                    name="GET /ventas/factura/[cod_venta] (PDF)",
                    catch_response=True,
                ) as resp_pdf:
                    if resp_pdf.status_code == 200 and "application/pdf" in resp_pdf.headers.get("Content-Type", ""):
                        resp_pdf.success()
                    else:
                        resp_pdf.failure(f"Error PDF recién creado: HTTP {resp_pdf.status_code}")

            # 4. Si fue a crédito, probar edición (POST Formulario HTML)
            if cod_venta_creada and tipo_venta == "credito":
                nueva_deuda_total = round(precio * 1.08, 2)
                form_editar = {
                        "cod_venta": str(cod_venta_creada),
                        "cedula_cliente": str(cedula_cliente),   # <-- AGREGA ESTA LÍNEA
                        "placa": placa,                          # <-- Y ESTA POR PRECAUCIÓN
                        "deuda_total": str(nueva_deuda_total),
                        "frecuencia_pago": "Mensual",
                        "cantidad_cuotas": "4",
                        "fecha_inicio_cuotas": fecha_inicio,
                        "fecha_vencimiento": (date.today() + timedelta(days=150)).strftime("%Y-%m-%d"),
                    }
                with self.client.post(
                    "/ventas/editar",
                    data=form_editar,
                    name="POST /ventas/editar (form)",
                    catch_response=True,
                ) as resp_edit:
                    if resp_edit.status_code != 200:
                        resp_edit.failure(f"HTTP {resp_edit.status_code} al editar venta")
                    elif "Error al actualizar la venta" in resp_edit.text:
                        match_err = re.search(r"Error al actualizar la venta:\s*([^<\n]+)", resp_edit.text)
                        detalle = match_err.group(1).strip() if match_err else "Error desconocido en flash"
                        resp_edit.failure(f"Validación rechazada: {detalle}")
                    else:
                        resp_edit.success()

        finally:
            # 5. Anular la venta de prueba para liberar el vehículo
            if cod_venta_creada:
                with self.client.post(
                    f"/ventas/eliminar/{cod_venta_creada}",
                    name="POST /ventas/eliminar/[id] (liberar)",
                    catch_response=True,
                ) as resp_del:
                    if resp_del.status_code == 200 and "Error al anular" not in resp_del.text:
                        resp_del.success()
                    else:
                        resp_del.failure(f"No se pudo anular venta #{cod_venta_creada}")
            placas_queue.put(placa)