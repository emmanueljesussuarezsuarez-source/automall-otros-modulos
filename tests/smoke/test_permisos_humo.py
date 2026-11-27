import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from controllers.permisos_controller import permisos_bp  # Ajusta la ruta de importación según tu estructura

@pytest.fixture
def app():
    """Configura la aplicación Flask para entorno de pruebas."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'clave_secreta_de_prueba'
    
    # Registramos el blueprint del módulo de permisos
    app.register_blueprint(permisos_bp)
    
    return app

@pytest.fixture
def client(app):
    """Cliente de pruebas para realizar peticiones HTTP simuladas."""
    return app.test_client()


@patch('controllers.permisos_controller.Permiso')
@patch('controllers.permisos_controller.requiere_superusuario')
def test_gestionar_permisos_get_sin_rol(mock_superusuario, mock_permiso, client):
    """Prueba de humo para cargar la vista GET de gestión de permisos sin un rol seleccionado."""
    mock_superusuario.return_value = lambda f: f
    
    # Simulamos que se obtienen los roles del sistema
    mock_permiso.obtener_roles.return_value = [
        {"cod_rol": 1, "nombre_rol": "Administrador"},
        {"cod_rol": 2, "nombre_rol": "Supervisor"}
    ]

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.get('/gestionar')
    
    assert response.status_code == 200
    mock_permiso.obtener_roles.assert_called_once()
    mock_permiso.obtener_modulos_activos.assert_not_called()


@patch('controllers.permisos_controller.Permiso')
@patch('controllers.permisos_controller.requiere_superusuario')
def test_gestionar_permisos_get_con_rol(mock_superusuario, mock_permiso, client):
    """Prueba de humo para cargar la vista GET cuando ya viene un rol seleccionado por parámetro URL."""
    mock_superusuario.return_value = lambda f: f
    
    mock_permiso.obtener_roles.return_value = [{"cod_rol": 1, "nombre_rol": "Administrador"}]
    mock_permiso.obtener_modulos_activos.return_value = [{"id": 1, "nombre": "Bancos"}]
    mock_permiso.obtener_acciones_activas.return_value = [{"id": 1, "nombre": "p_crear"}]
    mock_permiso.obtener_permisos_asignados_rol.return_value = [1]

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.get('/gestionar?cod_rol=1')
    
    assert response.status_code == 200
    mock_permiso.obtener_roles.assert_called_once()
    mock_permiso.obtener_modulos_activos.assert_called_once()
    mock_permiso.obtener_acciones_activas.assert_called_once()
    mock_permiso.obtener_permisos_asignados_rol.assert_called_once_with(1)


@patch('controllers.permisos_controller.NotificacionManager')
@patch('controllers.permisos_controller.Permiso')
@patch('controllers.permisos_controller.requiere_superusuario')
def test_gestionar_permisos_post_exitoso(mock_superusuario, mock_permiso, mock_notificacion, client):
    """Prueba de humo para la sincronización exitosa de la matriz de permisos (POST)."""
    mock_superusuario.return_value = lambda f: f
    
    # Simulamos éxito en la sincronización del modelo
    mock_permiso.sincronizar_permisos.return_value = {"status": True}

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    # Enviamos datos incluyendo una lista de permisos marcados
    response = client.post('/gestionar', data={
        'id_rol_actual': '2',
        'permisos_activos': ['1_p_crear', '1_p_leer']
    }, follow_redirects=True)

    assert response.status_code == 200
    mock_permiso.sincronizar_permisos.assert_called_once_with('2', ['1_p_crear', '1_p_leer'], 12345678)
    mock_notificacion.crear.assert_called_once()


@patch('controllers.permisos_controller.NotificacionManager')
@patch('controllers.permisos_controller.Permiso')
@patch('controllers.permisos_controller.requiere_superusuario')
def test_gestionar_permisos_post_con_error(mock_superusuario, mock_permiso, mock_notificacion, client):
    """Prueba de humo para validar el manejo de errores cuando la sincronización de permisos falla."""
    mock_superusuario.return_value = lambda f: f
    
    # Simulamos fallo retornado por el modelo
    mock_permiso.sincronizar_permisos.return_value = {
        "status": False,
        "error": "Error interno de base de datos"
    }

    with client.session_transaction() as sess:
        sess['cedula_usuario'] = 12345678

    response = client.post('/gestionar', data={
        'id_rol_actual': '2',
        'permisos_activos': []
    }, follow_redirects=True)

    assert response.status_code == 200
    mock_permiso.sincronizar_permisos.assert_called_once()
    # No debería crearse la notificación si el modelo retornó error
    mock_notificacion.crear.assert_not_called()