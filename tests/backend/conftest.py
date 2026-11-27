import os
import shutil
import pytest
from app import app as flask_app
from models.db import ConexionBD
from utils.notificaciones_manager import FILE_PATH as NOTIF_FILE_PATH


@pytest.fixture(scope="session")
def app_backend():
    """Instancia real de Flask configurada en modo TESTING para pruebas de backend."""
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client_be(app_backend):
    """Cliente HTTP para peticiones directas al servidor backend."""
    with app_backend.test_client() as client:
        yield client


@pytest.fixture
def usuario_autorizado_be():
    """Obtiene de BD 'seguridad' un usuario real con permisos completos sobre 'Vehiculos'."""
    conexion = ConexionBD.obtener_conexion_seguridad()
    cursor = conexion.cursor(dictionary=True)
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
        cursor.execute(sql)
        usuario = cursor.fetchone()
        if not usuario:
            pytest.skip("No se encontró usuario con los 4 permisos sobre 'Vehiculos' en BD seguridad.")
        return usuario
    finally:
        cursor.close()
        conexion.close()


@pytest.fixture(autouse=True)
def respaldar_notificaciones_be():
    """Respalda y restaura data/notificaciones.json en cada prueba de backend."""
    backup_path = f"{NOTIF_FILE_PATH}.bak_be"
    existia = os.path.exists(NOTIF_FILE_PATH)
    if existia:
        shutil.copy2(NOTIF_FILE_PATH, backup_path)

    yield

    if existia and os.path.exists(backup_path):
        shutil.move(backup_path, NOTIF_FILE_PATH)
    elif not existia and os.path.exists(NOTIF_FILE_PATH):
        os.remove(NOTIF_FILE_PATH)