import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca
from models.modelo import Modelo
from models.vehiculo import Vehiculo
from utils.notificaciones_manager import NotificacionManager

CEDULA_PROP_TEST = 99887701


def _placa_unica():
    return f"INTV{uuid.uuid4().hex[:6].upper()}"


def _nombre_unico(prefijo):
    return f"{prefijo}_{uuid.uuid4().hex[:8].upper()}"


def _contar_bitacora(cedula, cod_accion, cod_modulo=2):
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


def _limpiar_datos_vehiculos_prueba():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)

    # Obtener IDs de documentacion y accesorio vinculados a placas de prueba antes de borrar vehiculo
    cur.execute("SELECT cod_documento, cod_accesorio FROM vehiculo WHERE placa LIKE 'INTV%'")
    relacionados = cur.fetchall()
    docs_ids = [r["cod_documento"] for r in relacionados if r.get("cod_documento")]
    accs_ids = [r["cod_accesorio"] for r in relacionados if r.get("cod_accesorio")]

    # Limpieza ordenada de hijas a padres
    cur.execute("DELETE FROM imagen WHERE placa LIKE 'INTV%'")
    cur.execute("DELETE FROM catalogo WHERE placa LIKE 'INTV%'")
    cur.execute("DELETE FROM historia_estado_vehiculo WHERE placa LIKE 'INTV%'")
    cur.execute("DELETE FROM vehiculo WHERE placa LIKE 'INTV%'")

    if docs_ids:
        placeholders = ",".join(["%s"] * len(docs_ids))
        cur.execute(f"DELETE FROM documentacion WHERE cod_documento IN ({placeholders})", tuple(docs_ids))
    if accs_ids:
        placeholders = ",".join(["%s"] * len(accs_ids))
        cur.execute(f"DELETE FROM accesorio WHERE cod_accesorio IN ({placeholders})", tuple(accs_ids))

    cur.execute("DELETE FROM modelo WHERE nombre_modelo LIKE 'INT_MOD_VEH_%'")
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'INT_MARCA_VEH_%'")
    cur.execute("DELETE FROM propietario WHERE cedula_propietario = %s", (CEDULA_PROP_TEST,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_bd_vehiculos():
    """Garantiza limpieza ordenada de todas las tablas relacionadas antes y después de cada test."""
    _limpiar_datos_vehiculos_prueba()
    yield
    _limpiar_datos_vehiculos_prueba()


def _preparar_dependencias_reales(cedula_usuario):
    """Crea marca, modelo, propietario reales en BD y obtiene un tipo_vehiculo existente."""
    nombre_marca = _nombre_unico("INT_MARCA_VEH")
    Marca.guardar(nombre_marca, "Activo", cedula_usuario)
    marca = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre_marca)

    nombre_modelo = _nombre_unico("INT_MOD_VEH")
    Modelo.guardar(nombre_modelo, "Activo", marca["cod_marca"], cedula_usuario)
    modelo = next(m for m in Modelo.obtener_por_marca(marca["cod_marca"]) if m["nombre_modelo"] == nombre_modelo)

    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """INSERT INTO propietario (cedula_propietario, razon_social, telefono, correo, direccion, tipo, estado, fecha_registro)
           VALUES (%s, %s, %s, %s, %s, %s, 'Activo', CURDATE())""",
        (CEDULA_PROP_TEST, "Propietario Prueba Integracion", "04141234567", "prop@test.com", "Barquisimeto", "Natural")
    )
    conn.commit()

    cur.execute("SELECT cod_tipo FROM tipo_vehiculo ORDER BY cod_tipo ASC LIMIT 1")
    tipo_row = cur.fetchone()
    cod_tipo = tipo_row["cod_tipo"] if tipo_row else 1
    cur.close()
    conn.close()

    return marca, modelo, cod_tipo


def _form_vehiculo_valido(placa, cod_modelo, cod_tipo, estado="Disponible", precio="19500"):
    return {
        "placa": placa,
        "color": "Gris",
        "anio": "2024",
        "kilometraje": "12000",
        "tipo": str(cod_tipo),
        "estado": estado,
        "modelo": str(cod_modelo),
        "cedula": str(CEDULA_PROP_TEST),
        "precio": precio,
        "descripcion_catalogo": "Vehiculo de prueba de integracion",
        "fecha_ingreso": "2026-11-20",
        "otro_documento": "Ninguno",
        "original_totalPropiedad": "on",
        "carnet_circulacion": "on",
        "copia_llaves": "on",
        "repuesto": "on",
    }


# ==============================================================================
#   PRUEBAS DE INTEGRACIÓN DEL MÓDULO VEHÍCULO
# ==============================================================================

def test_cp_int_veh_01_flujo_registrar_vehiculo_multitabla_bitacora_y_notif(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-01: Integración POST /vehiculos-registrar -> Permisos -> Inserción real en 5 tablas
    (documentacion, accesorio, vehiculo, historia_estado_vehiculo, catalogo) -> Bitacora -> Notificación.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    _, modelo, cod_tipo = _preparar_dependencias_reales(cedula)
    placa = _placa_unica()
    bitacora_antes = _contar_bitacora(cedula, cod_accion=1, cod_modulo=2)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        respuesta = client_real.post(
            "/vehiculos-registrar",
            data=_form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo)
        )
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        # Verificar persistencia real en las tablas involucradas
        vehiculo_bd = Vehiculo.obtener_por_placa(placa)
        assert vehiculo_bd is not None
        assert vehiculo_bd["color"] == "Gris"
        assert float(vehiculo_bd["precio"]) == 19500.0
        assert vehiculo_bd["original_totalPropiedad"] == 1
        assert vehiculo_bd["copia_llaves"] == 1

        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM historia_estado_vehiculo WHERE placa = %s", (placa,))
        hist = cur.fetchall()
        cur.close()
        conn.close()
        assert len(hist) == 1
        assert hist[0]["estado"] == "Disponible"

        assert _contar_bitacora(cedula, cod_accion=1, cod_modulo=2) == bitacora_antes + 1

        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Nuevo Vehículo Registrado" and placa in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_veh_02_consulta_lista_y_busqueda_integrada_cinco_tablas(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-02: Integración GET /vehiculos-lista (renderizado real) y Vehiculo.buscar_por_placa
    (JOIN de vehiculo, catalogo, modelo, marca y tipo_vehiculo en MySQL).
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    marca, modelo, cod_tipo = _preparar_dependencias_reales(cedula)
    placa = _placa_unica()

    v_data = {
        "placa": placa, "color": "Azul", "anio": 2024, "kilometraje": 5000,
        "cod_tipo": cod_tipo, "estado": "Disponible", "modelo": modelo["cod_modelo"],
        "cedula": CEDULA_PROP_TEST
    }
    d_data = {
        f: 0 for f in [
            "original_totalPropiedad", "experticia_transito", "certificado_origen",
            "carnet_circulacion", "reserva_dominio", "garantia_vehiculo",
            "certificado_garantia", "manual_vehiculoGarantia", "finiquito",
            "resguardo", "seguro", "factura_compra"
        ]
    }
    d_data["fecha_ingreso"] = "2026-11-20"
    d_data["otro_documento"] = ""
    a_data = {"copia_llaves": 1, "repuesto": 0, "triangulo": 1}
    c_data = {"estado": "Activo", "precio": 24000.0, "descripcion": "Impecable"}

    Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], cedula)

    try:
        with client_real.session_transaction() as sess:
            sess["cod_rol"] = cod_rol
            sess["cedula_usuario"] = cedula

        # 1. Vista HTML real /vehiculos-lista
        resp = client_real.get("/vehiculos-lista")
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert placa in html
        assert marca["nombre_marca"] in html
        assert modelo["nombre_modelo"] in html

        # 2. Búsqueda integrada 5 tablas
        res_busqueda = Vehiculo.buscar_por_placa(placa.lower())
        assert res_busqueda is not None
        assert res_busqueda["exito"] is True
        assert res_busqueda["vehiculo"]["marca"] == marca["nombre_marca"]
        assert res_busqueda["vehiculo"]["modelo"] == modelo["nombre_modelo"]
        assert res_busqueda["vehiculo"]["precio"] == 24000.0
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_veh_03_flujo_editar_vehiculo_y_cambio_estado_historial_notif(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-03: Integración POST /vehiculos-editar/<placa> -> actualización en vehiculo,
    documentacion, accesorio y catalogo -> nuevo registro en historial -> Bitácora -> Notificación.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    _, modelo, cod_tipo = _preparar_dependencias_reales(cedula)
    placa = _placa_unica()

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        client_real.post("/vehiculos-registrar", data=_form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo))
        bitacora_antes = _contar_bitacora(cedula, cod_accion=3, cod_modulo=2)

        form_edit = _form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo, estado="Reservado", precio="21000")
        form_edit["color"] = "Negro"

        respuesta = client_real.post(f"/vehiculos-editar/{placa}", data=form_edit)
        datos = respuesta.get_json()

        assert respuesta.status_code == 200
        assert datos["status"] == "success"

        veh_actualizado = Vehiculo.obtener_por_placa(placa)
        assert veh_actualizado["estado"] == "Reservado"
        assert veh_actualizado["color"] == "Negro"
        assert float(veh_actualizado["precio"]) == 21000.0

        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT estado FROM historia_estado_vehiculo WHERE placa = %s ORDER BY cod_historia ASC", (placa,))
        estados_hist = [r["estado"] for r in cur.fetchall()]
        cur.close()
        conn.close()
        assert estados_hist == ["Disponible", "Reservado"]
        assert _contar_bitacora(cedula, cod_accion=3, cod_modulo=2) == bitacora_antes + 1

        notifs = NotificacionManager._cargar_todas()
        assert any(
            n.get("titulo") == "Cambio de Estado de Vehículo" and placa in n.get("mensaje", "")
            for n in notifs
        )
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=3, cod_modulo=2)


def test_cp_int_veh_04_flujo_eliminar_logico_y_consulta_historial_sp(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-04: Integración POST /vehiculos-eliminar/<placa> -> estado='Inactivo' -> exclusión de
    consultas activas -> GET /vehiculos-historial (Procedimiento sp_obtener_historial_vehiculos).
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    _, modelo, cod_tipo = _preparar_dependencias_reales(cedula)
    placa = _placa_unica()

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        client_real.post("/vehiculos-registrar", data=_form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo))
        bitacora_antes = _contar_bitacora(cedula, cod_accion=4, cod_modulo=2)

        resp_del = client_real.post(f"/vehiculos-eliminar/{placa}")
        assert resp_del.status_code == 302
        assert "/vehiculos-lista" in resp_del.location

        assert Vehiculo.obtener_por_placa(placa) is None
        assert all(v["placa"] != placa for v in Vehiculo.obtener_todos())
        assert _contar_bitacora(cedula, cod_accion=4, cod_modulo=2) == bitacora_antes + 1

        # Verificar integración con el procedimiento almacenado sp_obtener_historial_vehiculos
        resp_hist = client_real.get("/vehiculos-historial")
        assert resp_hist.status_code == 200
        assert placa in resp_hist.data.decode("utf-8")
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=4, cod_modulo=2)


def test_cp_int_veh_05_placa_duplicada_ejecuta_rollback_sin_huerfanos(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-05: Integración transaccional ante placa duplicada (Error MySQL 1062) ->
    verifica rollback atómico sin dejar registros huérfanos en documentacion ni accesorio.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    cod_rol = usuario_autorizado_vehiculos["cod_rol"]
    _, modelo, cod_tipo = _preparar_dependencias_reales(cedula)
    placa = _placa_unica()

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = cod_rol
        sess["cedula_usuario"] = cedula

    try:
        form = _form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo)
        resp1 = client_real.post("/vehiculos-registrar", data=form)
        assert resp1.status_code == 200

        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documentacion")
        docs_antes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM accesorio")
        acc_antes = cur.fetchone()[0]
        cur.close()
        conn.close()

        # Segundo intento con la misma placa
        resp2 = client_real.post("/vehiculos-registrar", data=form)
        datos2 = resp2.get_json()

        assert resp2.status_code == 400
        assert datos2["status"] == "error"
        assert "ya se encuentra registrada" in datos2["message"]

        # Verificar que rollback impidió huérfanos en documentacion y accesorio
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documentacion")
        docs_despues = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM accesorio")
        acc_despues = cur.fetchone()[0]
        cur.close()
        conn.close()

        assert docs_despues == docs_antes
        assert acc_despues == acc_antes
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_veh_06_permiso_denegado_y_validacion_sin_persistencia(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-VEH-06: Integración de seguridad (rol 99999 bloqueado en BD seguridad) y
    validación de año inválido (1800) sin alterar ninguna tabla en automall.
    """
    placa = _placa_unica()

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = 99999
        sess["cedula_usuario"] = "00000000"

    resp_denegada = client_real.get("/vehiculos-lista")
    assert resp_denegada.status_code == 302
    assert resp_denegada.location.endswith("/")

    # Con usuario válido pero año inválido
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    _, modelo, cod_tipo = _preparar_dependencias_reales(cedula)

    with client_real.session_transaction() as sess:
        sess["cod_rol"] = usuario_autorizado_vehiculos["cod_rol"]
        sess["cedula_usuario"] = cedula

    try:
        form_invalido = _form_vehiculo_valido(placa, modelo["cod_modelo"], cod_tipo)
        form_invalido["anio"] = "1800"

        resp_inv = client_real.post("/vehiculos-registrar", data=form_invalido)
        assert resp_inv.status_code == 400
        assert resp_inv.get_json()["status"] == "error"
        assert Vehiculo.obtener_por_placa(placa) is None
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)