import random
import re
import string
from locust import HttpUser, task, between

CREDENCIALES = {
    "email": "prueba@gmail.com",
    "password": "12345678",
}


def extraer_id_por_nombre(html, nombre_buscado, prefijo_ruta="/bancos"):
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


class UsuarioBancos(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        with self.client.post("/login", json=CREDENCIALES, name="POST /login", catch_response=True) as resp:
            if resp.status_code == 200 and resp.json().get("status") == "success":
                resp.success()
            else:
                resp.failure(f"Login fallido: {resp.text}")

    @task(4)
    def listar_bancos(self):
        with self.client.get("/bancos/gestion", name="GET /bancos/gestion", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} listando bancos")

    @task(1)
    def validacion_banco_corto(self):
        """Caso negativo controlado: nombre < 2 caracteres debe devolver 400."""
        with self.client.post(
            "/bancos/gestion",
            data={"nombre_banco": "A", "estado": "Activo"},
            name="POST /bancos/gestion (validacion_400)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()
            else:
                resp.failure(f"Se esperaba 400 y devolvió {resp.status_code}")

    @task(3)
    def flujo_crud_banco(self):
        sufijo = "".join(random.choices(string.ascii_uppercase, k=6)) + str(random.randint(100, 999))
        nombre = f"BancoTest_{sufijo}"

        # 1. Crear banco (POST form)
        with self.client.post(
            "/bancos/gestion",
            data={"nombre_banco": nombre, "estado": "Activo"},
            name="POST /bancos/gestion (crear)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200 or resp.json().get("status") != "success":
                resp.failure(f"Error creando banco: HTTP {resp.status_code} - {resp.text}")
                return
            resp.success()

        # 2. Consultar listado para obtener el ID recién creado
        resp_lista = self.client.get("/bancos/gestion", name="GET /bancos/gestion")
        if resp_lista.status_code != 200:
            return
        cod_banco = extraer_id_por_nombre(resp_lista.text, nombre, "/bancos")
        if not cod_banco:
            return

        # 3. Editar banco
        nombre_editado = f"BancoEdit_{sufijo}"
        with self.client.post(
            f"/bancos/editar/{cod_banco}",
            data={"nombre_banco": nombre_editado, "estado": "Activo"},
            name="POST /bancos/editar/[id]",
            catch_response=True,
        ) as resp_edit:
            if resp_edit.status_code == 200 and resp_edit.json().get("status") == "success":
                resp_edit.success()
            else:
                resp_edit.failure(f"Error editando banco #{cod_banco}: {resp_edit.text}")

        # 4. Eliminar (desactivar) banco de prueba
        with self.client.post(
            f"/bancos/eliminar/{cod_banco}",
            name="POST /bancos/eliminar/[id]",
            catch_response=True,
        ) as resp_del:
            if resp_del.status_code == 200 and resp_del.json().get("status") == "success":
                resp_del.success()
            else:
                resp_del.failure(f"Error eliminando banco #{cod_banco}: {resp_del.text}")