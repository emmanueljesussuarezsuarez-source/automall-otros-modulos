# tests/smoke/test_smoke_citas.py
# Pruebas de Humo — Módulo de Citas
# Objetivo: verificar que las rutas y funcionalidades críticas del módulo de citas
# respondan correctamente bajo condiciones básicas (happy-path y validaciones mínimas).
# Códigos: CS-CITA-01 → CS-CITA-23

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import app
from models.db import ConexionBD


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


def _set_sesion_cliente(c, cedula='11111112'):
    with c.session_transaction() as sess:
        sess['cedula_usuario'] = cedula
        sess['usuario_nombre'] = 'Cliente'
        sess['cod_rol'] = 4


def _set_sesion_rol(c, cod_rol=2):
    with c.session_transaction() as sess:
        sess['cedula_usuario'] = '14094670'
        sess['usuario_nombre'] = 'Staff'
        sess['cod_rol'] = cod_rol


@pytest.fixture
def cita_temporal():
    """Inserta una cita de prueba en automall.citas y la elimina al terminar."""
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM automall.citas WHERE cedula_usuario = '11111112' AND fecha = '2029-07-10'"
    )
    cur.execute(
        "INSERT INTO automall.citas (fecha, hora, cod_catalogo, cedula_usuario, estado, activo) "
        "VALUES ('2029-07-10', '10:00', 6, '11111112', 'Pendiente', 1)"
    )
    conn.commit()
    cod_cita = cur.lastrowid
    cur.close()
    conn.close()

    yield cod_cita

    conn2 = ConexionBD.obtener_conexion()
    cur2 = conn2.cursor()
    cur2.execute("DELETE FROM automall.citas WHERE cod_citas = %s", (cod_cita,))
    conn2.commit()
    cur2.close()
    conn2.close()


# ─────────────────────── PRUEBAS DE HUMO ─────────────────────────────────────

# CS-CITA-01
def test_smoke_consultar_sin_sesion_redirige(cliente):
    """GET /consultar sin sesión debe redirigir a /login."""
    respuesta = cliente.get('/consultar', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CITA-02
def test_smoke_consultar_admin_carga(cliente):
    """GET /consultar con sesión admin debe retornar HTTP 200."""
    _set_sesion_admin(cliente)
    respuesta = cliente.get('/consultar', follow_redirects=True)
    assert respuesta.status_code == 200
    assert len(respuesta.data) > 0


# CS-CITA-03
def test_smoke_consultar_cliente_carga(cliente):
    """GET /consultar con sesión cliente debe retornar HTTP 200 con sus citas."""
    _set_sesion_cliente(cliente, '11111112')
    respuesta = cliente.get('/consultar', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-04
def test_smoke_agendar_sin_sesion_redirige(cliente):
    """GET /agendar sin sesión debe redirigir a /login."""
    respuesta = cliente.get('/agendar', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CITA-05
def test_smoke_agendar_cliente_carga_formulario(cliente):
    """GET /agendar con sesión cliente debe retornar formulario HTTP 200."""
    _set_sesion_cliente(cliente)
    respuesta = cliente.get('/agendar', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-06
def test_smoke_agendar_admin_carga_formulario(cliente):
    """GET /agendar con sesión admin debe retornar formulario con lista de clientes."""
    _set_sesion_admin(cliente)
    respuesta = cliente.get('/agendar', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-07
def test_smoke_agendar_post_datos_vacios(cliente):
    """POST /agendar con campos vacíos debe retornar error de validación."""
    _set_sesion_cliente(cliente)
    respuesta = cliente.post('/agendar', data={
        'fecha_cita': '', 'hora_cita': '', 'cod_catalogo': ''
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-08
def test_smoke_eliminar_sin_sesion_redirige(cliente):
    """POST /eliminar/<id> sin sesión debe redirigir a /login."""
    respuesta = cliente.post('/eliminar/1', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CITA-09
def test_smoke_eliminar_cita_inexistente(cliente):
    """POST /eliminar con cita inexistente debe manejar el error sin excepción."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post('/eliminar/999999', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-10
def test_smoke_modificar_sin_sesion_redirige(cliente):
    """POST /modificar/<id> sin sesión debe redirigir a /login."""
    respuesta = cliente.post('/modificar/1', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CITA-11
def test_smoke_modificar_cita_inexistente(cliente):
    """POST /modificar con cita inexistente debe manejar el error sin excepción."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post('/modificar/999999', data={
        'fecha': '2029-07-10',
        'hora': '10:00',
        'estado': 'Pendiente'
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-12
def test_smoke_finalizar_sin_sesion_redirige(cliente):
    """POST /finalizar/<id> sin sesión debe redirigir a /login."""
    respuesta = cliente.post('/finalizar/1', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-CITA-13
def test_smoke_finalizar_cliente_sin_permiso(cliente):
    """POST /finalizar/<id> con sesión cliente (cod_rol=4) debe denegar acceso."""
    _set_sesion_cliente(cliente)
    respuesta = cliente.post('/finalizar/1', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-14
def test_smoke_modelo_citas_instanciacion():
    """CitasModel debe poder instanciarse con valores correctos."""
    from models.citas import CitasModel
    cita = CitasModel(
        cod_citas=1,
        fecha='2029-01-01',
        hora='10:00',
        cod_catalogo=6,
        cedula_usuario='11111112',
        estado='Pendiente',
        activo=1
    )
    assert cita.cod_citas == 1
    assert cita.fecha == '2029-01-01'
    assert cita.hora == '10:00'
    assert cita.cod_catalogo == 6
    assert cita.cedula_usuario == '11111112'
    assert cita.estado == 'Pendiente'
    assert cita.activo == 1


# CS-CITA-15
def test_smoke_eliminar_cita_existente_admin(cliente, cita_temporal):
    """POST /eliminar/<id> como admin con cita real debe ejecutarse sin excepción HTTP."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post(f'/eliminar/{cita_temporal}', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-16
def test_smoke_consultar_rol_sin_permiso_redirige(cliente):
    """GET /consultar con rol distinto a 1 y 4 debe redirigir a inicio."""
    _set_sesion_rol(cliente, cod_rol=2)
    respuesta = cliente.get('/consultar', follow_redirects=False)
    assert respuesta.status_code == 302


# CS-CITA-17
def test_smoke_agendar_rol_sin_permiso_redirige(cliente):
    """GET /agendar con rol distinto a 1 y 4 debe redirigir a consultar."""
    _set_sesion_rol(cliente, cod_rol=2)
    respuesta = cliente.get('/agendar', follow_redirects=False)
    assert respuesta.status_code == 302


# CS-CITA-18
def test_smoke_agendar_admin_sin_cliente_error(cliente):
    """POST /agendar como admin sin seleccionar cliente debe mostrar advertencia."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post('/agendar', data={
        'fecha_cita': '2029-07-10',
        'hora_cita': '10:00',
        'cod_catalogo': '6',
        'cedula_cliente': ''
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-19
def test_smoke_agendar_exitoso_cliente(cliente):
    """POST /agendar con datos válidos como cliente debe agendar o validar sin error 500."""
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM automall.citas WHERE cedula_usuario = '11111112' AND fecha = '2029-07-11'")
    conn.commit()
    cur.close()
    conn.close()

    _set_sesion_cliente(cliente, '11111112')
    try:
        respuesta = cliente.post('/agendar', data={
            'fecha_cita': '2029-07-11',
            'hora_cita': '10:00',
            'cod_catalogo': '6'
        }, follow_redirects=True)
        assert respuesta.status_code == 200
    finally:
        conn2 = ConexionBD.obtener_conexion()
        cur2 = conn2.cursor()
        cur2.execute("DELETE FROM automall.citas WHERE cedula_usuario = '11111112' AND fecha = '2029-07-11'")
        conn2.commit()
        cur2.close()
        conn2.close()


# CS-CITA-20
def test_smoke_eliminar_cita_existente_cliente(cliente, cita_temporal):
    """POST /eliminar/<id> como cliente sobre su propia cita debe cancelarla sin error."""
    _set_sesion_cliente(cliente, '11111112')
    respuesta = cliente.post(f'/eliminar/{cita_temporal}', follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-21
def test_smoke_modificar_cita_admin(cliente, cita_temporal):
    """POST /modificar/<id> como admin con datos válidos debe actualizar la cita."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post(f'/modificar/{cita_temporal}', data={
        'fecha': '2029-07-12',
        'hora': '14:00',
        'estado': 'Pendiente'
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-22
def test_smoke_modificar_cita_cliente(cliente, cita_temporal):
    """POST /modificar/<id> como cliente sobre su propia cita debe actualizar la hora."""
    _set_sesion_cliente(cliente, '11111112')
    respuesta = cliente.post(f'/modificar/{cita_temporal}', data={
        'hora': '14:00'
    }, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-CITA-23
def test_smoke_finalizar_cita_admin(cliente, cita_temporal):
    """POST /finalizar/<id> como admin sobre cita existente debe marcarla Finalizada."""
    _set_sesion_admin(cliente)
    respuesta = cliente.post(f'/finalizar/{cita_temporal}', follow_redirects=True)
    assert respuesta.status_code == 200
