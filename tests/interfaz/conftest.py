import socket
import threading
import time
import pytest
from flask.sessions import SecureCookieSessionInterface
from playwright.sync_api import BrowserContext, Page
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import app
from models.db import ConexionBD

BASE_URL = "http://127.0.0.1:5000"


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


def limpiar_usuario(cedula: str, correo: str = ""):
    """Elimina un usuario/cliente temporal de seguridad y citas relacionadas para pruebas UI."""
    conn_neg = ConexionBD.obtener_conexion()
    cur_neg = conn_neg.cursor()
    try:
        cur_neg.execute("DELETE FROM citas WHERE cedula_usuario = %s", (cedula,))
        conn_neg.commit()
    finally:
        cur_neg.close()
        conn_neg.close()

    conn_sec = ConexionBD.obtener_conexion_seguridad()
    cur_sec = conn_sec.cursor()
    try:
        cur_sec.execute("DELETE FROM t_bitacora WHERE cedula_usuario = %s", (cedula,))
        if correo:
            cur_sec.execute(
                "DELETE FROM t_usuario WHERE cedula_usuario = %s OR correo = %s",
                (cedula, correo),
            )
        else:
            cur_sec.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s", (cedula,))
        conn_sec.commit()
    finally:
        cur_sec.close()
        conn_sec.close()


def _asegurar_datos_prueba_interfaz():
    """Garantiza usuarios base esperados por las pruebas de interfaz y retorna datos de limpieza."""
    conn_sec = ConexionBD.obtener_conexion_seguridad()
    cur_sec = conn_sec.cursor()
    creados = []
    try:
        for cedula, nombre, apellido, correo, clave, rol in [
            ("11111112", "Cliente", "UI", "cliente_ui_11111112@automall.com", "UiCliente123*", 4),
            ("99887766", "Temp", "UI", "ui_temp@automall.com", "UiPass123!", 1),
        ]:
            cur_sec.execute(
                "SELECT cedula_usuario FROM t_usuario WHERE cedula_usuario = %s OR correo = %s",
                (cedula, correo),
            )
            if not cur_sec.fetchone():
                cur_sec.execute(
                    """
                    INSERT INTO t_usuario
                        (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, estado, cod_rol, foto)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, 'default.png')
                    """,
                    (cedula, nombre, apellido, "04140000000", "Direccion UI", correo, generate_password_hash(clave), rol),
                )
                creados.append((cedula, correo))
        conn_sec.commit()
    finally:
        cur_sec.close()
        conn_sec.close()
    return creados


@pytest.fixture(scope="session", autouse=True)
def _servidor_flask_interfaz():
    """Levanta Flask en 127.0.0.1:5000 en modo TESTING si no está encendido."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    creados = _asegurar_datos_prueba_interfaz()

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
        for cedula, correo in creados:
            try:
                limpiar_usuario(cedula, correo)
            except Exception:
                pass


@pytest.fixture(scope="session")
def base_url(_servidor_flask_interfaz):
    return _servidor_flask_interfaz


@pytest.fixture
def ui_server(_servidor_flask_interfaz):
    """Crea una cita temporal para las pruebas de modal/edición/eliminación en /consultar."""
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cod_cita_ui = None
    try:
        cur.execute("SELECT cod_catalogo FROM catalogo WHERE estado = 'Activo' LIMIT 1")
        fila_cat = cur.fetchone()
        if not fila_cat:
            cur.execute("SELECT cod_catalogo FROM catalogo LIMIT 1")
            fila_cat = cur.fetchone()
        cod_cat = fila_cat[0] if fila_cat else 6

        cur.execute(
            """
            INSERT INTO citas (estado, fecha, hora, cod_catalogo, cedula_usuario, activo)
            VALUES ('Pendiente', '2029-12-01', '09:30:00', %s, '29880513', 1)
            """,
            (cod_cat,),
        )
        cod_cita_ui = cur.lastrowid
        conn.commit()
    finally:
        cur.close()
        conn.close()

    try:
        yield {"base_url": _servidor_flask_interfaz, "cod_cita_ui": cod_cita_ui}
    finally:
        if cod_cita_ui is not None:
            conn_del = ConexionBD.obtener_conexion()
            cur_del = conn_del.cursor()
            try:
                cur_del.execute("DELETE FROM citas WHERE cod_citas = %s", (cod_cita_ui,))
                conn_del.commit()
            finally:
                cur_del.close()
                conn_del.close()


def inyectar_sesion_admin(context: BrowserContext, base_url: str = BASE_URL):
    usuario = _obtener_usuario_por_correo("prueba@gmail.com")
    _agregar_cookie_sesion(context, base_url, {
        "cedula_usuario": usuario["cedula_usuario"],
        "usuario_nombre": usuario["nombre"],
        "cod_rol": usuario["cod_rol"],
    })


def inyectar_sesion_cliente(context: BrowserContext, base_url: str = BASE_URL):
    usuario = _obtener_usuario_por_correo("darye@gmail.com")
    _agregar_cookie_sesion(context, base_url, {
        "cedula_usuario": usuario["cedula_usuario"],
        "usuario_nombre": usuario["nombre"],
        "cod_rol": usuario["cod_rol"],
    })


def inyectar_captcha_cookie(context: BrowserContext, base_url: str = BASE_URL, codigo: str = "SMOKE"):
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
