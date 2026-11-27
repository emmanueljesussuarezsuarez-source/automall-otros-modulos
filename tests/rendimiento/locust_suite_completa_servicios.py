import os
import random
import re
import string
import sys
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

DURACION_NIVEL = 45  # segundos por nivel (1u, 20u, 50u) -> ~17 min total


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

    casos = [
        ("cp01", "CP01 Formulario", True),
        ("cp02", "CP02 Listado", True),
        ("cp03", "CP03 Crear", True),
        ("cp04", "CP04 Editar", True),
        ("cp05", "CP05 Inactivar", True),
        ("cp06", "CP06 Reporte PDF", True),
    ]

    for tipo, prefijo, pausa_despues in casos:
        for usuarios, tasa in [(1, 1), (20, 5), (50, 10)]:
            agregar(tipo, f"{prefijo} - {usuarios}u", DURACION_NIVEL, usuarios=usuarios, tasa=tasa)
        if pausa_despues:
            agregar("pausa", "Transicion", 2, usuarios=0, tasa=50)

    # CP-SER-PERF-07: Pico repentino de 10 a 50 usuarios en 10s (60s total)
    agregar("mixto", "CP07 Pico", 15, usuarios=10, tasa=5)
    agregar("mixto", "CP07 Pico", 45, usuarios=50, tasa=4)

    # CP-SER-PERF-08: Estres progresivo de 5 a 100 usuarios en 2 minutos (150s total)
    agregar("pausa", "Transicion CP08", 2, usuarios=0, tasa=50)
    agregar("mixto", "CP08 Estres", 10, usuarios=5, tasa=5)
    agregar("mixto_ramp", "CP08 Estres", 120, tasa=5, u_ini=5, u_fin=100)
    agregar("mixto", "CP08 Estres", 20, usuarios=100, tasa=5)

    return etapas


ETAPAS = _construir_etapas()
ESTADO_SUITE = {"etapa": ETAPAS[0]}


class UsuarioSuiteCompletaServicios(HttpUser):
    """Ejecuta todos los escenarios de Servicios según la etapa activa de LoadTestShape."""

    wait_time = between(1, 3)

    def on_start(self):
        self.cod_servicio_edit = None
        self.paso_mixto = 0
        self.cod_servicio_mixto = None
        self.placa = "GH567IJ"

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

        self.placa = self._detectar_placa_real()

    def _detectar_placa_real(self):
        resp = self.client.get("/servicios", name="/servicios [setup placa]")
        if resp.status_code == 200:
            bloque = re.search(r'id="placa_reporte".*?</select>', resp.text, re.DOTALL)
            if bloque:
                coincidencia = re.search(r'<option value="([A-Za-z0-9]{5,7})">', bloque.group(0))
                if coincidencia:
                    return coincidencia.group(1)
        return "GH567IJ"

    def _nuevo_nombre_letras(self, prefijo="Lavado Perf"):
        sufijo = "".join(random.choices(string.ascii_lowercase, k=10))
        return f"{prefijo} {sufijo}"

    def _hoy(self):
        return date.today().strftime("%Y-%m-%d")

    def _extraer_cod_servicio(self, html, nombre_servicio):
        patron = rf'#(\d+)\s*</span>\s*</td>\s*<td[^>]*>\s*{re.escape(nombre_servicio)}\s*</td>'
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

    def _crear_servicio(self, nombre_servicio, request_name):
        with self.client.post(
            "/servicios/nuevo",
            data={
                "nombre_servicio": nombre_servicio,
                "costo_base": "45.00",
                "costo_final": "",
                "descripcion_especifica": "Limpieza y revision completa de servicio prueba",
                "fecha_realizacion": self._hoy(),
                "placa": self.placa,
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al crear servicio")
                return False, None
            if "Servicio registrado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al crear servicio")
                return False, None
            resp.success()
            cod_servicio = self._extraer_cod_servicio(resp.text, nombre_servicio)
            return True, cod_servicio

    def _editar_servicio(self, cod_servicio, nuevo_nombre, request_name):
        with self.client.post(
            f"/servicios/editar/{cod_servicio}",
            data={
                "nombre_servicio": nuevo_nombre,
                "costo_base": "60.00",
                "costo_final": "75.00",
                "descripcion_especifica": "Servicio actualizado en prueba de rendimiento",
                "fecha_realizacion": self._hoy(),
                "placa": self.placa,
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al editar servicio")
                return False
            if "Servicio actualizado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al editar servicio")
                return False
            resp.success()
            return True

    def _inactivar_servicio(self, cod_servicio, request_name):
        with self.client.post(
            f"/servicios/inactivar/{cod_servicio}",
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al inactivar servicio")
                return False
            if "Servicio inactivado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al inactivar servicio")
                return False
            resp.success()
            return True

    def _finalizar_servicio(self, cod_servicio, request_name):
        with self.client.post(
            f"/servicios/finalizar/{cod_servicio}/{self.placa}",
            data={"costo_final": "80.00"},
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al finalizar servicio")
                return False
            if "Servicio finalizado y vehículo reactivado." not in resp.text:
                resp.failure("No apareció el mensaje de finalización")
                return False
            resp.success()
            return True

    def _generar_reporte_pdf(self, request_name):
        with self.client.get(
            "/servicios/reporte/generar?estado=Activo&accion=ver",
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
                "/servicios",
                f"/servicios [{etiqueta}]",
                'id="tablaServicios"',
                "No se encontró #tablaServicios",
            )
            self.paso_mixto = 1
        elif self.paso_mixto == 1:
            nombre = self._nuevo_nombre_letras("Pulitura Perf")
            _, self.cod_servicio_mixto = self._crear_servicio(
                nombre,
                request_name=f"/servicios/nuevo [{etiqueta}]",
            )
            self.paso_mixto = 2
        elif self.paso_mixto == 2:
            if self.cod_servicio_mixto:
                self._finalizar_servicio(
                    self.cod_servicio_mixto,
                    request_name=f"/servicios/finalizar/[id] [{etiqueta}]",
                )
            self.paso_mixto = 3
        else:
            if self.cod_servicio_mixto:
                self._verificar_vista(
                    f"/servicios/recibo/{self.cod_servicio_mixto}",
                    f"/servicios/recibo/[id] [{etiqueta}]",
                    "RECIBO DE SERVICIO",
                    "No se cargó el recibo del servicio",
                )
            self.cod_servicio_mixto = None
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
                "/servicios/nuevo",
                f"/servicios/nuevo [{etiqueta}]",
                'id="formServicio"',
                "No se encontró #formServicio",
            )
        elif tipo == "cp02":
            self._verificar_vista(
                "/servicios",
                f"/servicios [{etiqueta}]",
                'id="tablaServicios"',
                "No se encontró #tablaServicios",
            )
        elif tipo == "cp03":
            self._crear_servicio(
                self._nuevo_nombre_letras("Lavado Perf"),
                request_name=f"/servicios/nuevo [{etiqueta}]",
            )
        elif tipo == "cp04":
            if not self.cod_servicio_edit:
                _, self.cod_servicio_edit = self._crear_servicio(
                    self._nuevo_nombre_letras("Servicio Edit"),
                    request_name="/servicios/nuevo [setup editar]",
                )
                return
            self._editar_servicio(
                self.cod_servicio_edit,
                self._nuevo_nombre_letras("Servicio Mod"),
                request_name=f"/servicios/editar/[id] [{etiqueta}]",
            )
        elif tipo == "cp05":
            ok, cod_servicio = self._crear_servicio(
                self._nuevo_nombre_letras("Servicio Inact"),
                request_name="/servicios/nuevo [setup inactivar]",
            )
            if ok and cod_servicio:
                self._inactivar_servicio(
                    cod_servicio,
                    request_name=f"/servicios/inactivar/[id] [{etiqueta}]",
                )
        elif tipo == "cp06":
            self._generar_reporte_pdf(f"/servicios/reporte/generar [{etiqueta}]")
        elif tipo in ("mixto", "mixto_ramp"):
            self._ejecutar_mixto(etiqueta)


class FormaSuiteCompletaServicios(LoadTestShape):
    """Controla automáticamente la línea de tiempo completa de Servicios (~17 min)."""

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