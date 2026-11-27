import pytest
from unittest.mock import MagicMock
from flask import Flask, Blueprint
from controllers.marca_controller import marca_bp
from controllers.modelo_controller import modelo_bp
from controllers.vehiculos_controller import vehiculos_bp
from controllers.catalogo_controller import catalogo_bp


def _crear_app_prueba(blueprint):
    """Función auxiliar para crear una app Flask aislada con un blueprint."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "clave_secreta_pruebas_unitarias"

    auth_bp = Blueprint("auth", __name__)

    @auth_bp.route("/login")
    def login():
        return "Login", 200

    app.register_blueprint(auth_bp)
    app.register_blueprint(blueprint)

    @app.route("/")
    def index():
        return "Inicio", 200

    return app


@pytest.fixture
def mock_bd(monkeypatch):
    """
    Simula la conexión y el cursor de MySQL para aislar las pruebas unitarias
    sin modificar la base de datos real 'automall' ni 'seguridad'.
    """
    mock_conexion = MagicMock()
    mock_cursor = MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        "models.db.ConexionBD.obtener_conexion",
        lambda: mock_conexion
    )
    return mock_conexion, mock_cursor


@pytest.fixture
def client_marca():
    """Cliente de pruebas Flask aislado para las rutas de marca_bp."""
    app = _crear_app_prueba(marca_bp)
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_modelo():
    """Cliente de pruebas Flask aislado para las rutas de modelo_bp."""
    app = _crear_app_prueba(modelo_bp)
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_vehiculos():
    """Cliente de pruebas Flask aislado para las rutas de vehiculos_bp."""
    app = _crear_app_prueba(vehiculos_bp)
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_catalogo():
    """Cliente de pruebas Flask aislado para las rutas de catalogo_bp."""
    app = _crear_app_prueba(catalogo_bp)
    with app.test_client() as client:
        yield client