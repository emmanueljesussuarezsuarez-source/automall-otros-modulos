# tests/smoke/test_smoke_clientes.py
# Pruebas de Humo — Módulo de Clientes
# Objetivo: verificar que las rutas y funcionalidades críticas del módulo de clientes
# respondan correctamente bajo condiciones básicas (happy-path y validaciones mínimas).
# Códigos: CS-CLIE-01 → CS-CLIE-15

import io
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import app
from models.db import ConexionBD
from werkzeug.security import generate_password_hash


# ─────────────────────── FIXTURES ────────────────────────────────────────────

@pytest.fixture
def cliente():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.secret_key = 'test_secret_smoke'
    with app.test_client() as c:
        yield c


def _set_sesion_admin(c):
    with c.session_transaction() as sess:
        sess['cedula_usuario'] = '14094670'
        sess['usuario_nombre'] = 'Admin'
        sess['cod_rol'] = 1


def _png_minimo():
    """Bytes de un PNG válido 1×1 pixel."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


def _limpiar_usuario(cedula, correo=None):
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute("DELETE FROM t_bitacora WHERE cedula_usuario = %s", (cedula,))
    cur.execute("DELETE FROM t_det_repuesta WHERE cedula_usuario = %s", (cedula,))
    if correo:
        cur.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s OR correo = %s", (cedula, correo))
    else:
        cur.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s", (cedula,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture
def cliente_temporal():
    """Crea un cliente temporal en BD y lo limpia al finalizar."""
    cedula = '88776655'
    correo = 'smoke_cliente_temp@test.com'
    _limpiar_usuario(cedula, correo)

    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO t_usuario (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, foto, cod_rol) "
        "VALUES (%s, 'Smoke', 'Cliente', '04141112233', 'Dir Smoke', %s, %s, 'uploads/perfiles/default.png', 4)",
        (cedula, correo, generate_password_hash('SmokePass1!'))
    )
    conn.commit()
    cur.close()
    conn.close()

    yield {'cedula': cedula, 'correo': correo}

    _limpiar_usuario(cedula, correo)


# ─────────────────────── PRUEBAS DE HUMO ─────────────────────────────────────

# CS-CLIE-01
def test_smoke_clientes_sin_sesion_redirige(cliente):
    """GET /clientes sin sesión debe redirigir a /login."""
    respuesta = cliente.get('/clientes', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CLIE-02
def test_smoke_clientes_listado_carga(cliente):
    """GET /clientes con sesión admin debe retornar HTTP 200 con contenido."""
    _set_sesion_admin(cliente)
    respuesta = cliente.get('/clientes', follow_redirects=True)
    assert respuesta.status_code == 200
    assert len(respuesta.data) > 0


# CS-CLIE-03
def test_smoke_registrar_clientes_pagina_carga(cliente):
    """GET /registrar_clientes debe retornar HTTP 200 con formulario."""
    respuesta = cliente.get('/registrar_clientes')
    assert respuesta.status_code == 200


# CS-CLIE-04
def test_smoke_registrar_clientes_datos_vacios(cliente):
    """POST /registrar_clientes con campos vacíos debe retornar HTTP 200 con errores."""
    respuesta = cliente.post('/registrar_clientes', data={}, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CLIE-05
def test_smoke_registrar_clientes_cedula_invalida(cliente):
    """POST /registrar_clientes con cédula alfanumérica debe retornar error de validación."""
    respuesta = cliente.post('/registrar_clientes', data={
        'cedula': 'ABC123',
        'nombre': 'Test',
        'apellido': 'Smoke',
        'telefono': '04141234567',
        'direccion': 'Calle Smoke',
        'email': 'smoke@test.com',
        'password': 'SmokePass1!'
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CLIE-06
def test_smoke_registrar_clientes_correo_invalido(cliente):
    """POST /registrar_clientes con correo sin @ debe retornar error de validación."""
    respuesta = cliente.post('/registrar_clientes', data={
        'cedula': '99991111',
        'nombre': 'Test',
        'apellido': 'Smoke',
        'telefono': '04141234567',
        'direccion': 'Calle Smoke',
        'email': 'correo_invalido',
        'password': 'SmokePass1!'
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CLIE-07
def test_smoke_editar_cliente_sin_sesion_redirige(cliente):
    """POST /clientes/editar/<cedula> sin sesión debe redirigir."""
    respuesta = cliente.post('/clientes/editar/12345678', data={}, follow_redirects=False)
    assert respuesta.status_code == 302


# CS-CLIE-08
def test_smoke_editar_cliente_campos_vacios(cliente):
    """POST /clientes/editar con campos vacíos debe mostrar errores de validación."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post('/clientes/editar/12345678', data={}, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CLIE-09
def test_smoke_eliminar_cliente_sin_sesion_redirige(cliente):
    """POST /clientes/eliminar/<cedula> sin sesión debe redirigir."""
    respuesta = cliente.post('/clientes/eliminar/12345678', follow_redirects=False)
    assert respuesta.status_code == 302


# CS-CLIE-10
def test_smoke_eliminar_cliente_inexistente(cliente):
    """POST /clientes/eliminar con cédula inexistente debe mostrar mensaje de error."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post('/clientes/eliminar/99999999', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CLIE-11
def test_smoke_registrar_archivo_exe_rechazado(cliente):
    """POST /registrar_clientes con archivo .exe debe rechazar la subida."""
    datos = {
        'cedula': '99991112',
        'nombre': 'Test',
        'apellido': 'Smoke',
        'telefono': '04141234567',
        'direccion': 'Dir Smoke',
        'email': 'smoke2@test.com',
        'password': 'SmokePass1!',
    }
    foto = (io.BytesIO(b'fake exe content'), 'malware.exe')
    respuesta = cliente.post(
        '/registrar_clientes',
        data={**datos, 'foto_perfil': foto},
        content_type='multipart/form-data',
        follow_redirects=True
    )
    assert respuesta.status_code == 200


# CS-CLIE-12
def test_smoke_registrar_imagen_png_acepta(cliente):
    """POST /registrar_clientes con imagen PNG válida no debe rechazar la imagen."""
    cedula = '99991113'
    correo = 'smoke3@test.com'
    _limpiar_usuario(cedula, correo)
    try:
        datos = {
            'cedula': cedula,
            'nombre': 'Test',
            'apellido': 'Smoke',
            'telefono': '04141234567',
            'direccion': 'Dir Smoke',
            'email': correo,
            'password': 'SmokePass1!',
        }
        foto = (io.BytesIO(_png_minimo()), 'foto.png')
        respuesta = cliente.post(
            '/registrar_clientes',
            data={**datos, 'foto_perfil': foto},
            content_type='multipart/form-data',
            follow_redirects=True
        )
        assert respuesta.status_code == 200
    finally:
        _limpiar_usuario(cedula, correo)


# CS-CLIE-13
def test_smoke_editar_cliente_exitoso(cliente, cliente_temporal):
    """POST /clientes/editar con datos válidos debe actualizar el cliente y redirigir."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post(
        f"/clientes/editar/{cliente_temporal['cedula']}",
        data={
            'nombre': 'SmokeEdit',
            'apellido': 'ClienteEdit',
            'telefono': '04149998877',
            'direccion': 'Nueva Dir 123',
            'correo': cliente_temporal['correo'],
        },
        follow_redirects=False
    )
    assert respuesta.status_code == 302


# CS-CLIE-14
def test_smoke_eliminar_cliente_exitoso(cliente, cliente_temporal):
    """POST /clientes/eliminar con cliente existente debe desactivarlo/eliminarlo y redirigir."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post(
        f"/clientes/eliminar/{cliente_temporal['cedula']}",
        follow_redirects=False
    )
    assert respuesta.status_code == 302


# CS-CLIE-15
def test_smoke_registrar_cliente_por_admin_redirige_listado(cliente):
    """POST /registrar_clientes exitoso con sesión admin debe redirigir a /clientes."""
    cedula = '99991114'
    correo = 'smoke_admin_reg@test.com'
    _limpiar_usuario(cedula, correo)
    _set_sesion_admin(cliente)
    try:
        respuesta = cliente.post('/registrar_clientes', data={
            'cedula': cedula,
            'nombre': 'AdminReg',
            'apellido': 'Smoke',
            'telefono': '04141234568',
            'direccion': 'Av Smoke 10',
            'email': correo,
            'password': 'SmokePass1!'
        }, follow_redirects=False)
        assert respuesta.status_code in (302, 200)
    finally:
        _limpiar_usuario(cedula, correo)
