import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from controllers.rol import roles_bp  # Ajusta la ruta de importación según tu estructura

@pytest.fixture
def app():
    """Configura la aplicación Flask para entorno de pruebas."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'clave_secreta_de_prueba'
    
    # Registramos el blueprint del módulo de roles
    app.register_blueprint(roles_bp)
    
    return app

@pytest.fixture
def client(app):
    """Cliente de pruebas para realizar peticiones HTTP simuladas."""
    return app.test_client()


@patch('controllers.rol.Rol')
@patch('controllers.rol.NotificacionManager')
@patch('controllers.rol.requiere_permiso')
def test_gestion_roles_get(mock_permiso, mock_notificacion, mock_rol, client):
    """Prueba de humo para verificar la carga de la vista GET de gestión de roles."""
    mock_permiso.return_value = lambda f: f
    
    # Simulamos los roles devueltos por el modelo
    mock_rol.obtener_todos.return_value = [
        {"id": 1, "nombre_rol": "Administrador", "descripcion_rol": "Acceso total", "estatus": 1},
        {"id": 2, "nombre_rol": "Supervisor", "descripcion_rol": "Acceso operativo", "estatus": 1}
    ]

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.get('/roles/gestion')
    
    assert response.status_code == 200
    mock_rol.obtener_todos.assert_called_once()


@patch('controllers.rol.Rol')
@patch('controllers.rol.NotificacionManager')
@patch('controllers.rol.requiere_permiso')
def test_gestion_roles_post_crear(mock_permiso, mock_notificacion, mock_rol, client):
    """Prueba de humo para el registro exitoso de un nuevo rol vía POST."""
    mock_permiso.return_value = lambda f: f
    
    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/roles/gestion', data={
        'nombre_rol': 'Auditor',
        'descripcion_rol': 'Rol para revisión de registros',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Rol registrado con éxito"
    
    # Validar llamadas al modelo y al gestor de notificaciones
    mock_rol.guardar.assert_called_once_with('Auditor', 'Rol para revisión de registros', 1, 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.rol.Rol')
@patch('controllers.rol.NotificacionManager')
@patch('controllers.rol.requiere_permiso')
def test_editar_rol_post(mock_permiso, mock_notificacion, mock_rol, client):
    """Prueba de humo para la actualización de un rol existente."""
    mock_permiso.return_value = lambda f: f
    
    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/roles/editar/1', data={
        'nombre_rol': 'Administrador General',
        'descripcion_rol': 'Actualización de descripción',
        'estatus': 1
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Rol actualizado correctamente"
    
    mock_rol.actualizar.assert_called_once_with(1, 'Administrador General', 'Actualización de descripción', '1', 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.rol.Rol')
@patch('controllers.rol.NotificacionManager')
@patch('controllers.rol.requiere_permiso')
def test_eliminar_rol_post(mock_permiso, mock_notificacion, mock_rol, client):
    """Prueba de humo para la desactivación o eliminación lógica de un rol."""
    mock_permiso.return_value = lambda f: f
    
    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/roles/eliminar/2')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "Rol desactivado/eliminado correctamente"
    
    mock_rol.eliminar.assert_called_once_with(2, 12345678)
    mock_notificacion.crear.assert_called_once()