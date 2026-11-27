import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca


def _limpiar_modelos_y_marcas_be():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM modelo WHERE nombre_modelo LIKE 'BE_MOD_%'")
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'BE_MARCA_MOD_%'")
    conn.commit()
    cur.close()
    conn.close()


def _limpiar_ultima_bitacora(cedula, cod_accion, cod_modulo):
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = %s AND cod_modulo = %s ORDER BY fecha DESC LIMIT 1",
        (cedula, cod_accion, cod_modulo)
    )
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_bd():
    _limpiar_modelos_y_marcas_be()
    yield
    _limpiar_modelos_y_marcas_be()


def _crear_marca_be(cedula):
    nombre = f"BE_MARCA_MOD_{uuid.uuid4().hex[:6].upper()}"
    Marca.guardar(nombre, "Activo", cedula)
    return next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre)


def test_be_mod_01_contrato_json_registro_y_edicion(client_be, usuario_autorizado_be):
    """CP-BE-MOD-01: Validar contrato JSON y códigos HTTP 200 en registro y edición de modelos."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    marca = _crear_marca_be(cedula)
    nombre = f"BE_MOD_{uuid.uuid4().hex[:6].upper()}"

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        resp_post = client_be.post(
            "/modelos/registro",
            data={"nombre_modelo": nombre, "estado": "Activo", "cod_marca": str(marca["cod_marca"])}
        )
        datos = resp_post.get_json()

        assert resp_post.status_code == 200
        assert resp_post.is_json is True
        assert {"status", "message", "cod_modelo", "nombre_modelo", "cod_marca"}.issubset(datos.keys())
        assert isinstance(datos["cod_modelo"], int)

        resp_edit = client_be.post(
            f"/modelos/editar/{datos['cod_modelo']}",
            data={"nombre_modelo": f"{nombre}_E", "estado": "Activo", "cod_marca": str(marca["cod_marca"])}
        )
        assert resp_edit.status_code == 200
        assert resp_edit.get_json()["status"] == "success"
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultima_bitacora(cedula, cod_accion=3, cod_modulo=7)


def test_be_mod_02_manejo_tipo_dato_invalido_en_cod_marca(client_be, usuario_autorizado_be):
    """CP-BE-MOD-02: Enviar texto no numérico en cod_marca retorna HTTP 400 JSON controlado (no 500)."""
    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = usuario_autorizado_be["cedula_usuario"]

    resp = client_be.post(
        "/modelos/registro",
        data={"nombre_modelo": "BE_MOD_ERR", "estado": "Activo", "cod_marca": "no_numerico"}
    )
    datos = resp.get_json()

    assert resp.status_code == 400
    assert resp.is_json is True
    assert datos["status"] == "error"


def test_be_mod_03_manejo_payload_incompleto_editar_sin_error_500(client_be, usuario_autorizado_be):
    """CP-BE-MOD-03: Petición POST sin cuerpo en /modelos/editar/1 retorna HTTP 400 JSON controlado."""
    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = usuario_autorizado_be["cedula_usuario"]

    resp = client_be.post("/modelos/editar/1", data={})
    datos = resp.get_json()

    assert resp.status_code == 400
    assert resp.is_json is True
    assert datos["status"] == "error"


def test_be_mod_04_metodo_http_no_permitido_405(client_be):
    """CP-BE-MOD-04: Peticiones GET a endpoints exclusivos POST de modelos retornan HTTP 405."""
    assert client_be.get("/modelos/editar/1").status_code == 405
    assert client_be.get("/modelos/eliminar/1").status_code == 405


def test_be_mod_05_proteccion_sql_injection_parametrizada(client_be, usuario_autorizado_be):
    """CP-BE-MOD-05: Payload de inyección SQL (DROP TABLE) en nombre_modelo es neutralizado por %s."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    marca = _crear_marca_be(cedula)
    payload_sqli = "BE_MOD_'; DROP TABLE marca; --"

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        resp = client_be.post(
            "/modelos/registro",
            data={"nombre_modelo": payload_sqli, "estado": "Activo", "cod_marca": str(marca["cod_marca"])}
        )
        assert resp.status_code == 200
        # Confirmar que la tabla marca sigue existiendo intacta
        assert len(Marca.obtener_todas()) >= 1
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=7)