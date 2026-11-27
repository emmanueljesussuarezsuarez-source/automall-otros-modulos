import os
import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "http://127.0.0.1:5000"
SESION_PATH = "tests/interfaz/sesion.json"


@pytest.fixture
def pagina_marca(browser: Browser):
    assert os.path.exists(SESION_PATH), (
        "Falta tests/interfaz/sesion.json. Ejecuta playwright codegen --save-storage primero."
    )
    context = browser.new_context(storage_state=SESION_PATH)
    page = context.new_page()
    yield page
    context.close()


def test_ui_marca_elementos_y_datatable(pagina_marca):
    errores_js = []
    pagina_marca.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_marca.goto(f"{BASE_URL}/marcas/registro")
    assert "/login" not in pagina_marca.url, "Sesión expirada: vuelve a generar sesion.json"

    # Verificar formulario de Nueva Marca
    expect(pagina_marca.locator("#formMarca")).to_be_visible()
    expect(pagina_marca.locator("#nombre_marca")).to_be_visible()
    expect(pagina_marca.locator("#formMarca button[type='submit']")).to_contain_text("Guardar Marca")

    # Verificar tabla de listado DataTables
    expect(pagina_marca.locator("#tablaMarcas")).to_be_visible()
    buscador = pagina_marca.locator("#tablaMarcas_filter input")
    if buscador.count() > 0:
        expect(buscador).to_be_visible()
        buscador.fill("Toyota")
        buscador.fill("")

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_marca_validacion_y_modal_editar(pagina_marca):
    errores_js = []
    pagina_marca.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_marca.goto(f"{BASE_URL}/marcas/registro")
    assert "/login" not in pagina_marca.url, "Sesión expirada: vuelve a generar sesion.json"

    # Validación HTML5 de campo vacío (required)
    valido_vacio = pagina_marca.evaluate(
        "document.getElementById('nombre_marca').checkValidity()"
    )
    assert valido_vacio is False

    # Probar apertura y precarga del Modal Editar (si hay marcas registradas)
    botones_editar = pagina_marca.locator(".btn-editar-marca")
    if botones_editar.count() > 0:
        botones_editar.first.click()
        modal = pagina_marca.locator("#modalEditarMarca")
        expect(modal).to_be_visible()
        expect(pagina_marca.locator("#edit_nombre_marca")).not_to_have_value("")

        # Cerrar modal sin alterar la BD
        pagina_marca.locator("#modalEditarMarca button[data-bs-dismiss='modal']").first.click()
        expect(modal).to_be_hidden()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_marca_responsive_movil(pagina_marca):
    pagina_marca.set_viewport_size({"width": 375, "height": 812})
    pagina_marca.goto(f"{BASE_URL}/marcas/registro")
    assert "/login" not in pagina_marca.url, "Sesión expirada: vuelve a generar sesion.json"

    expect(pagina_marca.locator("#formMarca")).to_be_visible()
    expect(pagina_marca.locator("#tablaMarcas")).to_be_visible()