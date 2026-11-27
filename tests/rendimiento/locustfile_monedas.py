import random
import re
import string
from locust import HttpUser, task, between

CREDENCIALES = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}


def extraer_id_por_nombre(html, nombre_buscado, prefijo_ruta):
    filas = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE | re.DOTALL)
    for fila in filas:
        if nombre_buscado in fila:
            for patron in (
                rf"{re.escape(prefijo_ruta)}/(?:editar|eliminar)/(\d+)",
                r'data-(?:id|cod|codigo)[a-z_-]*=["\'](\d+)["\']',
                r'onclick=["\'][^"\']*\(\s*(\d+)',
                r"<td[^>]*>\s*#?(\d+)\s*</td>",
            ):
                m = re.search(patron, fila, re.IGNORECASE)
                if m:
                    return int(m.group(1))

    pos = html.find(nombre_buscado)
    if pos != -1:
        ventana = html[max(0, pos - 400): pos + 600]
        for patron in (
            rf"{re.escape(prefijo_ruta)}/(?:editar|eliminar)/(\d+)",
            r'data-(?:id|cod|codigo)[a-z_-]*=["\'](\d+)["\']',
            r'onclick=["\'][^"\']*\(\s*(\d+)',
        ):
            m = re.search(patron, ventana, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return None


class UsuarioMonedas(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        with self.client.post("/login", json=CREDENCIALES, name="POST /login", catch_response=True) as resp:
            if resp.status_code == 200 and resp.json().get("status") == "success":
                resp.success()
            else:
                resp.failure(f"Login fallido: {resp.text}")

    @task(4)
    def listar_monedas(self):
        with self.client.get("/monedas/gestion", name="GET /monedas/gestion", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} listando monedas")

    @task(1)
    def validacion_moneda_invalida(self):
        """Caso negativo controlado: estado inválido debe devolver 400."""
        with self.client.post(
            "/monedas/crear",
            data={"nombre_moneda": "MonedaBad", "simbolo": "MB", "estado": "Invalido"},
            name="POST /monedas/crear (validacion_400)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()
            else:
                resp.failure(f"Se esperaba 400 y devolvió {resp.status_code}")

    @task(2)
    def flujo_crud_moneda_fisica(self):
        sufijo = "".join(random.choices(string.ascii_uppercase, k=6)) + str(random.randint(10, 99))
        nombre = f"MonTest_{sufijo}"
        simbolo = f"M{sufijo[:4]}"  # <= 10 caracteres

        # 1. Crear moneda
        with self.client.post(
            "/monedas/crear",
            data={"nombre_moneda": nombre, "simbolo": simbolo, "estado": "Activo"},
            name="POST /monedas/crear",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200 or resp.json().get("status") != "success":
                resp.failure(f"Error creando moneda: HTTP {resp.status_code} - {resp.text}")
                return
            resp.success()

        # 2. Obtener ID desde la vista
        resp_lista = self.client.get("/monedas/gestion", name="GET /monedas/gestion")
        if resp_lista.status_code != 200:
            return
        cod_moneda = extraer_id_por_nombre(resp_lista.text, nombre, "/monedas")
        if not cod_moneda:
            return

        # 3. Editar moneda
        with self.client.post(
            f"/monedas/editar/{cod_moneda}",
            data={"nombre_moneda": f"MonEdit_{sufijo}", "simbolo": simbolo, "estado": "Activo"},
            name="POST /monedas/editar/[id]",
            catch_response=True,
        ) as resp_edit:
            if resp_edit.status_code == 200 and resp_edit.json().get("status") == "success":
                resp_edit.success()
            else:
                resp_edit.failure(f"Error editando moneda #{cod_moneda}: {resp_edit.text}")

        # 4. Eliminar (desactivar) moneda
        with self.client.post(
            f"/monedas/eliminar/{cod_moneda}",
            name="POST /monedas/eliminar/[id]",
            catch_response=True,
        ) as resp_del:
            if resp_del.status_code == 200 and resp_del.json().get("status") == "success":
                resp_del.success()
            else:
                resp_del.failure(f"Error eliminando moneda #{cod_moneda}: {resp_del.text}")

    @task(2)
    def flujo_crud_moneda_digital(self):
        sufijo = "".join(random.choices(string.ascii_uppercase, k=6)) + str(random.randint(10, 99))
        nombre = f"DigTest_{sufijo}"
        simbolo = f"D{sufijo[:5]}"

        # 1. Crear moneda digital
        with self.client.post(
            "/monedas-digitales/crear",
            data={"nombre_digital": nombre, "simbolo_digital": simbolo, "estado_digital": "1"},
            name="POST /monedas-digitales/crear",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200 or resp.json().get("status") != "success":
                resp.failure(f"Error creando moneda digital: HTTP {resp.status_code} - {resp.text}")
                return
            resp.success()

        # 2. Obtener ID desde la vista
        resp_lista = self.client.get("/monedas/gestion", name="GET /monedas/gestion")
        if resp_lista.status_code != 200:
            return
        cod_dig = extraer_id_por_nombre(resp_lista.text, nombre, "/monedas-digitales")
        if not cod_dig:
            return

        # 3. Editar moneda digital
        with self.client.post(
            f"/monedas-digitales/editar/{cod_dig}",
            data={"nombre_digital": f"DigEdit_{sufijo}", "simbolo_digital": simbolo, "estado_digital": "1"},
            name="POST /monedas-digitales/editar/[id]",
            catch_response=True,
        ) as resp_edit:
            if resp_edit.status_code == 200 and resp_edit.json().get("status") == "success":
                resp_edit.success()
            else:
                resp_edit.failure(f"Error editando moneda digital #{cod_dig}: {resp_edit.text}")

        # 4. Eliminar (desactivar) moneda digital
        with self.client.post(
            f"/monedas-digitales/eliminar/{cod_dig}",
            name="POST /monedas-digitales/eliminar/[id]",
            catch_response=True,
        ) as resp_del:
            if resp_del.status_code == 200 and resp_del.json().get("status") == "success":
                resp_del.success()
            else:
                resp_del.failure(f"Error eliminando moneda digital #{cod_dig}: {resp_del.text}")