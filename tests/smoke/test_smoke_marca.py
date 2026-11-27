import pytest
from app import app
from models.marca import Marca


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_smoke_rutas_marca_registradas():
    rutas = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/marcas/registro" in rutas
    assert "/marcas/editar/<int:id>" in rutas
    assert "/marcas/eliminar/<int:id>" in rutas


def test_smoke_http_marca_sin_error_servidor(client):
    resp = client.get("/marcas/registro", follow_redirects=False)
    assert resp.status_code in (200, 302)
    assert resp.status_code < 500


def test_smoke_conexion_bd_marca():
    marcas = Marca.obtener_todas()
    assert isinstance(marcas, list)