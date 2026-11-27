import os
import sys
import uuid
from locust import LoadTestShape, task

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from locustfile_taller import UsuarioBaseTaller  # noqa: E402

DURACION_NIVEL = 45  # segundos por cada nivel (1u, 20u, 50u) -> ~17 min total


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
        ("cp05", "CP05 Eliminar", True),
        ("mixto", "CP06 Mixto", False),
    ]

    for tipo, prefijo, pausa_despues in casos:
        for usuarios, tasa in [(1, 1), (20, 5), (50, 10)]:
            agregar(tipo, f"{prefijo} - {usuarios}u", DURACION_NIVEL, usuarios=usuarios, tasa=tasa)
        if pausa_despues:
            agregar("pausa", "Transicion", 2, usuarios=0, tasa=50)

    # CP-TAL-PERF-07: Pico repentino de 10 a 50 usuarios en 10s (60s total)
    agregar("pausa", "Transicion CP07", 2, usuarios=0, tasa=50)
    agregar("mixto", "CP07 Pico", 15, usuarios=10, tasa=5)
    agregar("mixto", "CP07 Pico", 45, usuarios=50, tasa=4)

    # CP-TAL-PERF-08: Estres progresivo de 5 a 100 usuarios en 2 minutos (150s total)
    agregar("pausa", "Transicion CP08", 2, usuarios=0, tasa=50)
    agregar("mixto", "CP08 Estres", 10, usuarios=5, tasa=5)
    agregar("mixto_ramp", "CP08 Estres", 120, tasa=5, u_ini=5, u_fin=100)
    agregar("mixto", "CP08 Estres", 20, usuarios=100, tasa=5)

    return etapas


ETAPAS = _construir_etapas()
ESTADO_SUITE = {"etapa": ETAPAS[0]}


class UsuarioSuiteCompletaTaller(UsuarioBaseTaller):
    """Ejecuta todos los escenarios de Taller según la etapa activa de LoadTestShape."""

    def on_start(self):
        super().on_start()
        self.cod_taller_edit = None
        self.paso_mixto = 0
        self.cod_taller_mixto = None

    def _editar_con_nombre(self, cod_taller, nuevo_nombre, nueva_direccion, request_name):
        with self.client.post(
            f"/taller/editar/{cod_taller}",
            data={
                "nombre_taller": nuevo_nombre,
                "direccion": nueva_direccion,
                "estado": "1",
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al editar taller")
                return False
            if "Taller actualizado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al editar taller")
                return False
            resp.success()
            return True

    def _eliminar_con_nombre(self, cod_taller, request_name):
        with self.client.post(
            f"/taller/eliminar/{cod_taller}",
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al eliminar taller")
                return False
            if "Taller desactivado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al eliminar taller")
                return False
            resp.success()
            return True

    def _verificar_vista(self, etiqueta, texto_esperado, descripcion_error):
        with self.client.get(
            "/taller",
            name=f"/taller [{etiqueta}]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code}")
            elif texto_esperado not in resp.text:
                resp.failure(descripcion_error)
            else:
                resp.success()

    def _ejecutar_mixto(self, etiqueta):
        if self.paso_mixto == 0:
            self._verificar_vista(etiqueta, 'id="tablaTalleres"', "No se encontró #tablaTalleres")
            self.paso_mixto = 1
        elif self.paso_mixto == 1:
            nombre = self._nuevo_nombre("Taller Perf Mix")
            direccion = f"Calle Flujo {uuid.uuid4().hex[:6]}"
            _, self.cod_taller_mixto = self._crear_taller(
                nombre,
                direccion,
                request_name=f"/taller/nuevo [{etiqueta}]",
            )
            self.paso_mixto = 2
        else:
            if self.cod_taller_mixto:
                self._editar_con_nombre(
                    self.cod_taller_mixto,
                    self._nuevo_nombre("Taller Perf MixMod"),
                    f"Calle Edit {uuid.uuid4().hex[:6]}",
                    request_name=f"/taller/editar/[id] [{etiqueta}]",
                )
            self.paso_mixto = 0

    @task
    def ejecutar_etapa_actual(self):
        etapa = ESTADO_SUITE["etapa"]
        tipo = etapa["tipo"]
        etiqueta = etapa["etiqueta"]

        if tipo == "pausa":
            return
        if tipo == "cp01":
            self._verificar_vista(etiqueta, 'id="modalRegistrarTaller"', "No se encontró #modalRegistrarTaller")
        elif tipo == "cp02":
            self._verificar_vista(etiqueta, 'id="tablaTalleres"', "No se encontró #tablaTalleres")
        elif tipo == "cp03":
            self._crear_taller(
                self._nuevo_nombre("Taller Perf"),
                f"Av Carga {uuid.uuid4().hex[:6]}",
                request_name=f"/taller/nuevo [{etiqueta}]",
            )
        elif tipo == "cp04":
            if not self.cod_taller_edit:
                _, self.cod_taller_edit = self._crear_taller(
                    self._nuevo_nombre("Taller Perf Edit"),
                    "Av Inicial Edicion 100",
                    request_name="/taller/nuevo [setup editar]",
                )
                return
            self._editar_con_nombre(
                self.cod_taller_edit,
                self._nuevo_nombre("Taller Perf Mod"),
                f"Av Editada {uuid.uuid4().hex[:6]}",
                request_name=f"/taller/editar/[id] [{etiqueta}]",
            )
        elif tipo == "cp05":
            ok, cod_taller = self._crear_taller(
                self._nuevo_nombre("Taller Perf Del"),
                "Av Temporal Eliminar 200",
                request_name="/taller/nuevo [setup eliminar]",
            )
            if ok and cod_taller:
                self._eliminar_con_nombre(cod_taller, request_name=f"/taller/eliminar/[id] [{etiqueta}]")
        elif tipo in ("mixto", "mixto_ramp"):
            self._ejecutar_mixto(etiqueta)


class FormaSuiteCompletaTaller(LoadTestShape):
    """Controla automáticamente la línea de tiempo completa de los 8 casos (~17 min)."""

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