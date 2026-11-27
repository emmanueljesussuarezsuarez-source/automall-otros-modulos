import pytest
from app import app
from models.catalogo import Catalogo


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_smoke_ruta_catalogo_registrada():
    rutas = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/catalogo-ventas" in rutas


def test_smoke_http_catalogo_publico_disponible(client):
    resp = client.get("/catalogo-ventas")
    assert resp.status_code == 200
    assert b"<html" in resp.data.lower()


def test_smoke_conexion_bd_catalogo():
    disponibles = Catalogo.obtener_disponibles()
    assert isinstance(disponibles, list)