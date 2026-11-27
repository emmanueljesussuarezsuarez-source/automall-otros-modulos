from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"


def test_ui_catalogo_tabla_y_buscador(page: Page):
    errores_js = []
    page.on("pageerror", lambda err: errores_js.append(str(err)))

    page.set_viewport_size({"width": 1280, "height": 720})
    resp = page.goto(f"{BASE_URL}/catalogo-ventas")
    assert resp is not None and resp.status == 200

    expect(page.get_by_text("Vehículos en Exhibición")).to_be_visible()
    expect(page.locator("#tablaCatalogo")).to_be_visible()
    expect(page.get_by_role("link", name="Volver al Inventario")).to_be_visible()

    buscador = page.locator("#tablaCatalogo_filter input")
    if buscador.count() > 0:
        expect(buscador).to_be_visible()
        buscador.fill("Toyota")
        buscador.fill("")

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_catalogo_galeria_y_modal_detalles(page: Page):
    errores_js = []
    page.on("pageerror", lambda err: errores_js.append(str(err)))

    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(f"{BASE_URL}/catalogo-ventas")

    # Probar Modal de Detalles si hay vehículos en exhibición
    botones_detalle = page.locator("button[data-bs-target='#modalDetalles']")
    if botones_detalle.count() > 0:
        botones_detalle.first.click()
        modal_det = page.locator("#modalDetalles")
        expect(modal_det).to_be_visible()
        expect(page.locator("#det-placa")).not_to_be_empty()
        expect(page.locator("#det-vehiculo")).not_to_be_empty()

        page.locator("#modalDetalles button[data-bs-dismiss='modal']").first.click()
        expect(modal_det).to_be_hidden()

    # Probar Modal de Galería y navegación del carrusel si hay fotos
    miniaturas_galeria = page.locator("[onclick*='abrirGaleriaCatalogo']")
    if miniaturas_galeria.count() > 0:
        miniaturas_galeria.first.click()
        modal_gal = page.locator("#modalGaleriaFotos")
        expect(modal_gal).to_be_visible()
        expect(page.locator("#galeriaTitulo")).to_contain_text("Fotos:")
        expect(page.locator("#carrusel-items .carousel-item.active")).to_be_visible()
        expect(page.locator("#galeria-contador")).to_contain_text("Foto 1 de")

        # Si el vehículo tiene más de 1 foto, probar botón Siguiente
        btn_next = modal_gal.locator(".carousel-control-next")
        if btn_next.is_visible():
            btn_next.click()
            expect(page.locator("#galeria-contador")).to_contain_text("Foto 2 de")

        page.locator("#modalGaleriaFotos button[data-bs-dismiss='modal']").first.click()
        expect(modal_gal).to_be_hidden()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_catalogo_responsive_movil(page: Page):
    errores_js = []
    page.on("pageerror", lambda err: errores_js.append(str(err)))

    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{BASE_URL}/catalogo-ventas")

    expect(page.locator("#tablaCatalogo")).to_be_visible()
    assert errores_js == [], f"Errores JS detectados: {errores_js}"