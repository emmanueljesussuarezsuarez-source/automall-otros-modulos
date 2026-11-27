import os
import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "http://127.0.0.1:5000"
SESION_PATH = "tests/interfaz/sesion.json"


@pytest.fixture
def pagina_modelo(browser: Browser):
    assert os.path.exists(SESION_PATH), (
        "Falta tests/interfaz/sesion.json. Ejecuta playwright codegen --save-storage primero."
    )
    context = browser.new_context(storage_state=SESION_PATH)
    page = context.new_page()
    yield page
    context.close()


def test_ui_modelo_elementos_y_datatable(pagina_modelo):
    errores_js = []
    pagina_modelo.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_modelo.goto(f"{BASE_URL}/modelos/registro")
    assert "/login" not in pagina_modelo.url, "Sesión expirada: vuelve a generar sesion.json"

    # Verificar formulario de Nuevo Modelo
    expect(pagina_modelo.locator("#formModelo")).to_be_visible()
    expect(pagina_modelo.locator("#cod_marca")).to_be_visible()
    expect(pagina_modelo.locator("#nombre_modelo")).to_be_visible()
    expect(pagina_modelo.locator("#nombre_modelo")).to_have_attribute("maxlength", "21")
    expect(pagina_modelo.locator("#formModelo button[type='submit']")).to_contain_text("Guardar Modelo")

    # Verificar tabla DataTables de Modelos
    expect(pagina_modelo.locator("#tablaModelos")).to_be_visible()
    buscador = pagina_modelo.locator("#tablaModelos_filter input")
    if buscador.count() > 0:
        expect(buscador).to_be_visible()
        buscador.fill("Corolla")
        buscador.fill("")

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_modelo_validacion_y_modal_editar(pagina_modelo):
    errores_js = []
    pagina_modelo.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_modelo.goto(f"{BASE_URL}/modelos/registro")
    assert "/login" not in pagina_modelo.url, "Sesión expirada: vuelve a generar sesion.json"

    # Validar que el select #cod_marca exige seleccionar una marca
    select_valido = pagina_modelo.evaluate(
        "document.getElementById('cod_marca').checkValidity()"
    )
    assert select_valido is False

    # Probar apertura, precarga de marca/nombre y cierre del Modal Editar
    botones_editar = pagina_modelo.locator(".btn-editar")
    if botones_editar.count() > 0:
        botones_editar.first.click()
        modal = pagina_modelo.locator("#modalEditar")
        expect(modal).to_be_visible()
        expect(pagina_modelo.locator("#edit_nombre_modelo")).not_to_have_value("")
        expect(pagina_modelo.locator("#edit_cod_marca")).not_to_have_value("")

        pagina_modelo.locator("#modalEditar button[data-bs-dismiss='modal']").first.click()
        expect(modal).to_be_hidden()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_modelo_responsive_movil(pagina_modelo):
    pagina_modelo.set_viewport_size({"width": 375, "height": 812})
    pagina_modelo.goto(f"{BASE_URL}/modelos/registro")
    assert "/login" not in pagina_modelo.url, "Sesión expirada: vuelve a generar sesion.json"

    expect(pagina_modelo.locator("#formModelo")).to_be_visible()
    expect(pagina_modelo.locator("#tablaModelos")).to_be_visible()