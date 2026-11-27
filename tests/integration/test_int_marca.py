import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca
from utils.notificaciones_manager import NotificacionManager


def _nombre_unico(prefijo="INT_MARCA"):
    return f"{prefijo}_{uuid.uuid4().hex[:8].upper()}"


def _contar_bitacora(cedula, cod_accion, cod_modulo=6):
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = %s AND cod_modulo = %s",
        (cedula, cod_accion, cod_modulo)
    )
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


def _limpiar_ultimo_registro_bitacora(cedula, cod_accion, cod_modulo=6):
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = %s AND cod_modulo = %s ORDER BY fecha DESC LIMIT 1",
        (cedula, cod_accion, cod_modulo)
    )
    conn.commit()
    cur.close()
    conn.close()


def _limpiar_marcas_prueba(patron="INT_MARCA_%"):
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE %s", (patron,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_bd_marcas():
    """Garantiza limpieza en automall.marca antes y después de cada test de integración."""
    _limpiar_marcas_prueba()
    yield
    _limpiar_marcas_prueba()


# ==============================================================================
#   PRUEBAS DE INTEGRACIÓN DEL MÓDULO MARCA
# ==============================================================================

def test_cp_int_mar_01_flujo_crear_marca_bd_bitacora_y_notificacion(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MAR-01: Integración completa POST /marcas/registro -> Permisos (seguridad) ->
    Marca.guardar (automall) -> Bitacora.registrar (seguridad) -> NotificacionManager (JSON).
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    nombre = _nombre_unico()
    bitacora_antes = _contar_bitacora(cedula, cod_accion=1, cod_modulo=6)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(
            "/marcas/registro",
            data={"nombre_marca": f"  {nombre}  ", "estado": "Activo"}
        )
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"
        assert datos["nombre_marca"] == nombre
        assert datos["cod_marca"] is not None

        # 1. Verificar persistencia real en BD automall.marca
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM marca WHERE cod_marca = %s", (datos["cod_marca"],))
        fila_bd = cur.fetchone()
        cur.close()
        conn.close()

        assert fila_bd is not None
        assert fila_bd["nombre_marca"] == nombre
        assert fila_bd["estado"] == "Activo"

        # 2. Verificar registro real en BD seguridad.t_bitacora
        bitacora_despues = _contar_bitacora(cedula, cod_accion=1, cod_modulo=6)
        assert bitacora_despues == bitacora_antes + 1

        # 3. Verificar escritura real en data/notificaciones.json
        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Nueva Marca Registrada" and nombre in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)


def test_cp_int_mar_02_consulta_get_marcas_y_renderizado_plantilla_real(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MAR-02: Integración GET /marcas/registro -> Permisos -> Marca.obtener_todas() ->
    Renderizado real de templates/vehiculos/marca_registro.html.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    nombre = _nombre_unico()

    Marca.guardar(nombre, "Activo", cedula)
    try:
        with client_real.session_transaction() as sess:
            sess["cod_rol"] = cod_rol
            sess["cedula_usuario"] = cedula

        respuesta = client_real.get("/marcas/registro")
        html = respuesta.data.decode("utf-8")

        assert respuesta.status_code == 200
        assert nombre in html
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)


def test_cp_int_mar_03_flujo_editar_marca_bd_y_bitacora(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MAR-03: Integración POST /marcas/editar/<id> -> actualización real en automall.marca ->
    registro en seguridad.t_bitacora (cod_accion=3) -> notificación JSON.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    nombre_inicial = _nombre_unico()
    nombre_nuevo = _nombre_unico("INT_MARCA_EDIT")

    Marca.guardar(nombre_inicial, "Activo", cedula)
    creada = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre_inicial)
    cod_marca = creada["cod_marca"]
    bitacora_antes = _contar_bitacora(cedula, cod_accion=3, cod_modulo=6)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(
            f"/marcas/editar/{cod_marca}",
            data={"nombre_marca": nombre_nuevo, "estado": "Activo"}
        )
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        # Verificar cambio real en BD
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM marca WHERE cod_marca = %s", (cod_marca,))
        fila_bd = cur.fetchone()
        cur.close()
        conn.close()

        assert fila_bd["nombre_marca"] == nombre_nuevo
        assert _contar_bitacora(cedula, cod_accion=3, cod_modulo=6) == bitacora_antes + 1

        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Marca Actualizada" and nombre_nuevo in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=3, cod_modulo=6)


def test_cp_int_mar_04_flujo_eliminar_logico_excluye_consultas(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MAR-04: Integración POST /marcas/eliminar/<id> -> estado='Inactivo' en MySQL ->
    exclusión en obtener_todas/obtener_activas -> registro en bitácora (cod_accion=4).
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    nombre = _nombre_unico()

    Marca.guardar(nombre, "Activo", cedula)
    creada = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre)
    cod_marca = creada["cod_marca"]
    bitacora_antes = _contar_bitacora(cedula, cod_accion=4, cod_modulo=6)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(f"/marcas/eliminar/{cod_marca}")
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        # Verificar en BD que el registro sigue existiendo pero en estado 'Inactivo'
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT estado FROM marca WHERE cod_marca = %s", (cod_marca,))
        fila_bd = cur.fetchone()
        cur.close()
        conn.close()

        assert fila_bd["estado"] == "Inactivo"
        assert all(m["cod_marca"] != cod_marca for m in Marca.obtener_todas())
        assert all(m["cod_marca"] != cod_marca for m in Marca.obtener_activas())
        assert _contar_bitacora(cedula, cod_accion=4, cod_modulo=6) == bitacora_antes + 1
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=4, cod_modulo=6)


def test_cp_int_mar_05_permiso_denegado_contra_bd_seguridad(client_real):
    """
    CP-INT-MAR-05: Integración middleware @requiere_permiso con BD 'seguridad' real ->
    rol sin permisos (99999) es bloqueado con HTTP 302 y no inserta en 'automall.marca'.
    """
    nombre = _nombre_unico()

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = 99999
        sess["cedula_usuario"] = "00000000"

    respuesta = client_real.post(
        "/marcas/registro",
        data={"nombre_marca": nombre, "estado": "Activo"}
    )

    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/")
    assert all(m["nombre_marca"] != nombre for m in Marca.obtener_todas())


def test_cp_int_mar_06_validacion_backend_no_persiste_en_bd(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MAR-06: Integración controlador + modelo ante entrada inválida ('A') ->
    retorna HTTP 400 y garantiza 0 inserciones en 'automall.marca'.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    respuesta = client_real.post(
        "/marcas/registro",
        data={"nombre_marca": "A", "estado": "Activo"}
    )
    datos = respuesta.get_json()

    assert respuesta.status_code == 400
    assert datos["status"] == "error"
    assert all(m["nombre_marca"] != "A" for m in Marca.obtener_todas())