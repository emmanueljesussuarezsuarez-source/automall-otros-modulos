import pytest
from app import app
from models.vehiculo import Vehiculo


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_smoke_rutas_vehiculo_registradas():
    rutas = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/vehiculos-lista" in rutas
    assert "/vehiculos-registrar" in rutas
    assert "/vehiculos-editar/<placa>" in rutas
    assert "/vehiculos-eliminar/<placa>" in rutas


def test_smoke_http_vehiculo_sin_error_servidor(client):
    for ruta in ("/vehiculos-lista", "/vehiculos-registrar"):
        resp = client.get(ruta, follow_redirects=False)
        assert resp.status_code in (200, 302)
        assert resp.status_code < 500


def test_smoke_conexion_bd_vehiculo():
    vehiculos = Vehiculo.obtener_todos()
    tipos = Vehiculo.obtener_tipos()
    assert isinstance(vehiculos, list)
    assert isinstance(tipos, list)