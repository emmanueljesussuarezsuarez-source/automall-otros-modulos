import base64
import os
import time
import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "http://127.0.0.1:5000"
SESION_PATH = "tests/interfaz/sesion.json"

# PNG mínimo válido de 1x1 píxel en memoria para validar la carga de imagen
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def pagina(browser: Browser):
    assert os.path.exists(SESION_PATH), "Falta tests/interfaz/sesion.json"
    context = browser.new_context(storage_state=SESION_PATH, viewport={"width": 1280, "height": 720})
    page = context.new_page()
    yield page
    context.close()


def test_aceptacion_cp01_01_flujo_completo_vehiculo(pagina):
    placa_prueba = f"ACP-{int(time.time()) % 1000:03d}"

    pagina.goto(f"{BASE_URL}/vehiculos-registrar")
    assert "/login" not in pagina.url, "Sesión expirada: vuelve a generar sesion.json"

    # 1. Llenar documentación, accesorios y datos técnicos cumpliendo validacion_vehiculo.js
    pagina.locator("input[name='fecha_ingreso']").fill("2026-11-26")
    pagina.locator("#original_totalPropiedad").check()
    pagina.locator("#copia_llaves").check()

    pagina.locator("input[name='placa']").fill(placa_prueba)
    pagina.locator("input[name='color']").fill("Blanco")
    pagina.locator("input[name='anio']").fill("2022")
    pagina.locator("input[name='kilometraje']").fill("45000")

    tipo_val = pagina.locator("select[name='tipo']:not(#modal_tipo) option:not([disabled])").first.get_attribute("value")
    modelo_val = pagina.locator("#select-modelo option:not([disabled])").first.get_attribute("value")
    prop_val = pagina.locator("#select-propietario option:not([disabled])").first.get_attribute("value")

    pagina.locator("select[name='tipo']:not(#modal_tipo)").select_option(tipo_val)
    pagina.locator("#select-modelo").select_option(modelo_val)
    pagina.locator("#select-propietario").select_option(prop_val)

    pagina.locator("#input-imagenes").set_input_files(
        {"name": "prueba_acep.png", "mimeType": "image/png", "buffer": PNG_1X1}
    )
    pagina.locator("input[name='precio']").fill("14500")
    pagina.locator("textarea[name='descripcion_catalogo']").fill("Vehiculo de prueba de aceptacion.")

    pagina.get_by_role("button", name="Finalizar Registro").click()

    # Esperar alerta verde "¡Registrado!" y redirección automática a /vehiculos-lista
    expect(pagina.locator(".swal2-icon-success")).to_be_visible(timeout=8000)
    pagina.wait_for_url("**/vehiculos-lista", timeout=8000)

    # 2. Buscar en el inventario y verificar el Modal Expediente (#modalDetalles)
    buscador = pagina.locator("#tablaVehiculos_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(placa_prueba)
    fila = pagina.locator("#tablaVehiculos tbody tr", has_text=placa_prueba)
    expect(fila.first).to_be_visible(timeout=5000)

    fila.first.locator("button[data-bs-target='#modalDetalles']").click()
    expect(pagina.locator("#modalDetalles")).to_be_visible()
    expect(pagina.locator("#det-placa")).to_contain_text(placa_prueba)
    pagina.locator("#modalDetalles button[data-bs-dismiss='modal']").first.click()
    expect(pagina.locator("#modalDetalles")).to_be_hidden()

    # 3. Verificar registro automático en el Historial de Movimientos
    pagina.goto(f"{BASE_URL}/vehiculos-historial")
    busc_hist = pagina.locator("#tablaHistorial_filter input")
    expect(busc_hist).to_be_visible(timeout=5000)
    busc_hist.fill(placa_prueba)
    expect(pagina.locator("#tablaHistorial tbody tr", has_text=placa_prueba).first).to_be_visible(timeout=5000)

    # 4. Volver a lista y eliminar el vehículo temporal para dejar la BD limpia
    pagina.goto(f"{BASE_URL}/vehiculos-lista")
    buscador = pagina.locator("#tablaVehiculos_filter input")
    expect(buscador).to_be_visible(timeout=5000)
    buscador.fill(placa_prueba)
    fila_limpiar = pagina.locator("#tablaVehiculos tbody tr", has_text=placa_prueba)
    expect(fila_limpiar.first).to_be_visible(timeout=5000)

    fila_limpiar.first.locator("button.btn-outline-danger").click()
    pagina.locator(".swal2-confirm").click()
    pagina.wait_for_load_state("domcontentloaded")