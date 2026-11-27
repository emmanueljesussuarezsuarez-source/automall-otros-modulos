import re
import uuid
from locust import HttpUser, SequentialTaskSet, task, between
from locust.exception import StopUser

CREDENCIALES_LOGIN = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}


class UsuarioBaseTaller(HttpUser):
    """Clase base con sesión autenticada y operaciones reutilizables de Taller."""

    abstract = True
    wait_time = between(1, 3)

    def on_start(self):
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

    def _nuevo_nombre(self, prefijo="Taller Perf"):
        return f"{prefijo} {uuid.uuid4().hex[:10]}"

    def _extraer_cod_taller(self, html, nombre_taller):
        patron = rf'data-id="(\d+)"\s+data-nombre="{re.escape(nombre_taller)}"'
        coincidencia = re.search(patron, html)
        return coincidencia.group(1) if coincidencia else None

    def _crear_taller(self, nombre_taller, direccion, request_name="/taller/nuevo"):
        with self.client.post(
            "/taller/nuevo",
            data={
                "nombre_taller": nombre_taller,
                "direccion": direccion,
                "estado": "1",
            },
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code} al crear taller")
                return False, None
            if "Taller registrado correctamente." not in resp.text:
                resp.failure("No apareció el mensaje de éxito al crear taller")
                return False, None
            resp.success()
            cod_taller = self._extraer_cod_taller(resp.text, nombre_taller)
            return True, cod_taller

    def _editar_taller(self, cod_taller, nuevo_nombre, nueva_direccion):
        with self.client.post(
            f"/taller/editar/{cod_taller}",
            data={
                "nombre_taller": nuevo_nombre,
                "direccion": nueva_direccion,
                "estado": "1",
            },
            name="/taller/editar/[id]",
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

    def _eliminar_taller(self, cod_taller):
        with self.client.post(
            f"/taller/eliminar/{cod_taller}",
            name="/taller/eliminar/[id]",
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


class CP01CargarFormularioTaller(UsuarioBaseTaller):
    """CP-TAL-PERF-01: Cargar vista con el formulario modal de crear taller (GET /taller)."""

    @task
    def cargar_formulario_registro(self):
        with self.client.get(
            "/taller",
            name="/taller [CP-01 Formulario]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code}")
            elif 'id="modalRegistrarTaller"' not in resp.text:
                resp.failure("No se encontró el modal #modalRegistrarTaller en la vista")
            else:
                resp.success()


class CP02ListarTalleres(UsuarioBaseTaller):
    """CP-TAL-PERF-02: Listar talleres activos (GET /taller)."""

    @task
    def listar_talleres(self):
        with self.client.get(
            "/taller",
            name="/taller [CP-02 Listado]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code}")
            elif 'id="tablaTalleres"' not in resp.text:
                resp.failure("No se encontró la tabla #tablaTalleres en la vista")
            else:
                resp.success()


class CP03CrearTaller(UsuarioBaseTaller):
    """CP-TAL-PERF-03: Crear un taller nuevo (POST /taller/nuevo)."""

    @task
    def crear_taller(self):
        nombre = self._nuevo_nombre("Taller Perf")
        direccion = f"Av Prueba Carga {uuid.uuid4().hex[:6]}"
        self._crear_taller(nombre, direccion)


class CP04EditarTaller(UsuarioBaseTaller):
    """CP-TAL-PERF-04: Editar un taller existente (POST /taller/editar/<id>)."""

    def on_start(self):
        super().on_start()
        nombre_base = self._nuevo_nombre("Taller Perf Edit")
        _, self.cod_taller = self._crear_taller(
            nombre_base,
            "Av Inicial Edicion 100",
            request_name="/taller/nuevo [setup editar]",
        )

    @task
    def editar_taller(self):
        if not getattr(self, "cod_taller", None):
            nombre_base = self._nuevo_nombre("Taller Perf Edit")
            _, self.cod_taller = self._crear_taller(
                nombre_base,
                "Av Inicial Edicion 100",
                request_name="/taller/nuevo [setup editar]",
            )
            return

        nuevo_nombre = self._nuevo_nombre("Taller Perf Mod")
        nueva_dir = f"Av Editada {uuid.uuid4().hex[:6]}"
        self._editar_taller(self.cod_taller, nuevo_nombre, nueva_dir)


class CP05EliminarTaller(UsuarioBaseTaller):
    """CP-TAL-PERF-05: Eliminar/desactivar un taller (POST /taller/eliminar/<id>)."""

    @task
    def eliminar_taller(self):
        nombre_temp = self._nuevo_nombre("Taller Perf Del")
        ok, cod_taller = self._crear_taller(
            nombre_temp,
            "Av Temporal Eliminar 200",
            request_name="/taller/nuevo [setup eliminar]",
        )
        if ok and cod_taller:
            self._eliminar_taller(cod_taller)


class FlujoMixtoTallerTasks(SequentialTaskSet):
    """Secuencia realista: listar talleres -> crear taller -> editar taller."""

    def on_start(self):
        self.cod_taller_actual = None

    @task
    def paso_1_listar_talleres(self):
        with self.client.get(
            "/taller",
            name="/taller [Flujo Mixto]",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Error HTTP {resp.status_code}")
            elif 'id="tablaTalleres"' not in resp.text:
                resp.failure("No se encontró la tabla #tablaTalleres")
            else:
                resp.success()

    @task
    def paso_2_crear_taller(self):
        nombre = self.user._nuevo_nombre("Taller Perf Mix")
        direccion = f"Calle Flujo Mixto {uuid.uuid4().hex[:6]}"
        _, self.cod_taller_actual = self.user._crear_taller(
            nombre,
            direccion,
            request_name="/taller/nuevo [Flujo Mixto]",
        )

    @task
    def paso_3_editar_taller(self):
        if self.cod_taller_actual:
            nuevo_nombre = self.user._nuevo_nombre("Taller Perf MixMod")
            nueva_dir = f"Calle Editada {uuid.uuid4().hex[:6]}"
            self.user._editar_taller(
                self.cod_taller_actual,
                nuevo_nombre,
                nueva_dir,
            )


class CP06FlujoMixtoTaller(UsuarioBaseTaller):
    """CP-TAL-PERF-06 / 07 / 08: Flujo mixto de usuario (listar, crear y editar)."""

    tasks = [FlujoMixtoTallerTasks]