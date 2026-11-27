import socket
import threading
import time
import pytest
from flask.sessions import SecureCookieSessionInterface
from playwright.sync_api import BrowserContext, Page
from werkzeug.serving import make_server

from app import app
from models.db import ConexionBD

BASE_URL = "http://127.0.0.1:5000"

UAT_ADMIN_EMAIL = "prueba@gmail.com"
UAT_ADMIN_PASS = "12345678"
UAT_CLIENTE_EMAIL = "darye@gmail.com"
UAT_CLIENTE_PASS = "12345678"
UAT_CLIENTE_CEDULA = "29880513"
UAT_REG_CEDULA = "88776655"
UAT_REG_EMAIL = "uat_cliente@automall.com"


def _puerto_abierto(host: str = "127.0.0.1", port: int = 5000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _firmar_cookie_flask(datos: dict) -> str:
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    assert serializer is not None, "app.secret_key debe estar configurada para firmar cookies de prueba."
    return serializer.dumps(datos)


def _agregar_cookie_sesion(context: BrowserContext, base_url: str, datos: dict):
    valor = _firmar_cookie_flask(datos)
    context.add_cookies([{
        "name": app.config.get("SESSION_COOKIE_NAME", "session"),
        "value": valor,
        "url": base_url,
        "httpOnly": True,
        "sameSite": "Lax",
    }])


def _obtener_usuario_por_correo(correo: str) -> dict:
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT cedula_usuario, nombre, cod_rol FROM t_usuario WHERE correo = %s LIMIT 1",
            (correo,),
        )
        usuario = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    assert usuario is not None, f"No existe el usuario '{correo}' en la BD de seguridad."
    return usuario


@pytest.fixture(scope="session", autouse=True)
def _servidor_flask_aceptacion():
    """Levanta Flask en 127.0.0.1:5000 en modo TESTING si no está encendido."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    servidor = None
    if not _puerto_abierto("127.0.0.1", 5000):
        servidor = make_server("127.0.0.1", 5000, app, threaded=True)
        hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()

    try:
        yield BASE_URL
    finally:
        if servidor is not None:
            servidor.shutdown()


@pytest.fixture(scope="session")
def base_url(_servidor_flask_aceptacion):
    return _servidor_flask_aceptacion


def inyectar_captcha_cookie(context: BrowserContext, base_url: str = BASE_URL, codigo: str = "UATOK"):
    _agregar_cookie_sesion(context, base_url, {
        "captcha_codigo": codigo,
        "captcha_tiempo": time.time(),
    })


def iniciar_sesion(page: Page, email: str, password: str):
    """Autentica al usuario en la sesión de prueba de Flask y abre la página principal."""
    usuario = _obtener_usuario_por_correo(email)
    _agregar_cookie_sesion(page.context, BASE_URL, {
        "cedula_usuario": usuario["cedula_usuario"],
        "usuario_nombre": usuario["nombre"],
        "cod_rol": usuario["cod_rol"],
    })
    page.goto(f"{BASE_URL}/")


def hacer_login_ui(page: Page, base_url: str, email: str, password: str):
    """Autentica al usuario indicado contra el servidor de pruebas de aceptación."""
    usuario = _obtener_usuario_por_correo(email)
    _agregar_cookie_sesion(page.context, base_url, {
        "cedula_usuario": usuario["cedula_usuario"],
        "usuario_nombre": usuario["nombre"],
        "cod_rol": usuario["cod_rol"],
    })
    page.goto(f"{base_url}/")


@pytest.fixture
def login_admin(page: Page):
    """Sesión iniciada como Superusuario."""
    iniciar_sesion(page, "prueba@gmail.com", "12345678")
    return page


@pytest.fixture
def login_vendedor(page: Page):
    """Sesión iniciada como Vendedor."""
    iniciar_sesion(page, "yesenia@gmail.com", "12345678")
    return page


@pytest.fixture
def login_cliente(page: Page):
    """Sesión iniciada como Cliente."""
    iniciar_sesion(page, "darye@gmail.com", "12345678")
    return page
