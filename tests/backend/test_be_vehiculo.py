import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca
from models.modelo import Modelo
from models.vehiculo import Vehiculo

CEDULA_PROP_BE = 99887703


def _limpiar_vehiculos_be():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT cod_documento, cod_accesorio FROM vehiculo WHERE placa LIKE 'BEVH%'")
    rel = cur.fetchall()
    docs = [r["cod_documento"] for r in rel if r.get("cod_documento")]
    accs = [r["cod_accesorio"] for r in rel if r.get("cod_accesorio")]

    cur.execute("DELETE FROM imagen WHERE placa LIKE 'BEVH%'")
    cur.execute("DELETE FROM catalogo WHERE placa LIKE 'BEVH%'")
    cur.execute("DELETE FROM historia_estado_vehiculo WHERE placa LIKE 'BEVH%'")
    cur.execute("DELETE FROM vehiculo WHERE placa LIKE 'BEVH%'")

    if docs:
        cur.execute(f"DELETE FROM documentacion WHERE cod_documento IN ({','.join(['%s']*len(docs))})", tuple(docs))
    if accs:
        cur.execute(f"DELETE FROM accesorio WHERE cod_accesorio IN ({','.join(['%s']*len(accs))})", tuple(accs))

    cur.execute("DELETE FROM modelo WHERE nombre_modelo LIKE 'BE_MOD_VEH_%'")
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'BE_MARCA_VEH_%'")
    cur.execute("DELETE FROM propietario WHERE cedula_propietario = %s", (CEDULA_PROP_BE,))
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
    _limpiar_vehiculos_be()
    yield
    _limpiar_vehiculos_be()


def _crear_dependencias_be(cedula):
    n_marca = f"BE_MARCA_VEH_{uuid.uuid4().hex[:6].upper()}"
    Marca.guardar(n_marca, "Activo", cedula)
    marca = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == n_marca)

    n_modelo = f"BE_MOD_VEH_{uuid.uuid4().hex[:6].upper()}"
    Modelo.guardar(n_modelo, "Activo", marca["cod_marca"], cedula)
    modelo = next(m for m in Modelo.obtener_por_marca(marca["cod_marca"]) if m["nombre_modelo"] == n_modelo)

    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """INSERT INTO propietario (cedula_propietario, razon_social, telefono, correo, direccion, tipo, estado, fecha_registro)
           VALUES (%s, 'Propietario Backend Test', '04140000000', 'be@test.com', 'Lara', 'Natural', 'Activo', CURDATE())""",
        (CEDULA_PROP_BE,)
    )
    conn.commit()
    cur.execute("SELECT cod_tipo FROM tipo_vehiculo ORDER BY cod_tipo ASC LIMIT 1")
    row = cur.fetchone()
    cod_tipo = row["cod_tipo"] if row else 1
    cur.close()
    conn.close()
    return modelo["cod_modelo"], cod_tipo


def _form_be(placa, cod_modelo, cod_tipo):
    return {
        "placa": placa, "color": "Rojo", "anio": "2024", "kilometraje": "1000",
        "tipo": str(cod_tipo), "estado": "Disponible", "modelo": str(cod_modelo),
        "cedula": str(CEDULA_PROP_BE), "precio": "22000",
        "descripcion_catalogo": "Prueba backend", "fecha_ingreso": "2026-11-20",
        "otro_documento": ""
    }


def test_be_veh_01_contrato_json_registro_y_edicion(client_be, usuario_autorizado_be):
    """CP-BE-VEH-01: Validar contrato JSON (200, status y message) en registro y edición de vehículo."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    cod_modelo, cod_tipo = _crear_dependencias_be(cedula)
    placa = f"BEVH{uuid.uuid4().hex[:6].upper()}"

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        form = _form_be(placa, cod_modelo, cod_tipo)
        resp1 = client_be.post("/vehiculos-registrar", data=form)
        d1 = resp1.get_json()
        assert resp1.status_code == 200
        assert resp1.is_json is True
        assert {"status", "message"}.issubset(d1.keys())
        assert d1["status"] == "success"

        form["precio"] = "23000"
        resp2 = client_be.post(f"/vehiculos-editar/{placa}", data=form)
        d2 = resp2.get_json()
        assert resp2.status_code == 200
        assert resp2.is_json is True
        assert d2["status"] == "success"
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=2)
        _limpiar_ultima_bitacora(cedula, cod_accion=3, cod_modulo=2)


def test_be_veh_02_manejo_tipos_no_numericos_anio_y_precio(client_be, usuario_autorizado_be):
    """CP-BE-VEH-02: Enviar texto no numérico en año y precio retorna HTTP 400 JSON controlado (no 500)."""
    cedula = usuario_autorizado_be["cedula_usuario"]
    cod_modelo, cod_tipo = _crear_dependencias_be(cedula)
    placa = f"BEVH{uuid.uuid4().hex[:6].upper()}"

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        form_mal = _form_be(placa, cod_modelo, cod_tipo)
        form_mal["anio"] = "dos_mil"
        form_mal["precio"] = "caro"

        resp = client_be.post("/vehiculos-registrar", data=form_mal)
        datos = resp.get_json()

        assert resp.status_code == 400
        assert resp.is_json is True
        assert datos["status"] == "error"
        assert Vehiculo.obtener_por_placa(placa) is None
    finally:
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultima_bitacora(cedula, cod_accion=1, cod_modulo=7)


def test_be_veh_03_manejo_payload_incompleto_sin_error_500(client_be, usuario_autorizado_be):
    """CP-BE-VEH-03: Petición POST vacía en /vehiculos-registrar retorna HTTP 400 JSON controlado."""
    with client_be.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_be["cod_rol"]
        sess["cedula_usuario"] = usuario_autorizado_be["cedula_usuario"]

    resp = client_be.post("/vehiculos-registrar", data={})
    datos = resp.get_json()

    assert resp.status_code == 400
    assert resp.is_json is True
    assert datos["status"] == "error"


def test_be_veh_04_metodo_405_y_seguridad_directa(client_be):
    """CP-BE-VEH-04: Método GET en ruta POST-only retorna 405; POST sin sesión/permisos redirige 302."""
    assert client_be.get("/vehiculos-eliminar/ABC123").status_code == 405

    resp_sin_sesion = client_be.post("/vehiculos-registrar", data={})
    assert resp_sin_sesion.status_code == 302
    assert "/login" in resp_sin_sesion.location

    with client_be.session_transaction() as sess:
        sess["cod_rol"] = 99999
        sess["cedula_usuario"] = "00000000"

    resp_sin_permiso = client_be.post("/vehiculos-eliminar/ABC123")
    assert resp_sin_permiso.status_code == 302
    assert resp_sin_permiso.location.endswith("/")


def test_be_veh_05_proteccion_sql_injection_en_consultas_placa(app_backend):
    """CP-BE-VEH-05: Consultas de backend por placa neutralizan intentos de inyección SQL (' OR '1'='1)."""
    payload_sqli = "' OR '1'='1"
    assert Vehiculo.buscar_por_placa(payload_sqli) is None
    assert Vehiculo.obtener_por_placa(payload_sqli) is None