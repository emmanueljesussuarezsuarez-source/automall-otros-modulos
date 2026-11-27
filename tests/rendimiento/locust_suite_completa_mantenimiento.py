import os
import re
import sys
import threading
import uuid
from datetime import date
from locust import HttpUser, LoadTestShape, between, task
from locust.exception import StopUser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import Config  # noqa: E402

if (
    Config.DB_NEGOCIO.get("database") != "automall_test"
    or Config.DB_SEGURIDAD.get("database") != "seguridad_test"
):
    raise RuntimeError(
        "BLOQUEADO: config.py debe apuntar a 'automall_test' y 'seguridad_test' "
        f"(actual: {Config.DB_NEGOCIO.get('database')} / {Config.DB_SEGURIDAD.get('database')})."
    )

CREDENCIALES_LOGIN = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}

DURACION_NIVEL = 45  # segundos por nivel (1u, 20u, 50u) -> ~17-18 min total

_SETUP_LOCK = threading.Lock()
_CACHE_SETUP = {
    "inicializado": False,
    "placas": ["GH567IJ"],
    "cod_taller": None,
    "quien_autoriza": "18998754",
    "contador_usuarios": 0,
}


def _construir_etapas():
    etapas = []
    t = 0

    def agregar(tipo, etiqueta, duracion, usuarios=0, tasa=1, u_ini=0, u_fin=0):
        nonlocal t
        etapas.append({
            "inicio": t,
            "fin": t + duracion,
            "tipo": tipo,
            "etiqueta": etiqueta,
            "usuarios": usuarios,
            "tasa": tasa,
            "u_ini": u_ini,
            "u_fin": u_fin,
        })
        t += duracion

    casos_principales = [
        ("cp01", "CP01 Formulario"),
        ("cp02", "CP02 Listado"),
        ("cp03", "CP03 Crear"),
        ("cp04", "CP04 Editar"),
        ("cp05", "CP05 Inactivar"),
    ]

    for tipo, prefijo in casos_principales:
        for usuarios, tasa in [(1, 1), (20, 5), (50, 10)]:
            agregar(tipo, f"{prefijo} - {usuarios}u", DURACION_NIVEL, usuarios=usuarios, tasa=tasa)
        agregar("pausa", "Transicion", 5, usuarios=0, tasa=50)

    # CP-MAN-PERF-07: Pico repentino de 10 a 50 usuarios en 10s (60s total)
    agregar("mixto", "CP07 Pico", 15, usuarios=10, tasa=5)
    agregar("mixto", "CP07 Pico", 45, usuarios=50, tasa=4)
    agregar("pausa", "Transicion CP08", 5, usuarios=0, tasa=50)

    # CP-MAN-PERF-08: Estres progresivo de 5 a 100 usuarios en 2 minutos (150s total)
    agregar("mixto", "CP08 Estres", 10, usuarios=5, tasa=5)
    agregar("mixto_ramp", "CP08 Estres", 120, tasa=5, u_ini=5, u_fin=100)
    agregar("mixto", "CP08 Estres", 20, usuarios=100, tasa=5)
    agregar("pausa", "Transicion CP06", 5, usuarios=0, tasa=50)

    # CP-MAN-PERF-06 al final para no saturar /login de CP07 y CP08 con PDFs pesados
    for usuarios, tasa in [(1, 1), (20, 5), (50, 10)]:
        agregar("cp06", f"CP06 Reporte PDF - {usuarios}u", DURACION_NIVEL, usuarios=usuarios, tasa=tasa)

    return etapas


ETAPAS = _construir_etapas()
ESTADO_SUITE = {"etapa": ETAPAS[0]}


class UsuarioSuiteCompletaMantenimiento(HttpUser):
    """Ejecuta todos los escenarios de Mantenimiento Operacional según la etapa activa."""

    wait_time = between(1, 3)

    def on_start(self):
        self.cod_mant_edit = None
        self.paso_inactivar = 0
        self.cod_mant_inactivar = None
        self.paso_mixto = 0
        self.cod_mant_mixto = None

        with self.client.post(
            "/login",
            json=CREDENCIALES_LOGIN,
            name="/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP en login: {resp.status_code}")
                raise StopUser()
            try:
                data = resp.json()
            except ValueError:
                resp.failure("La respuesta de login no es JSON válido")
                raise StopUser()
            if data.get("status") != "success":
                resp.failure(f"Login rechazado: {data.get('message')}")
                raise StopUser()
            resp.success()

        self._asegurar_datos_base()

    def _extraer_valores_select(self, html, select_id):
        bloque = re.search(
            rf'<select[^>]*id="{re.escape(select_id)}"[^>]*>(.*?)</select>',
            html,
            re.DOTALL,
        )
        if not bloque:
            return []
        valores = re.findall(r'<option[^>]*value="([^"]*)"', bloque.group(1))
        return [v.strip() for v in valores if v.strip()]

    def _asegurar_datos_base(self):
        with _SETUP_LOCK:
            if not _CACHE_SETUP["inicializado"]:
                resp = self.client.get("/mantenimiento-operacional", name="/mantenimiento-operacional [setup]")
                if resp.status_code == 200:
                    placas_validas = [
                        p for p in self._extraer_valores_select(resp.text, "placa")
                        if 5 <= len(p) <= 7
                    ]
                    if placas_validas:
                        _CACHE_SETUP["placas"] = placas_validas
                    talleres = [t for t in self._extraer_valores_select(resp.text, "cod_taller") if t.isdigit()]
                    if not talleres:
                        self.client.post(
                            "/taller/nuevo",
                            data={
                                "nombre_taller": f"Taller Base Mant {uuid.uuid4().hex[:6]}",
                                "direccion": "Av Principal Mantenimiento 100",
                                "estado": "1",
                            },
                            name="/taller/nuevo [setup]",
                            allow_redirects=True,
                        )
                        resp2 = self.client.get("/mantenimiento-operacional", name="/mantenimiento-operacional [setup]")
                        if resp2.status_code == 200:
                            talleres = [t for t in self._extraer_valores_select(resp2.text, "cod_taller") if t.isdigit()]
                    if talleres:
                        _CACHE_SETUP["cod_taller"] = talleres[0]

                resp_crear = self.client.get("/mantenimiento-operacional/crear", name="/mantenimiento-operacional/crear [setup]")
                if resp_crear.status_code == 200:
                    autorizadores = [a for a in self._extraer_valores_select(resp_crear.text, "quien_autoriza") if a.isdigit()]
                    if autorizadores:
                        _CACHE_SETUP["quien_autoriza"] = autorizadores[0]

                _CACHE_SETUP["inicializado"] = True

            idx = _CACHE_SETUP["contador_usuarios"]
            _CACHE_SETUP["contador_usuarios"] += 1
            placas = _CACHE_SETUP["placas"]
            self.placa = placas[idx % len(placas)]
            self.cod_taller = _CACHE_SETUP["cod_taller"] or "1"
            self.quien_autoriza = _CACHE_SETUP["quien_autoriza"] or "18998754"

    def _hoy(self):
        return date.today().strftime("%Y-%m-%d")

    def _nueva_descripcion(self, prefijo="Mantenimiento Perf"):
        return f"{prefijo} {uuid.uuid4().hex[:10]}"

    def _extraer_error_flash(self, html):
        coincidencia = re.search(
            r'data-category="(?:danger|warning)"\s+data-message="([^"]+)"',
            html,
        )
        return coincidencia.group(1) if coincidencia else None

    def _extraer_cod_mantenimiento(self, html, descripcion):
        patron = rf'#(\d+)\s*</span>\s*</td>\s*<td[^>]*>\s*{re.escape(descripcion)}\s*</td>'
        coincidencia = re.search(patron, html)
        return coincidencia.group(1) if coincidencia else None

    def _verificar_vista(self, ruta, request_name, texto_esperado, descripcion_error):
        with self.client.get(ruta, name=request_name, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code}")
            elif texto_esperado not in resp.text:
                resp.failure(descripcion_error)
            else:
                resp.success()

    def _crear_mantenimiento(self, descripcion, request_name):
        with self.client.post(
            "/mantenimiento-operacional/crear",
            data={
                "placa": self.placa,
                "cod_taller": self.cod_taller,
                "quien_autoriza": self.quien_autoriza,
                "tipo": "Preventivo",
                "fecha_solicitud": self._hoy(),
                "fecha_completada": "",
                "descripcion_general": descripcion,
                "costo_base": "150.00",
                "costo_final": "",
                "descripcion_detalle_0": "Filtro de aceite prueba",
                "cantidad_0": "2",
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al crear mantenimiento")
                return False, None
            if "Mantenimiento registrado correctamente." not in resp.text:
                msg = self._extraer_error_flash(resp.text) or "No apareció el mensaje de éxito al crear mantenimiento"
                resp.failure(msg)
                return False, None
            resp.success()
            cod_mant = self._extraer_cod_mantenimiento(resp.text, descripcion)
            return True, cod_mant

    def _editar_mantenimiento(self, cod_mant, nueva_desc, request_name):
        with self.client.post(
            f"/mantenimiento-operacional/editar/{cod_mant}",
            data={
                "placa": self.placa,
                "cod_taller": self.cod_taller,
                "quien_autoriza": self.quien_autoriza,
                "tipo": "Correctivo",
                "fecha_solicitud": self._hoy(),
                "fecha_completada": "",
                "descripcion_general": nueva_desc,
                "costo_base": "220.00",
                "costo_final": "250.00",
                "descripcion_detalle_0": "Pastillas ceramicas prueba",
                "cantidad_0": "4",
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al editar mantenimiento")
                return False
            if "Mantenimiento actualizado correctamente." not in resp.text:
                msg = self._extraer_error_flash(resp.text) or "No apareció el mensaje de éxito al editar mantenimiento"
                resp.failure(msg)
                return False
            resp.success()
            return True

    def _inactivar_mantenimiento(self, cod_mant, request_name):
        with self.client.post(
            f"/mantenimiento-operacional/inactivar/{cod_mant}",
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al inactivar mantenimiento")
                return False
            if "Mantenimiento inactivado correctamente." not in resp.text:
                msg = self._extraer_error_flash(resp.text) or "No apareció el mensaje de éxito al inactivar mantenimiento"
                resp.failure(msg)
                return False
            resp.success()
            return True

    def _finalizar_mantenimiento(self, cod_mant, request_name):
        with self.client.post(
            f"/mantenimiento-operacional/finalizar/{cod_mant}/{self.placa}",
            data={"costo_final": "280.00"},
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al finalizar mantenimiento")
                return False
            if "Mantenimiento finalizado correctamente." not in resp.text:
                msg = self._extraer_error_flash(resp.text) or "No apareció el mensaje de finalización"
                resp.failure(msg)
                return False
            resp.success()
            return True

    def _generar_reporte_pdf(self, request_name):
        with self.client.get(
            "/mantenimiento-operacional/reporte/generar?estado=Activo&accion=ver",
            name=request_name,
            allow_redirects=False,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al generar reporte PDF")
            elif "application/pdf" not in resp.headers.get("Content-Type", "") or not resp.content.startswith(b"%PDF"):
                resp.failure("La respuesta no devolvió un PDF válido")
            else:
                resp.success()

    def _ejecutar_mixto(self, etiqueta):
        if self.paso_mixto == 0:
            self._verificar_vista(
                "/mantenimiento-operacional",
                f"/mantenimiento-operacional [{etiqueta}]",
                'id="tablaMantenimientoOperacional"',
                "No se encontró #tablaMantenimientoOperacional",
            )
            self.paso_mixto = 1
        elif self.paso_mixto == 1:
            desc = self._nueva_descripcion("Mant Flujo Mixto")
            _, self.cod_mant_mixto = self._crear_mantenimiento(
                desc,
                request_name=f"/mantenimiento-operacional/crear [{etiqueta}]",
            )
            self.paso_mixto = 2
        elif self.paso_mixto == 2:
            if self.cod_mant_mixto:
                self._finalizar_mantenimiento(
                    self.cod_mant_mixto,
                    request_name=f"/mantenimiento-operacional/finalizar/[id] [{etiqueta}]",
                )
            self.paso_mixto = 3
        else:
            if self.cod_mant_mixto:
                self._verificar_vista(
                    f"/mantenimiento-operacional/ver-recibo/{self.cod_mant_mixto}",
                    f"/mantenimiento-operacional/ver-recibo/[id] [{etiqueta}]",
                    "RECIBO DE MANTENIMIENTO",
                    "No se cargó el recibo de mantenimiento",
                )
            self.cod_mant_mixto = None
            self.paso_mixto = 0

    @task
    def ejecutar_etapa_actual(self):
        etapa = ESTADO_SUITE["etapa"]
        tipo = etapa["tipo"]
        etiqueta = etapa["etiqueta"]

        if tipo == "pausa":
            return
        if tipo == "cp01":
            self._verificar_vista(
                "/mantenimiento-operacional/crear",
                f"/mantenimiento-operacional/crear [{etiqueta}]",
                'id="descripcion_general"',
                "No se encontró el formulario de mantenimiento",
            )
        elif tipo == "cp02":
            self._verificar_vista(
                "/mantenimiento-operacional",
                f"/mantenimiento-operacional [{etiqueta}]",
                'id="tablaMantenimientoOperacional"',
                "No se encontró #tablaMantenimientoOperacional",
            )
        elif tipo == "cp03":
            self._crear_mantenimiento(
                self._nueva_descripcion("Mantenimiento Perf"),
                request_name=f"/mantenimiento-operacional/crear [{etiqueta}]",
            )
        elif tipo == "cp04":
            if not self.cod_mant_edit:
                _, self.cod_mant_edit = self._crear_mantenimiento(
                    self._nueva_descripcion("Mant Base Edit"),
                    request_name="/mantenimiento-operacional/crear [setup editar]",
                )
                return
            self._editar_mantenimiento(
                self.cod_mant_edit,
                self._nueva_descripcion("Mant Editado Perf"),
                request_name=f"/mantenimiento-operacional/editar/[id] [{etiqueta}]",
            )
        elif tipo == "cp05":
            if self.paso_inactivar == 0 or not self.cod_mant_inactivar:
                ok, cod_mant = self._crear_mantenimiento(
                    self._nueva_descripcion("Mant Temp Inact"),
                    request_name="/mantenimiento-operacional/crear [setup inactivar]",
                )
                if ok and cod_mant:
                    self.cod_mant_inactivar = cod_mant
                    self.paso_inactivar = 1
                return
            self._inactivar_mantenimiento(
                self.cod_mant_inactivar,
                request_name=f"/mantenimiento-operacional/inactivar/[id] [{etiqueta}]",
            )
            self.cod_mant_inactivar = None
            self.paso_inactivar = 0
        elif tipo == "cp06":
            self._generar_reporte_pdf(f"/mantenimiento-operacional/reporte/generar [{etiqueta}]")
        elif tipo in ("mixto", "mixto_ramp"):
            self._ejecutar_mixto(etiqueta)


class FormaSuiteCompletaMantenimiento(LoadTestShape):
    """Controla automáticamente la línea de tiempo completa de Mantenimiento Operacional (~18 min)."""

    def tick(self):
        run_time = self.get_run_time()
        for etapa in ETAPAS:
            if etapa["inicio"] <= run_time < etapa["fin"]:
                ESTADO_SUITE["etapa"] = etapa
                if etapa["tipo"] == "mixto_ramp":
                    duracion = etapa["fin"] - etapa["inicio"]
                    progreso = (run_time - etapa["inicio"]) / duracion
                    usuarios = etapa["u_ini"] + round((etapa["u_fin"] - etapa["u_ini"]) * progreso)
                    return (usuarios, etapa["tasa"])
                return (etapa["usuarios"], etapa["tasa"])
        return None