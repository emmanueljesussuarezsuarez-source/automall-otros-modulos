import pytest
from app import app
from models.modelo import Modelo


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_smoke_rutas_modelo_registradas():
    rutas = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/modelos/registro" in rutas
    assert "/modelos/editar/<int:id>" in rutas
    assert "/modelos/eliminar/<int:id>" in rutas


def test_smoke_http_modelo_sin_error_servidor(client):
    resp = client.get("/modelos/registro", follow_redirects=False)
    assert resp.status_code in (200, 302)
    assert resp.status_code < 500


def test_smoke_conexion_bd_modelo():
    modelos = Modelo.obtener_todas()
    assert isinstance(modelos, list)