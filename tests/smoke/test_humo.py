import os
import pytest
from flask import url_for
from app import app as flask_app
from models.db import ConexionBD
from utils.notificaciones_manager import NotificacionManager


@pytest.fixture(scope="module")
def client_humo():
    """Cliente de pruebas sobre la app Flask real para verificación de arranque."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope="module")
def usuario_humo():
    """Obtiene un usuario real de BD 'seguridad' con permisos sobre 'Vehiculos'."""
    conn = ConexionBD.obtener_conexion_seguridad()
    cur = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT u.cedula_usuario, u.cod_rol
            FROM t_usuario u
            INNER JOIN t_rol_permiso rp ON rp.cod_rol = u.cod_rol
            INNER JOIN t_permiso p ON rp.cod_permiso = p.cod_permiso
            INNER JOIN t_modulo m ON p.cod_modulo = m.cod_modulo
            INNER JOIN t_acciones a ON p.cod_accion = a.cod_accion
            WHERE m.nombre_modulo = 'Vehiculos'
              AND a.nom_accion IN ('CREAR', 'LEER', 'ACTUALIZAR', 'ELIMINAR')
            GROUP BY u.cedula_usuario, u.cod_rol
            HAVING COUNT(DISTINCT a.nom_accion) = 4
            LIMIT 1
        """
        cur.execute(sql)
        usuario = cur.fetchone()
        if not usuario:
            pytest.skip("No se encontró usuario con permisos sobre 'Vehiculos' en BD seguridad.")
        return usuario
    finally:
        cur.close()
        conn.close()


def test_cp_humo_01_arranque_flask_y_blueprints_criticos():
    """CP-HUMO-01: Verificar que la aplicación Flask instancia y registra los Blueprints clave."""
    assert flask_app is not None
    assert bool(flask_app.secret_key)
    assert {"marcas", "modelos", "vehiculos", "catalogo"}.issubset(flask_app.blueprints.keys())
    assert len(flask_app.blueprints) >= 20


def test_cp_humo_02_salud_conexiones_mysql_negocio_y_seguridad():
    """CP-HUMO-02: Verificar conectividad activa con ambas bases de datos ('automall' y 'seguridad')."""
    # 1. Base de datos de negocio (automall)
    conn_neg = ConexionBD.obtener_conexion()
    cur_neg = conn_neg.cursor()
    try:
        for tabla in ("marca", "modelo", "vehiculo", "catalogo"):
            cur_neg.execute(f"SELECT COUNT(*) FROM {tabla}")
            assert cur_neg.fetchone()[0] >= 0
    finally:
        cur_neg.close()
        conn_neg.close()

    # 2. Base de datos de seguridad (seguridad)
    conn_seg = ConexionBD.obtener_conexion_seguridad()
    cur_seg = conn_seg.cursor()
    try:
        for tabla in ("t_usuario", "t_rol", "t_bitacora"):
            cur_seg.execute(f"SELECT COUNT(*) FROM {tabla}")
            assert cur_seg.fetchone()[0] >= 0
    finally:
        cur_seg.close()
        conn_seg.close()


def test_cp_humo_03_rutas_publicas_principales_responden_200(client_humo):
    """CP-HUMO-03: Verificar que inicio (/), catálogo (/catalogo-ventas) y login cargan con HTTP 200."""
    with flask_app.test_request_context():
        login_url = url_for("auth.login")

    for ruta in ("/", "/catalogo-ventas", login_url):
        resp = client_humo.get(ruta)
        assert resp.status_code == 200, f"Fallo al cargar ruta pública {ruta}"
        assert len(resp.data) > 0


def test_cp_humo_04_rutas_privadas_activas_y_protegidas(client_humo):
    """CP-HUMO-04: Verificar que las rutas administrativas existen y redirigen (302) sin sesión."""
    rutas_privadas = (
        "/marcas/registro",
        "/modelos/registro",
        "/vehiculos-lista",
        "/vehiculos-registrar",
        "/vehiculos-historial",
    )
    for ruta in rutas_privadas:
        resp = client_humo.get(ruta)
        assert resp.status_code == 302, f"La ruta {ruta} no protegió el acceso sin sesión"


def test_cp_humo_05_vistas_autenticadas_cargan_sin_errores_500(client_humo, usuario_humo):
    """CP-HUMO-05: Verificar que las vistas reales de Marca, Modelo, Vehículo e Historial renderizan HTTP 200."""
    with client_humo.session_transaction() as sess:
        sess["cod_rol"] = usuario_humo["cod_rol"]
        sess["cedula_usuario"] = usuario_humo["cedula_usuario"]

    rutas_autenticadas = (
        "/marcas/registro",
        "/modelos/registro",
        "/vehiculos-lista",
        "/vehiculos-registrar",
        "/vehiculos-historial",
    )
    for ruta in rutas_autenticadas:
        resp = client_humo.get(ruta)
        assert resp.status_code == 200, f"Error al renderizar vista autenticada {ruta}"
        assert len(resp.data) > 0


def test_cp_humo_06_recursos_estaticos_plantillas_y_notificaciones():
    """CP-HUMO-06: Verificar existencia de carpetas templates/static y lectura válida de notificaciones.json."""
    assert os.path.isdir(flask_app.template_folder)
    assert os.path.isdir(flask_app.static_folder)
    notificaciones = NotificacionManager._cargar_todas()
    assert isinstance(notificaciones, list)