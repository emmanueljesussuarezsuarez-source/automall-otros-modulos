import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"


def test_ui_login_elementos_visibles(page: Page):
    errores_js = []
    page.on("pageerror", lambda err: errores_js.append(str(err)))

    page.goto(f"{BASE_URL}/login")

    expect(page.locator("#captchaInput")).to_be_visible()
    expect(page.locator("#btnSubmit")).to_be_visible()
    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_catalogo_publico_escritorio_y_movil(page: Page):
    errores_js = []
    page.on("pageerror", lambda err: errores_js.append(str(err)))

    # Vista escritorio
    page.set_viewport_size({"width": 1280, "height": 720})
    resp = page.goto(f"{BASE_URL}/catalogo-ventas")
    assert resp is not None and resp.status == 200
    expect(page.locator("body")).to_be_visible()

    # Vista móvil (responsive sin desbordamiento horizontal)
    page.set_viewport_size({"width": 375, "height": 812})
    sin_scroll_horizontal = page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2"
    )
    assert sin_scroll_horizontal, "El catálogo tiene desbordamiento horizontal en móvil"
    assert errores_js == [], f"Errores JS detectados: {errores_js}"