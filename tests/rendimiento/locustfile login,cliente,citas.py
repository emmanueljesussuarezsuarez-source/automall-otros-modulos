# tests/rendimiento/locustfile.py
# Pruebas de Rendimiento – AutoMall v1.2
# Ejecutar todos los módulos:
#   py -m locust -f tests/rendimiento/locustfile.py --host=http://127.0.0.1:5000
# Ejecutar módulo por módulo:
#   Login   : py -m locust -f tests/rendimiento/locustfile.py --host=http://127.0.0.1:5000 --web-port 8090 UsuarioAnonimo UsuarioLoginValido
#   Clientes: py -m locust -f tests/rendimiento/locustfile.py --host=http://127.0.0.1:5000 --web-port 8090 UsuarioAdmin
#   Citas   : py -m locust -f tests/rendimiento/locustfile.py --host=http://127.0.0.1:5000 --web-port 8090 UsuarioCliente

import os
import re
import sys
import time
import threading
from datetime import date, timedelta
from flask.sessions import SecureCookieSessionInterface
from werkzeug.security import generate_password_hash
from locust import HttpUser, task, between, events

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app import app
from models.db import ConexionBD


# ─────────────────────────── CONFIGURACIÓN ───────────────────────────────────

ADMIN_CEDULA   = "99887766"
ADMIN_EMAIL    = "locust_admin@automall.com"
ADMIN_PASSWORD = "LocustAdmin1*"

CLIENTE_CEDULA   = "11111112"
CAPTCHA_CODE     = "ABCD"
VEHICULO_DEFAULT = "6"

_lock = threading.Lock()
_seq_cliente = 80000000
_seq_fecha = 0


def _siguiente_cedula():
    global _seq_cliente
    with _lock:
        _seq_cliente += 1
        return str(_seq_cliente)


def _siguiente_fecha():
    global _seq_fecha
    with _lock:
        _seq_fecha += 1
        fecha = date(2030, 1, 1) + timedelta(days=_seq_fecha % 3650)
        return fecha.strftime("%Y-%m-%d")


def _crear_cookie_firmada(data: dict) -> str:
    si = SecureCookieSessionInterface()
    serializer = si.get_signing_serializer(app)
    return serializer.dumps(data)


# ─────────────────────────── SETUP / TEARDOWN EN BD ──────────────────────────

def _limpiar_admin_locust():
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute("DELETE FROM t_bitacora WHERE cedula_usuario = %s", (ADMIN_CEDULA,))
    cur.execute("DELETE FROM t_det_repuesta WHERE cedula_usuario = %s", (ADMIN_CEDULA,))
    cur.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s OR correo = %s", (ADMIN_CEDULA, ADMIN_EMAIL))
    conn.commit()
    cur.close()
    conn.close()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Crea un usuario administrador temporal para que Locust pueda autenticarse."""
    _limpiar_admin_locust()
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO t_usuario (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, cod_rol) "
        "VALUES (%s, 'Locust', 'Admin', '04140001122', 'Sede AutoMall', %s, %s, 1)",
        (ADMIN_CEDULA, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD)),
    )
    conn.commit()
    cur.close()
    conn.close()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Elimina el usuario administrador temporal al finalizar la prueba."""
    try:
        _limpiar_admin_locust()
    except Exception:
        pass


# ─────────────────────────── HELPERS ─────────────────────────────────────────

def _obtener_cookie_captcha() -> str:
    """Genera una cookie de sesión firmada por Flask con el CAPTCHA válido."""
    return _crear_cookie_firmada({
        "captcha_codigo": CAPTCHA_CODE,
        "captcha_tiempo": time.time() + 86400,
    })


def _hacer_login(client, email, password):
    """Autentica al usuario via POST /login (JSON) usando bloque with."""
    client.cookies.clear()
    cookie_captcha = _obtener_cookie_captcha()
    with client.post(
        "/login",
        json={
            "email": email,
            "password": password,
            "captcha": CAPTCHA_CODE,
        },
        cookies={"session": cookie_captcha},
        headers={"Content-Type": "application/json"},
        name="POST /login [auth]",
        catch_response=True,
    ) as response:
        try:
            data = response.json()
            if data.get("status") == "success":
                response.success()
                return True
            response.failure(f"Login fallido: {data.get('message', 'sin mensaje')}")
            return False
        except Exception as e:
            response.failure(f"Respuesta no JSON: {e}")
            return False


# ─────────────────────────── PR-LOG: MÓDULO LOGIN ────────────────────────────

class UsuarioAnonimo(HttpUser):
    """
    PR-LOG-01, PR-LOG-02, PR-LOG-03:
    Carga de /login, generación de /captcha y rechazo de credenciales inválidas.
    """
    weight = 2
    wait_time = between(1, 3)

    @task(3)
    def pr_log_01_get_login(self):
        """PR-LOG-01: Carga de la página GET /login."""
        with self.client.get("/login", name="PR-LOG-01 GET /login", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Esperado 200, obtenido {r.status_code}")

    @task(2)
    def pr_log_02_get_captcha(self):
        """PR-LOG-02: Generación de imagen CAPTCHA GET /captcha."""
        with self.client.get("/captcha", name="PR-LOG-02 GET /captcha", catch_response=True) as r:
            if r.status_code == 200 and "image/png" in r.headers.get("Content-Type", ""):
                r.success()
            else:
                r.failure(f"Esperado image/png 200, obtenido {r.status_code}")

    @task(1)
    def pr_log_03_post_login_invalido(self):
        """PR-LOG-03: POST /login con credenciales inválidas."""
        cookie_captcha = _obtener_cookie_captcha()
        with self.client.post(
            "/login",
            json={"email": "noexiste@test.com", "password": "MalPass1!", "captcha": CAPTCHA_CODE},
            cookies={"session": cookie_captcha},
            headers={"Content-Type": "application/json"},
            name="PR-LOG-03 POST /login [inválido]",
            catch_response=True,
        ) as r:
            try:
                data = r.json()
                if data.get("status") == "error":
                    r.success()
                else:
                    r.failure("Se esperaba status=error")
            except Exception:
                r.failure("Respuesta no JSON")


class UsuarioLoginValido(HttpUser):
    """
    PR-LOG-04: Autenticación completa válida + cierre de sesión.
    """
    weight = 1
    wait_time = between(2, 5)

    @task
    def pr_log_04_login_valido(self):
        """PR-LOG-04: POST /login con credenciales válidas de administrador."""
        _hacer_login(self.client, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.client.get("/logout", name="GET /logout [cleanup]", allow_redirects=False)


# ─────────────────────────── PR-CLIE: MÓDULO CLIENTES (CRUD) ─────────────────

class UsuarioAdmin(HttpUser):
    """
    Módulo de Clientes:
      PR-CLIE-01: Consultar (GET /clientes)
      PR-CLIE-02: Crear (POST /registrar_clientes)
      PR-CLIE-03: Modificar (POST /clientes/editar/<cedula>)
      PR-CLIE-04: Eliminar (POST /clientes/eliminar/<cedula>)
    """
    weight = 2
    wait_time = between(1, 3)

    def on_start(self):
        self._autenticado = _hacer_login(self.client, ADMIN_EMAIL, ADMIN_PASSWORD)

    @task(3)
    def pr_clie_01_consultar_clientes(self):
        """PR-CLIE-01: Consultar listado de clientes (GET /clientes)."""
        with self.client.get(
            "/clientes",
            name="PR-CLIE-01 Consultar GET /clientes",
            allow_redirects=False,
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 302:
                r.failure("Sesión expirada – redirigido a /login")
            else:
                r.failure(f"Código inesperado: {r.status_code}")

    @task(1)
    def pr_clie_crud_crear_modificar_eliminar(self):
        """
        PR-CLIE-02, PR-CLIE-03 y PR-CLIE-04:
        Flujo CRUD limpio: Crear -> Modificar -> Eliminar.
        """
        cedula = _siguiente_cedula()
        correo = f"locust_{cedula}@automall.com"

        # PR-CLIE-02: Crear cliente
        with self.client.post(
            "/registrar_clientes",
            data={
                "cedula": cedula,
                "nombre": "Locust",
                "apellido": "Test",
                "telefono": "04141234567",
                "direccion": "Avenida Prueba Locust 123",
                "email": correo,
                "password": "LocustPass1*",
            },
            name="PR-CLIE-02 Crear POST /registrar_clientes",
            allow_redirects=False,
            catch_response=True,
        ) as r_crear:
            loc = r_crear.headers.get("Location", "")
            if r_crear.status_code in (200, 302) and "/login" not in loc:
                r_crear.success()
            else:
                r_crear.failure(f"Error creando cliente: {r_crear.status_code} -> {loc}")
                return

        # PR-CLIE-03: Modificar cliente
        with self.client.post(
            f"/clientes/editar/{cedula}",
            data={
                "nombre": "LocustEdit",
                "apellido": "TestEdit",
                "telefono": "04247654321",
                "direccion": "Calle Modificada Locust 456",
                "correo": correo,
            },
            name="PR-CLIE-03 Modificar POST /clientes/editar",
            allow_redirects=False,
            catch_response=True,
        ) as r_mod:
            loc = r_mod.headers.get("Location", "")
            if r_mod.status_code in (200, 302) and "/login" not in loc:
                r_mod.success()
            else:
                r_mod.failure(f"Error modificando cliente: {r_mod.status_code} -> {loc}")

        # PR-CLIE-04: Eliminar cliente
        with self.client.post(
            f"/clientes/eliminar/{cedula}",
            name="PR-CLIE-04 Eliminar POST /clientes/eliminar",
            allow_redirects=False,
            catch_response=True,
        ) as r_del:
            loc = r_del.headers.get("Location", "")
            if r_del.status_code in (200, 302) and "/login" not in loc:
                r_del.success()
            else:
                r_del.failure(f"Error eliminando cliente: {r_del.status_code} -> {loc}")


# ─────────────────────────── PR-CITA: MÓDULO CITAS (CRUD) ────────────────────

class UsuarioCliente(HttpUser):
    """
    Módulo de Citas:
      PR-CITA-01: Consultar citas (GET /consultar)
      PR-CITA-02: Crear / Agendar cita (POST /agendar)
      PR-CITA-03: Modificar / Reprogramar cita (POST /modificar/<cod_cita>)
      PR-CITA-04: Eliminar / Cancelar cita (POST /eliminar/<cod_cita>)
    """
    weight = 3
    wait_time = between(1, 3)

    def on_start(self):
        self._autenticado = _hacer_login(self.client, ADMIN_EMAIL, ADMIN_PASSWORD)

    @task(3)
    def pr_cita_01_consultar_citas(self):
        """PR-CITA-01: Consultar citas (GET /consultar)."""
        with self.client.get(
            "/consultar",
            name="PR-CITA-01 Consultar GET /consultar",
            allow_redirects=False,
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 302:
                r.failure("Sesión expirada – redirigido a /login")
            else:
                r.failure(f"Código inesperado: {r.status_code}")

    @task(1)
    def pr_cita_crud_crear_modificar_eliminar(self):
        """
        PR-CITA-02, PR-CITA-03 y PR-CITA-04:
        Crea una cita en fecha única -> extrae su cod_cita de /consultar -> modifica -> elimina.
        """
        fecha_cita = _siguiente_fecha()

        # PR-CITA-02: Crear cita (POST /agendar)
        with self.client.post(
            "/agendar",
            data={
                "fecha_cita": fecha_cita,
                "hora_cita": "10:00",
                "cod_catalogo": VEHICULO_DEFAULT,
                "cedula_cliente": CLIENTE_CEDULA,
            },
            name="PR-CITA-02 Crear POST /agendar",
            allow_redirects=False,
            catch_response=True,
        ) as r_crear:
            loc = r_crear.headers.get("Location", "")
            if r_crear.status_code in (200, 302) and "/login" not in loc:
                r_crear.success()
            else:
                r_crear.failure(f"Error agendando cita: {r_crear.status_code} -> {loc}")
                return

        # Obtener el último cod_cita registrado en /consultar
        r_list = self.client.get("/consultar", name="GET /consultar [buscar id]")
        cods = re.findall(r'data-cod="(\d+)"', r_list.text)
        if not cods:
            return
        cod_cita = cods[0]

        # PR-CITA-03: Modificar cita (POST /modificar/<cod_cita>)
        with self.client.post(
            f"/modificar/{cod_cita}",
            data={
                "fecha": fecha_cita,
                "hora": "11:00",
                "estado": "Pendiente",
            },
            name="PR-CITA-03 Modificar POST /modificar",
            allow_redirects=False,
            catch_response=True,
        ) as r_mod:
            loc = r_mod.headers.get("Location", "")
            if r_mod.status_code in (200, 302) and "/login" not in loc:
                r_mod.success()
            else:
                r_mod.failure(f"Error modificando cita: {r_mod.status_code} -> {loc}")

        # PR-CITA-04: Eliminar cita (POST /eliminar/<cod_cita>)
        with self.client.post(
            f"/eliminar/{cod_cita}",
            name="PR-CITA-04 Eliminar POST /eliminar",
            allow_redirects=False,
            catch_response=True,
        ) as r_del:
            loc = r_del.headers.get("Location", "")
            if r_del.status_code in (200, 302) and "/login" not in loc:
                r_del.success()
            else:
                r_del.failure(f"Error eliminando cita: {r_del.status_code} -> {loc}")
