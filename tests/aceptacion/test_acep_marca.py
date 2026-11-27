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


def test_aceptacion_cp02_01_flujo_completo_marca(pagina):
    sufijo = "".join(random.choices(string.ascii_lowercase, k=5))
    nombre_inicial = f"MarcaAce {sufijo}"
    nombre_editado = f"MarcaEdi {sufijo}"

    pagina.goto(f"{BASE_URL}/marcas/registro")
    assert "/login" not in pagina.url, "Sesión expirada: vuelve a generar sesion.json"

    # 1. Usuario registra una marca nueva (solo letras, máx 20 caracteres)
    pagina.locator("#nombre_marca").fill(nombre_inicial)
    pagina.locator("#formMarca button[type='submit']").click()

    # Esperar alerta verde de éxito y recarga automática (timer: 2000)
    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)
    pagina.wait_for_load_state("domcontentloaded")

    # 2. Verificar que aparece en el listado (filtrando por DataTables)
    buscador = pagina.locator("#tablaMarcas_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(nombre_inicial)
    fila = pagina.locator("#tablaMarcas tbody tr", has_text=nombre_inicial)
    expect(fila.first).to_be_visible(timeout=5000)

    # 3. Usuario edita la marca desde el modal
    fila.first.locator(".btn-editar-marca").click()
    expect(pagina.locator("#modalEditarMarca")).to_be_visible()
    pagina.locator("#edit_nombre_marca").fill(nombre_editado)
    pagina.locator("#formEditarMarca button[type='submit']").click()

    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)
    pagina.wait_for_load_state("domcontentloaded")

    # 4. Verificar cambio guardado y eliminar registro de prueba
    buscador = pagina.locator("#tablaMarcas_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(nombre_editado)
    fila_editada = pagina.locator("#tablaMarcas tbody tr", has_text=nombre_editado)
    expect(fila_editada.first).to_be_visible(timeout=5000)

    fila_editada.first.locator(".btn-eliminar-marca").click()
    pagina.locator(".swal2-confirm").click()
    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=5000)
    expect(pagina.locator(".swal2-popup")).to_be_hidden(timeout=6000)