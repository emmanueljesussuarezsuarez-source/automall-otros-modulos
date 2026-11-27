import uuid
import pytest
from models.db import ConexionBD


def _limpiar_marcas_be():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'BE_MARCA_%'")
    conn.commit()
    cur.close()
    conn.close()


def _limpiar_ultima_bitacora(cedula, cod_accion, cod_modulo=6):
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
    _limpiar_marcas_be()
    yield
    _limpiar_marcas_be()


def test_be_mar_01_contrato_json_y_status_http_registro(client_be, usuario_autorizado_be):
    """CP-BE-MAR-01: Validar contrato JSON exacto (cabeceras, claves y tipos) en POST /marcas/registro."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    nombre = f"BE_MARCA_{uuid.uuid4().hex[:6].upper()}"

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        resp = client_be.post("/marcas/registro", data={"nombre_marca": nombre, "estado": "Activo"})
        datos = resp.get_json()

        assert resp.status_code == 200
        assert resp.is_json is True
        assert "application/json" in resp.content_type
        assert {"status", "message", "cod_marca", "nombre_marca"}.issubset(datos.keys())
        assert datos["status"] == "success"
        assert isinstance(datos["cod_marca"], int)
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)


def test_be_mar_02_manejo_payload_incompleto_sin_error_500(client_be, usuario_autorizado_be):
    """CP-BE-MAR-02: Petición POST sin campos obligatorios retorna HTTP 400 JSON controlado (no 500)."""
    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = usuario_autorizado_be["cedula_usuario"]

    resp = client_be.post("/marcas/registro", data={})
    datos = resp.get_json()

    assert resp.status_code == 400
    assert resp.is_json is True
    assert datos["status"] == "error"


def test_be_mar_03_metodo_http_no_permitido_405(client_be):
    """CP-BE-MAR-03: Peticiones GET a endpoints exclusivos POST retornan HTTP 405 Method Not Allowed."""
    assert client_be.get("/marcas/editar/1").status_code == 405
    assert client_be.get("/marcas/eliminar/1").status_code == 405


def test_be_mar_04_seguridad_direct_post_sin_sesion_y_sin_permisos(client_be):
    """CP-BE-MAR-04: Bloqueo en backend ante POST directo sin sesión (302 login) o rol inválido (302 inicio)."""
    resp_sin_sesion = client_be.post("/marcas/editar/1", data={"nombre_marca": "Test", "estado": "Activo"})
    assert resp_sin_sesion.status_code == 302
    assert "/login" in resp_sin_sesion.location

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = 99999
        sess["cedula_usuario"] = "00000000"

    resp_sin_permiso = client_be.post("/marcas/eliminar/1")
    assert resp_sin_permiso.status_code == 302
    assert resp_sin_permiso.location.endswith("/")


def test_be_mar_05_proteccion_sql_injection_parametrizada(client_be, usuario_autorizado_be):
    """CP-BE-MAR-05: Inyección SQL en nombre_marca no altera la estructura ni otros registros de BD."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    payload_sqli = "BE_MARCA_' OR '1'='1"

    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM marca")
    total_antes = cur.fetchone()[0]
    cur.close()
    conn.close()

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        resp = client_be.post("/marcas/registro", data={"nombre_marca": payload_sqli, "estado": "Activo"})
        assert resp.status_code == 200

        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM marca")
        total_despues = cur.fetchone()[0]
        cur.close()
        conn.close()

        # Solo se insertó 1 fila literal; no hubo borrado ni alteración masiva
        assert total_despues == total_antes + 1
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)