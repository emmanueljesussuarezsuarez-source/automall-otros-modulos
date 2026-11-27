import uuid
import pytest
from models.db import ConexionBD
from models.marca import Marca
from models.modelo import Modelo
from models.vehiculo import Vehiculo
from models.catalogo import Catalogo

CEDULA_PROP_CAT = 99887702


def _placa_unica():
    return f"INTC{uuid.uuid4().hex[:6].upper()}"


def _nombre_unico(prefijo):
    return f"{prefijo}_{uuid.uuid4().hex[:8].upper()}"


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


def _limpiar_datos_catalogo_prueba():
    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT cod_documento, cod_accesorio FROM vehiculo WHERE placa LIKE 'INTC%'")
    relacionados = cur.fetchall()
    docs_ids = [r["cod_documento"] for r in relacionados if r.get("cod_documento")]
    accs_ids = [r["cod_accesorio"] for r in relacionados if r.get("cod_accesorio")]

    cur.execute("DELETE FROM imagen WHERE placa LIKE 'INTC%'")
    cur.execute("DELETE FROM catalogo WHERE placa LIKE 'INTC%'")
    cur.execute("DELETE FROM historia_estado_vehiculo WHERE placa LIKE 'INTC%'")
    cur.execute("DELETE FROM vehiculo WHERE placa LIKE 'INTC%'")

    if docs_ids:
        placeholders = ",".join(["%s"] * len(docs_ids))
        cur.execute(f"DELETE FROM documentacion WHERE cod_documento IN ({placeholders})", tuple(docs_ids))
    if accs_ids:
        placeholders = ",".join(["%s"] * len(accs_ids))
        cur.execute(f"DELETE FROM accesorio WHERE cod_accesorio IN ({placeholders})", tuple(accs_ids))

    cur.execute("DELETE FROM modelo WHERE nombre_modelo LIKE 'INT_MOD_CAT_%'")
    cur.execute("DELETE FROM marca WHERE nombre_marca LIKE 'INT_MARCA_CAT_%'")
    cur.execute("DELETE FROM propietario WHERE cedula_propietario = %s", (CEDULA_PROP_CAT,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_bd_catalogo():
    """Limpia los datos temporales del catálogo antes y después de cada test."""
    _limpiar_datos_catalogo_prueba()
    yield
    _limpiar_datos_catalogo_prueba()


def _crear_vehiculo_publicado_en_catalogo(cedula_usuario, estado_veh="Disponible", precio=26500.0):
    nombre_marca = _nombre_unico("INT_MARCA_CAT")
    Marca.guardar(nombre_marca, "Activo", cedula_usuario)
    marca = next(m for m in Marca.obtener_todas() if m["nombre_marca"] == nombre_marca)

    nombre_modelo = _nombre_unico("INT_MOD_CAT")
    Modelo.guardar(nombre_modelo, "Activo", marca["cod_marca"], cedula_usuario)
    modelo = next(m for m in Modelo.obtener_por_marca(marca["cod_marca"]) if m["nombre_modelo"] == nombre_modelo)

    conn = ConexionBD.obtener_conexion()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """INSERT INTO propietario (cedula_propietario, razon_social, telefono, correo, direccion, tipo, estado, fecha_registro)
           VALUES (%s, %s, %s, %s, %s, %s, 'Activo', CURDATE())""",
        (CEDULA_PROP_CAT, "Propietario Catalogo Test", "04147654321", "cat@test.com", "Barquisimeto", "Natural")
    )
    conn.commit()
    cur.execute("SELECT cod_tipo FROM tipo_vehiculo ORDER BY cod_tipo ASC LIMIT 1")
    tipo_row = cur.fetchone()
    cod_tipo = tipo_row["cod_tipo"] if tipo_row else 1
    cur.close()
    conn.close()

    placa = _placa_unica()
    v_data = {
        "placa": placa, "color": "Blanco", "anio": 2025, "kilometraje": 3500,
        "cod_tipo": cod_tipo, "estado": estado_veh, "modelo": modelo["cod_modelo"],
        "cedula": CEDULA_PROP_CAT
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
    a_data = {"copia_llaves": 1, "repuesto": 1, "triangulo": 1}
    c_data = {"estado": "Activo", "precio": precio, "descripcion": "Vehiculo catalogo integracion"}

    Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], cedula_usuario)
    return placa, marca, modelo


# ==============================================================================
#   PRUEBAS DE INTEGRACIÓN DEL MÓDULO CATÁLOGO
# ==============================================================================

def test_cp_int_cat_01_sp_obtener_disponibles_agrupa_imagenes(usuario_autorizado_vehiculos):
    """
    CP-INT-CAT-01: Integración Catalogo.obtener_disponibles() -> Procedimiento almacenado
    sp_obtener_catalogo_detallado en MySQL -> agrupación de múltiples fotos y conversión de precio.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    placa, _, _ = _crear_vehiculo_publicado_en_catalogo(cedula, precio=26500.50)

    try:
        # Insertar 2 imágenes en tabla imagen para probar agrupación desde el SP real
        conn = ConexionBD.obtener_conexion()
        cur = conn.cursor()
        cur.execute("INSERT INTO imagen (URL, fecha_subida, placa) VALUES (%s, CURDATE(), %s)", ("uploads/cat_1.jpg", placa))
        cur.execute("INSERT INTO imagen (URL, fecha_subida, placa) VALUES (%s, CURDATE(), %s)", ("uploads/cat_2.jpg", placa))
        conn.commit()
        cur.close()
        conn.close()

        disponibles = Catalogo.obtener_disponibles()
        encontrados = [v for v in disponibles if v["placa"] == placa]

        assert len(encontrados) == 1  # Agrupado en 1 solo vehículo aunque tenga 2 fotos
        veh = encontrados[0]
        assert isinstance(veh["precio"], float)
        assert veh["precio"] == 26500.50
        assert veh["imagenes_lista"] == ["uploads/cat_1.jpg", "uploads/cat_2.jpg"]
        assert veh["imagen_url"] == "uploads/cat_1.jpg"
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_cat_02_vehiculo_inactivo_excluido_del_catalogo(usuario_autorizado_vehiculos):
    """
    CP-INT-CAT-02: Integración Vehículo–Catálogo -> al inactivar un vehículo mediante
    Vehiculo.eliminar(), el procedimiento sp_obtener_catalogo_detallado deja de listarlo.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    placa, _, _ = _crear_vehiculo_publicado_en_catalogo(cedula)

    try:
        assert any(v["placa"] == placa for v in Catalogo.obtener_disponibles())

        Vehiculo.eliminar(placa, cedula)

        assert all(v["placa"] != placa for v in Catalogo.obtener_disponibles())
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=4, cod_modulo=2)


def test_cp_int_cat_03_obtener_por_placa_mediante_sp_real(usuario_autorizado_vehiculos):
    """
    CP-INT-CAT-03: Integración Catalogo.obtener_por_placa() contra sp_obtener_catalogo_detallado
    en MySQL para placa existente e inexistente.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    placa, _, _ = _crear_vehiculo_publicado_en_catalogo(cedula, precio=31200.00)

    try:
        detalle = Catalogo.obtener_por_placa(placa)
        assert detalle is not None
        assert detalle["placa"] == placa
        assert detalle["precio"] == 31200.0

        assert Catalogo.obtener_por_placa("NOEXISTE999") is None
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_cat_04_ruta_publica_catalogo_ventas_renderiza_vehiculo_real(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-CAT-04: Integración GET /catalogo-ventas (sin sesión) -> sp_obtener_catalogo_detallado ->
    renderizado real de templates/vehiculos/catalogo_lista.html con el vehículo publicado.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    _, marca, modelo = _crear_vehiculo_publicado_en_catalogo(cedula)

    try:
        respuesta = client_real.get("/catalogo-ventas")
        html = respuesta.data.decode("utf-8")

        assert respuesta.status_code == 200
        assert marca["nombre_marca"] in html
        assert modelo["nombre_modelo"] in html
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)


def test_cp_int_cat_05_ruta_inicio_integra_catalogo_disponibles(client_real, usuario_autorizado_vehiculos):
    """
    CP-INT-CAT-05: Integración de la página principal GET / (app.py -> index) con
    Catalogo.obtener_disponibles()[:6] y renderizado de templates/index.html.
    """
    cedula = usuario_autorizado_vehiculos["cedula_usuario"]
    _crear_vehiculo_publicado_en_catalogo(cedula)

    try:
        respuesta = client_real.get("/")
        assert respuesta.status_code == 200
    finally:
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=6)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=7)
        _limpiar_ultimo_registro_bitacora(cedula, cod_accion=1, cod_modulo=2)