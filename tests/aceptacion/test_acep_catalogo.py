from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"


def test_aceptacion_cp04_01_consulta_cliente_en_catalogo(page: Page):
    page.set_viewport_size({"width": 1280, "height": 720})
    resp = page.goto(f"{BASE_URL}/catalogo-ventas")
    assert resp is not None and resp.status == 200

    # 1. El cliente ve vehículos en exhibición con precio en dólares
    expect(page.get_by_text("Vehículos en Exhibición")).to_be_visible()
    filas = page.locator("#tablaCatalogo tbody tr")
    assert filas.count() > 0, "Debe haber al menos un vehículo Disponible en catálogo"
    expect(filas.first).to_contain_text("$")

    # Tomar la placa real del primer vehículo y probar el buscador del catálogo
    placa_real = filas.first.locator("td").nth(1).inner_text().strip()
    buscador = page.locator("#tablaCatalogo_filter input")
    if buscador.count() > 0:
        buscador.fill(placa_real)
        expect(filas.first).to_contain_text(placa_real)

    # 2. El cliente abre el expediente del vehículo disponible
    filas.first.locator("button[data-bs-target='#modalDetalles']").click()
    modal_det = page.locator("#modalDetalles")
    expect(modal_det).to_be_visible()
    expect(page.locator("#det-placa")).to_contain_text(placa_real)
    expect(page.locator("#det-estado")).to_contain_text("Disponible")
    modal_det.locator("button[data-bs-dismiss='modal']").first.click()
    expect(modal_det).to_be_hidden()

    # 3. El cliente abre la galería de fotos del vehículo y navega si hay más de una
    miniatura = filas.first.locator("[onclick*='abrirGaleriaCatalogo']")
    if miniatura.count() > 0:
        miniatura.click()
        modal_gal = page.locator("#modalGaleriaFotos")
        expect(modal_gal).to_be_visible()
        expect(page.locator("#galeria-contador")).to_contain_text("Foto 1 de")

        btn_next = modal_gal.locator(".carousel-control-next")
        if btn_next.is_visible():
            btn_next.click()
            expect(page.locator("#galeria-contador")).to_contain_text("Foto 2 de")

        modal_gal.locator("button[data-bs-dismiss='modal']").first.click()
        expect(modal_gal).to_be_hidden()