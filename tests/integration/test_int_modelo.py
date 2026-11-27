import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca
from models.modelo import Modelo
from utils.notificaciones_manager import NotificacionManager


def _nombre_unico(prefijo):
    return f"{prefijo}_{uuid.uuid4().hex[:8].upper()}"


def _contar_bitacora(cedula, cod_accion, cod_modulo=7):
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


def _limpiar_ultimo_registro_bitacora(cedula, cod_accion, cod_modulo):
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = %s AND cod_modulo = %s ORDER BY fecha DESC LIMIT 1",
        (cedula, cod_accion, cod_modulo)
    )
    conn.commit()
    cur.close()
    conn.close()


def _limpiar_datos_modelo_y_marca():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor()
    # Primero se eliminan los modelos hijos y luego las marcas padre
    cur.execute("DELETE FROM modelo WHERE nombre_modelo LIKE 'INT_MOD_%'")
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'INT_MARCA_%'")
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_bd_modelos():
    """Limpia los registros temporales de modelo y marca antes y después de cada test."""
    _limpiar_datos_modelo_y_marca()
    yield
    _limpiar_datos_modelo_y_marca()


def _crear_marca_real(cedula):
    nombre_marca = _nombre_unico("INT_MARCA")
    Marca.guardar(nombre_marca, "Activo", cedula)
    marca = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre_marca)
    return marca


# ==============================================================================
#   PRUEBAS DE INTEGRACIÓN DEL MÓDULO MODELO
# ==============================================================================

def test_cp_int_mod_01_flujo_crear_modelo_con_marca_real_bitacora_y_notif(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-01: Integración POST /modelos/registro -> Permisos -> Modelo.guardar (enlazado a Marca real) ->
    Bitacora (cod_modulo=7) -> NotificacionManager JSON.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    marca = _crear_marca_real(cedula)
    nombre_modelo = _nombre_unico("INT_MOD")
    bitacora_antes = _contar_bitacora(cedula, cod_accion=1, cod_modulo=7)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(
            "/modelos/registro",
            data={
                "nombre_modelo": f"  {nombre_modelo}  ",
                "estado": "Activo",
                "cod_marca": str(marca["cod_marca"])
            }
        )
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"
        assert datos["nombre_modelo"] == nombre_modelo
        assert datos["cod_modelo"] is not None

        # Verificar en BD real automall.modelo
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modelo WHERE cod_modelo = %s", (datos["cod_modelo"],))
        fila_bd = cur.fetchone()
        cur.close()
        conn.close()

        assert fila_bd is not None
        assert fila_bd["nombre_modelo"] == nombre_modelo
        assert fila_bd["cod_marca"] == marca["cod_marca"]
        assert _contar_bitacora(cedula, cod_accion=1, cod_modulo=7) == bitacora_antes + 1

        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Nuevo Modelo Registrado" and nombre_modelo in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)


def test_cp_int_mod_02_consulta_get_modelos_join_marca_y_renderizado_real(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-02: Integración GET /modelos/registro -> Modelo.obtener_todas() (INNER JOIN marca) +
    Marca.obtener_activas() -> Renderizado real de templates/vehiculos/modelo_registro.html.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    marca = _crear_marca_real(cedula)
    nombre_modelo = _nombre_unico("INT_MOD")
    Modelo.guardar(nombre_modelo, "Activo", marca["cod_marca"], cedula)

    try:
        with client_real.session_transaction() as sess:
            sess["cod_rol"] = cod_rol
            sess["cedula_usuario"] = cedula

        respuesta = client_real.get("/modelos/registro")
        html = respuesta.data.decode("utf-8")

        assert respuesta.status_code == 200
        assert nombre_modelo in html
        assert marca["nombre_marca"] in html
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)


def test_cp_int_mod_03_flujo_editar_modelo_y_reasignar_marca_real(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-03: Integración POST /modelos/editar/<id> -> actualización de nombre y reasignación de
    cod_marca en BD real -> Bitácora (cod_accion=3) -> Notificación JSON.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    marca_1 = _crear_marca_real(cedula)
    marca_2 = _crear_marca_real(cedula)
    nombre_inicial = _nombre_unico("INT_MOD")
    nombre_nuevo = _nombre_unico("INT_MOD_EDIT")

    Modelo.guardar(nombre_inicial, "Activo", marca_1["cod_marca"], cedula)
    creado = next(m for m in Modelo.obtener_todas() if m["nombre_modelo"] == nombre_inicial)
    cod_modelo = creado["cod_modelo"]
    bitacora_antes = _contar_bitacora(cedula, cod_accion=3, cod_modulo=7)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(
            f"/modelos/editar/{cod_modelo}",
            data={
                "nombre_modelo": nombre_nuevo,
                "estado": "Activo",
                "cod_marca": str(marca_2["cod_marca"])
            }
        )
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        # Verificar en BD que cambió tanto nombre_modelo como cod_marca
        modelos_m2 = Modelo.obtener_por_marca(marca_2["cod_marca"])
        assert any(m["cod_modelo"] == cod_modelo and m["nombre_modelo"] == nombre_nuevo for m in modelos_m2)
        assert _contar_bitacora(cedula, cod_accion=3, cod_modulo=7) == bitacora_antes + 1

        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Modelo Actualizado" and nombre_nuevo in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=3, cod_modulo=7)


def test_cp_int_mod_04_flujo_eliminar_logico_excluye_consultas(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-04: Integración POST /modelos/eliminar/<id> -> estado='Inactivo' en MySQL ->
    exclusión en obtener_todas y obtener_por_marca -> Bitácora (cod_accion=4).
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    marca = _crear_marca_real(cedula)
    nombre_modelo = _nombre_unico("INT_MOD")

    Modelo.guardar(nombre_modelo, "Activo", marca["cod_marca"], cedula)
    creado = next(m for m in Modelo.obtener_todas() if m["nombre_modelo"] == nombre_modelo)
    cod_modelo = creado["cod_modelo"]
    bitacora_antes = _contar_bitacora(cedula, cod_accion=4, cod_modulo=7)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(f"/modelos/eliminar/{cod_modelo}")
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT estado FROM modelo WHERE cod_modelo = %s", (cod_modelo,))
        fila_bd = cur.fetchone()
        cur.close()
        conn.close()

        assert fila_bd["estado"] == "Inactivo"
        assert all(m["cod_modelo"] != cod_modelo for m in Modelo.obtener_todas())
        assert all(m["cod_modelo"] != cod_modelo for m in Modelo.obtener_por_marca(marca["cod_marca"]))
        assert _contar_bitacora(cedula, cod_accion=4, cod_modulo=7) == bitacora_antes + 1
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=4, cod_modulo=7)


def test_cp_int_mod_05_obtener_por_marca_filtra_solo_activos_en_bd(usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-05: Integración Modelo–Marca en BD real -> obtener_por_marca retorna únicamente
    los modelos 'Activo' de esa marca, excluyendo los 'Inactivo'.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    marca = _crear_marca_real(cedula)
    mod_activo = _nombre_unico("INT_MOD_ACT")
    mod_inactivo = _nombre_unico("INT_MOD_INA")

    try:
        Modelo.guardar(mod_activo, "Activo", marca["cod_marca"], cedula)
        Modelo.guardar(mod_inactivo, "Inactivo", marca["cod_marca"], cedula)

        resultados = Modelo.obtener_por_marca(marca["cod_marca"])
        nombres = [m["nombre_modelo"] for m in resultados]

        assert mod_activo in nombres
        assert mod_inactivo not in nombres
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)


def test_cp_int_mod_06_bloqueo_permiso_y_validacion_no_persisten_en_bd(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-MOD-06: Integración seguridad y validación -> rol no autorizado (99999) redirige 302 y
    datos inválidos (cod_marca='0') retornan HTTP 400 sin insertar en automall.modelo.
    """
    nombre_bloqueado = _nombre_unico("INT_MOD_BLK")

    # 1. Rol sin permisos contra BD seguridad real
    with client_real.session_transaction() as sess:
        sess["cod_rol"] = 99999
        sess["cedula_usuario"] = "00000000"

    resp_denegada = client_real.post(
        "/modelos/registro",
        data={"nombre_modelo": nombre_bloqueado, "estado": "Activo", "cod_marca": "1"}
    )
    assert resp_denegada.status_code == 302
    assert resp_denegada.location.endswith("/")

    # 2. Usuario autorizado pero con cod_marca inválido
    with client_real.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_vehiculos["cod_rol"]
        sess["cedula_usuario"] = usuario_autorizado_vehiculos["cedula_usuario"]

    resp_invalida = client_real.post(
        "/modelos/registro",
        data={"nombre_modelo": nombre_bloqueado, "estado": "Activo", "cod_marca": "0"}
    )
    assert resp_invalida.status_code == 400
    assert resp_invalida.get_json()["status"] == "error"
    assert all(m["nombre_modelo"] != nombre_bloqueado for m in Modelo.obtener_todas())