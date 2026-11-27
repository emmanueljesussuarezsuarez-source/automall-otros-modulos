from models.catalogo import Catalogo


def test_be_cat_01_endpoint_cabeceras_http_y_codificacion(client_be):
    """CP-BE-CAT-01: Validar código HTTP 200, tipo de contenido HTML y codificación UTF-8 en /catalogo-ventas."""
    resp = client_be.get("/catalogo-ventas")

    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    assert "charset=utf-8" in resp.content_type.lower()


def test_be_cat_02_metodo_post_no_permitido_405(client_be):
    """CP-BE-CAT-02: Validar que el endpoint de solo lectura /catalogo-ventas rechaza peticiones POST (405)."""
    resp = client_be.post("/catalogo-ventas", data={"precio": "1"})
    assert resp.status_code == 405


def test_be_cat_03_sp_protegido_contra_sql_injection(app_backend):
    """CP-BE-CAT-03: Procedimiento almacenado sp_obtener_catalogo_detallado neutraliza inyección SQL."""
    resultado = Catalogo.obtener_por_placa("' OR '1'='1")
    assert resultado is None


def test_be_cat_04_ruta_inexistente_devuelve_404(client_be):
    """CP-BE-CAT-04: Ruta inexistente bajo catálogo retorna HTTP 404 Not Found sin error 500."""
    resp = client_be.get("/catalogo-ventas/ruta-inexistente-999")
    assert resp.status_code == 404