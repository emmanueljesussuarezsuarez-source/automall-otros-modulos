import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from controllers.configuracion_controller import config_bp  # Ajusta la ruta de importación según tu estructura

@pytest.fixture
def app():
    """Configura la aplicación Flask para entorno de pruebas."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'clave_secreta_de_prueba'
    
    # Registramos el blueprint del módulo de configuración
    app.register_blueprint(config_bp)
    
    return app

@pytest.fixture
def client(app):
    """Cliente de pruebas para realizar peticiones HTTP simuladas."""
    return app.test_client()


@patch('controllers.configuracion_controller.Modulo')
@patch('controllers.configuracion_controller.Accion')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_gestion_configuracion_get(mock_permiso, mock_accion, mock_modulo, client):
    """Prueba de humo para la carga de la vista GET de módulos y acciones."""
    mock_permiso.return_value = lambda f: f
    
    mock_modulo.obtener_todos.return_value = [{"id": 1, "nombre_modulo": "Bancos"}]
    mock_accion.obtener_todas.return_value = [{"id": 1, "nom_accion": "p_crear"}]

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.get('/configuracion/modulos-acciones')
    
    assert response.status_code == 200
    mock_modulo.obtener_todos.assert_called_once()
    mock_accion.obtener_todas.assert_called_once()


# ================= PRUEBAS PARA MÓDULOS =================

@patch('controllers.configuracion_controller.os.path.exists')
@patch('controllers.configuracion_controller.Modulo')
@patch('controllers.configuracion_controller.NotificacionManager')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_crear_modulo_exitoso(mock_permiso, mock_notificacion, mock_modulo, mock_exists, client):
    """Prueba de humo para registrar un módulo exitosamente (cuando existen los archivos físicos)."""
    mock_permiso.return_value = lambda f: f
    # Simulamos que los archivos físicos del módulo sí existen en el sistema
    mock_exists.return_value = True

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/modulos/crear', data={
        'nombre_modulo': 'Bancos',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Módulo registrado con éxito"
    
    mock_modulo.guardar.assert_called_once_with('Bancos', 1, 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.configuracion_controller.os.path.exists')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_crear_modulo_fals_archivos_faltantes(mock_permiso, mock_exists, client):
    """Prueba de humo para validar el error cuando faltan los archivos físicos del módulo."""
    mock_permiso.return_value = lambda f: f
    # Simulamos que los archivos físicos NO existen
    mock_exists.return_value = False

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/modulos/crear', data={
        'nombre_modulo': 'Inventario',
        'estatus': 1
    })

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["status"] == "error"
    assert "Faltan los siguientes archivos físicos" in json_data["message"]


@patch('controllers.configuracion_controller.Modulo')
@patch('controllers.configuracion_controller.NotificacionManager')
def test_editar_modulo(mock_notificacion, mock_modulo, client):
    """Prueba de humo para actualizar un módulo existente."""
    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/modulos/editar/1', data={
        'nombre_modulo': 'Bancos Modificado',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Módulo actualizado"
    
    mock_modulo.actualizar.assert_called_once_with(1, 'Bancos Modificado', '1', 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.configuracion_controller.Modulo')
@patch('controllers.configuracion_controller.NotificacionManager')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_eliminar_modulo(mock_permiso, mock_notificacion, mock_modulo, client):
    """Prueba de humo para desactivar un módulo."""
    mock_permiso.return_value = lambda f: f

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/modulos/eliminar/1')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Módulo desactivado"
    
    mock_modulo.eliminar.assert_called_once_with(1, 12345678)
    mock_notificacion.crear.assert_called_once()


# ================= PRUEBAS PARA ACCIONES =================

@patch('controllers.configuracion_controller.Accion')
@patch('controllers.configuracion_controller.NotificacionManager')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_crear_accion_exitosa(mock_permiso, mock_notificacion, mock_accion, client):
    """Prueba de humo para registrar una nueva acción."""
    mock_permiso.return_value = lambda f: f

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/acciones/crear', data={
        'nom_accion': 'p_exportar',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Acción registrada con éxito"
    
    mock_accion.guardar.assert_called_once_with('p_exportar', 1, 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.configuracion_controller.Accion')
@patch('controllers.configuracion_controller.NotificacionManager')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_editar_accion(mock_permiso, mock_notificacion, mock_accion, client):
    """Prueba de humo para actualizar una acción existente."""
    mock_permiso.return_value = lambda f: f

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/acciones/editar/1', data={
        'nom_accion': 'p_exportar_updated',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Acción actualizada"
    
    mock_accion.actualizar.assert_called_once_with(1, 'p_exportar_updated', '1', 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.configuracion_controller.Accion')
@patch('controllers.configuracion_controller.NotificacionManager')
@patch('controllers.configuracion_controller.requiere_permiso')
def test_eliminar_accion(mock_permiso, mock_notificacion, mock_accion, client):
    """Prueba de humo para desactivar una acción."""
    mock_permiso.return_value = lambda f: f

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/acciones/eliminar/1')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Acción desactivada"
    
    mock_accion.eliminar.assert_called_once_with(1, 12345678)
    mock_notificacion.crear.assert_called_once()