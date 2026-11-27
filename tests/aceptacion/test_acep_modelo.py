import os
import random
import string
import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "http://127.0.0.1:5000"
SESION_PATH = "tests/interfaz/sesion.json"


@pytest.fixture
def pagina(browser: Browser):
    assert os.path.exists(SESION_PATH), "Falta tests/interfaz/sesion.json"
    context = browser.new_context(storage_state=SESION_PATH, viewport={"width": 1280, "height": 720})
    page = context.new_page()
    yield page
    context.close()


def test_aceptacion_cp03_01_flujo_completo_modelo(pagina):
    sufijo = "".join(random.choices(string.ascii_lowercase, k=5))
    modelo_inicial = f"ModAce {sufijo}"
    modelo_editado = f"ModEdi {sufijo}"

    pagina.goto(f"{BASE_URL}/modelos/registro")
    assert "/login" not in pagina.url, "Sesión expirada: vuelve a generar sesion.json"

    # 1. Seleccionar primera marca disponible y registrar modelo (solo letras)
    opciones_marca = pagina.locator("#cod_marca option:not([disabled])")
    assert opciones_marca.count() > 0, "Debe existir al menos una marca activa en BD"
    cod_marca = opciones_marca.first.get_attribute("value")

    pagina.locator("#cod_marca").select_option(cod_marca)
    pagina.locator("#nombre_modelo").fill(modelo_inicial)
    pagina.locator("#formModelo button[type='submit']").click()

    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)
    pagina.wait_for_load_state("domcontentloaded")

    # 2. Verificar que aparece en #tablaModelos
    buscador = pagina.locator("#tablaModelos_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(modelo_inicial)
    fila = pagina.locator("#tablaModelos tbody tr", has_text=modelo_inicial)
    expect(fila.first).to_be_visible(timeout=5000)

    # 3. Editar el modelo en el modal
    fila.first.locator(".btn-editar").click()
    expect(pagina.locator("#modalEditar")).to_be_visible()
    pagina.locator("#edit_nombre_modelo").fill(modelo_editado)
    pagina.locator("#formEditar button[type='submit']").click()

    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)
    pagina.wait_for_load_state("domcontentloaded")

    # 4. Verificar cambio y eliminar registro temporal
    buscador = pagina.locator("#tablaModelos_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(modelo_editado)
    fila_editada = pagina.locator("#tablaModelos tbody tr", has_text=modelo_editado)
    expect(fila_editada.first).to_be_visible(timeout=5000)

    fila_editada.first.locator(".btn-eliminar-modelo").click()
    pagina.locator(".swal2-confirm").click()
    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)