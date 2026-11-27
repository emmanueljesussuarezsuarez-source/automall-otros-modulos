# tests/smoke/test_smoke_login.py
# Pruebas de Humo — Módulo de Login y Autenticación
# Objetivo: verificar que las rutas y funcionalidades críticas del módulo respondan
# correctamente bajo condiciones normales y validaciones esenciales antes de suites exhaustivas.
# Códigos: CS-LOG-01 → CS-LOG-22

import time
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import app
from models.auth import Auth
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


def _set_captcha(c, codigo='SMOKE'):
    """Establece captcha válido en sesión."""
    with c.session_transaction() as sess:
        sess['captcha_codigo'] = codigo
        sess['captcha_tiempo'] = time.time()


def _set_sesion(c, cedula='14094670', nombre='Admin', rol=1):
    """Establece sesión autenticada."""
    with c.session_transaction() as sess:
        sess['cedula_usuario'] = cedula
        sess['usuario_nombre'] = nombre
        sess['cod_rol'] = rol


@pytest.fixture
def usuario_temporal():
    """Crea usuario temporal con preguntas de seguridad en BD y lo limpia al terminar."""
    cedula = '55544433'
    correo = 'smoke_login@automall.com'
    pass_plana = 'SmokePass1!'
    pass_hash = generate_password_hash(pass_plana)

    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute("DELETE FROM t_bitacora WHERE cedula_usuario = %s", (cedula,))
    cur.execute("DELETE FROM t_det_repuesta WHERE cedula_usuario = %s", (cedula,))
    cur.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s OR correo = %s", (cedula, correo))
    cur.execute(
        "INSERT INTO t_usuario (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, cod_rol) "
        "VALUES (%s, 'Smoke', 'Login', '04140000001', 'Dir Smoke', %s, %s, 4)",
        (cedula, correo, pass_hash)
    )
    cur.execute(
        "SELECT cod_preguntas FROM t_banco_preguntas "
        "WHERE cod_preguntas NOT IN (SELECT cod_preguntas FROM t_det_repuesta) LIMIT 2"
    )
    pregs = [r[0] for r in cur.fetchall()]
    if len(pregs) >= 2:
        cur.execute(
            "INSERT INTO t_det_repuesta (cedula_usuario, cod_preguntas, respuesta) VALUES (%s, %s, 'respuno')",
            (cedula, pregs[0])
        )
        cur.execute(
            "INSERT INTO t_det_repuesta (cedula_usuario, cod_preguntas, respuesta) VALUES (%s, %s, 'respdos')",
            (cedula, pregs[1])
        )
    conn.commit()
    cur.close()
    conn.close()

    yield {'cedula': cedula, 'correo': correo, 'password': pass_plana}

    conn2 = ConexionBD.obtener_conexion_seguridad()
    cur2 = conn2.cursor()
    cur2.execute("DELETE FROM t_bitacora WHERE cedula_usuario = %s", (cedula,))
    cur2.execute("DELETE FROM t_det_repuesta WHERE cedula_usuario = %s", (cedula,))
    cur2.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s", (cedula,))
    conn2.commit()
    cur2.close()
    conn2.close()


# ─────────────────────── PRUEBAS DE HUMO ─────────────────────────────────────

# CS-LOG-01
def test_smoke_login_pagina_carga(cliente):
    """La página de login debe responder HTTP 200."""
    respuesta = cliente.get('/login')
    assert respuesta.status_code == 200


# CS-LOG-02
def test_smoke_captcha_genera_imagen(cliente):
    """El endpoint /captcha debe retornar imagen PNG."""
    respuesta = cliente.get('/captcha')
    assert respuesta.status_code == 200
    assert respuesta.content_type == 'image/png'


# CS-LOG-03
def test_smoke_captcha_cabeceras_anti_cache(cliente):
    """La respuesta de /captcha debe incluir cabecera Cache-Control."""
    respuesta = cliente.get('/captcha')
    assert 'no-cache' in respuesta.headers.get('Cache-Control', '')


# CS-LOG-04
def test_smoke_login_post_sin_json_retorna_400(cliente):
    """POST /login con form-data debe retornar HTTP 400."""
    respuesta = cliente.post('/login', data={'email': 'x@x.com', 'password': '123'})
    assert respuesta.status_code == 400


# CS-LOG-05
def test_smoke_login_post_captcha_incorrecto(cliente):
    """POST /login con captcha inválido debe retornar error y recargar_captcha=True."""
    _set_captcha(cliente, 'SMOKE')
    respuesta = cliente.post(
        '/login',
        json={'email': 'admin@automall.com', 'password': 'Test1234!', 'captcha': 'MALO'},
        content_type='application/json'
    )
    data = respuesta.get_json()
    assert data['status'] == 'error'
    assert data.get('recargar_captcha') is True


# CS-LOG-06
def test_smoke_login_exitoso(cliente, usuario_temporal):
    """POST /login con credenciales válidas y captcha correcto debe retornar success."""
    _set_captcha(cliente, 'SMOKE')
    respuesta = cliente.post(
        '/login',
        json={
            'email': usuario_temporal['correo'],
            'password': usuario_temporal['password'],
            'captcha': 'SMOKE'
        },
        content_type='application/json'
    )
    data = respuesta.get_json()
    assert data['status'] == 'success'


# CS-LOG-07
def test_smoke_logout_redirige_a_login(cliente):
    """GET /logout debe redirigir a /login."""
    _set_sesion(cliente)
    respuesta = cliente.get('/logout', follow_redirects=False)
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-LOG-08
def test_smoke_logout_limpia_sesion(cliente):
    """Después del logout, cedula_usuario no debe estar en sesión."""
    _set_sesion(cliente)
    cliente.get('/logout', follow_redirects=True)
    with cliente.session_transaction() as sess:
        assert 'cedula_usuario' not in sess


# CS-LOG-09
def test_smoke_recuperar_pagina_carga(cliente):
    """GET /recuperar debe retornar HTTP 200."""
    respuesta = cliente.get('/recuperar')
    assert respuesta.status_code == 200


# CS-LOG-10
def test_smoke_recuperar_correo_invalido(cliente):
    """POST /recuperar con email sin @ debe mostrar advertencia."""
    respuesta = cliente.post('/recuperar', data={'email': 'correo_sin_arroba'}, follow_redirects=True)
    assert respuesta.status_code == 200


# CS-LOG-11
def test_smoke_recuperar_correo_inexistente(cliente):
    """POST /recuperar con correo no registrado debe mostrar flash de error."""
    respuesta = cliente.post('/recuperar', data={'email': 'noexiste_smoke@automall.com'}, follow_redirects=True)
    assert respuesta.status_code == 200
    assert len(respuesta.data) > 0


# CS-LOG-12
def test_smoke_verificar_respuesta_sin_sesion_redirige(cliente):
    """POST /verificar_respuesta sin sesión debe redirigir."""
    respuesta = cliente.post('/verificar_respuesta', data={'respuesta': ['r1', 'r2']}, follow_redirects=False)
    assert respuesta.status_code == 302


# CS-LOG-13
def test_smoke_cambiar_password_sin_sesion_redirige(cliente):
    """POST /cambiar_password sin sesión autorizada debe redirigir a /login."""
    respuesta = cliente.post(
        '/cambiar_password',
        data={'nueva_password': 'Abc1234!', 'confirmar_password': 'Abc1234!'},
        follow_redirects=False
    )
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')


# CS-LOG-14
def test_smoke_modelo_auth_instanciacion_y_setters():
    """La clase Auth debe instanciarse y permitir modificar sus propiedades."""
    obj = Auth('12345678', 'Juan', 'Perez', '0981234567', 'Calle 1', 'juan@test.com', 'hash123')
    assert obj.cedula_usuario == '12345678'
    assert obj.correo == 'juan@test.com'
    obj.cedula_usuario = '87654321'
    obj.nombre = 'Carlos'
    obj.apellido = 'Lopez'
    obj.telefono = '04141112233'
    obj.direccion = 'Av 2'
    obj.correo = 'carlos@test.com'
    obj.password = 'nuevo_hash'
    assert obj.cedula_usuario == '87654321'
    assert obj.nombre == 'Carlos'
    assert obj.apellido == 'Lopez'
    assert obj.telefono == '04141112233'
    assert obj.direccion == 'Av 2'
    assert obj.correo == 'carlos@test.com'
    assert obj.password == 'nuevo_hash'


# CS-LOG-15
def test_smoke_login_credenciales_invalidas_no_guarda_sesion(cliente):
    """POST /login con credenciales incorrectas no debe guardar sesión."""
    _set_captcha(cliente, 'SMOKE')
    cliente.post(
        '/login',
        json={'email': 'noeexiste_smoke@automall123.com', 'password': 'Wrongpass1!', 'captcha': 'SMOKE'},
        content_type='application/json'
    )
    with cliente.session_transaction() as sess:
        assert 'cedula_usuario' not in sess


# CS-LOG-16
def test_smoke_recuperar_correo_con_preguntas(cliente, usuario_temporal):
    """POST /recuperar con correo válido y preguntas en BD debe cargar formulario de verificación."""
    respuesta = cliente.post('/recuperar', data={'email': usuario_temporal['correo']})
    assert respuesta.status_code == 200
    with cliente.session_transaction() as sess:
        assert sess.get('recuperar_correo') == usuario_temporal['correo']


# CS-LOG-17
def test_smoke_verificar_respuesta_vacia_redirige(cliente, usuario_temporal):
    """POST /verificar_respuesta con respuestas vacías debe redirigir a /recuperar."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
    respuesta = cliente.post('/verificar_respuesta', data={'respuesta': ['', '']}, follow_redirects=False)
    assert respuesta.status_code == 302


# CS-LOG-18
def test_smoke_verificar_respuesta_correcta_autoriza(cliente, usuario_temporal):
    """POST /verificar_respuesta con respuestas correctas debe autorizar cambio de contraseña."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
        sess['recuperar_cedula'] = usuario_temporal['cedula']
    respuesta = cliente.post('/verificar_respuesta', data={'respuesta': ['respuno', 'respdos']})
    assert respuesta.status_code == 200
    with cliente.session_transaction() as sess:
        assert sess.get('recuperacion_autorizada') is True


# CS-LOG-19
def test_smoke_verificar_respuesta_incorrecta_redirige(cliente, usuario_temporal):
    """POST /verificar_respuesta con respuestas erróneas debe redirigir a /recuperar."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
    respuesta = cliente.post('/verificar_respuesta', data={'respuesta': ['mal1', 'mal2']}, follow_redirects=False)
    assert respuesta.status_code == 302


# CS-LOG-20
def test_smoke_cambiar_password_no_coinciden(cliente, usuario_temporal):
    """POST /cambiar_password con contraseñas distintas debe mostrar error."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
        sess['recuperacion_autorizada'] = True
    respuesta = cliente.post(
        '/cambiar_password',
        data={'nueva_password': 'NuevaPass1!', 'confirmar_password': 'OtraPass2!'}
    )
    assert respuesta.status_code == 200


# CS-LOG-21
def test_smoke_cambiar_password_debil(cliente, usuario_temporal):
    """POST /cambiar_password con contraseña débil debe ser rechazada."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
        sess['recuperacion_autorizada'] = True
    respuesta = cliente.post(
        '/cambiar_password',
        data={'nueva_password': '123', 'confirmar_password': '123'}
    )
    assert respuesta.status_code == 200


# CS-LOG-22
def test_smoke_cambiar_password_exitoso(cliente, usuario_temporal):
    """POST /cambiar_password válido debe actualizar contraseña y redirigir a /login."""
    with cliente.session_transaction() as sess:
        sess['recuperar_correo'] = usuario_temporal['correo']
        sess['recuperacion_autorizada'] = True
    respuesta = cliente.post(
        '/cambiar_password',
        data={'nueva_password': 'SmokeNewPass1!', 'confirmar_password': 'SmokeNewPass1!'},
        follow_redirects=False
    )
    assert respuesta.status_code == 302
    assert '/login' in respuesta.headers.get('Location', '')
