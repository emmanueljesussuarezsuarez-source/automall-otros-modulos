import os
import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "http://127.0.0.1:5000"
SESION_PATH = "tests/interfaz/sesion.json"


@pytest.fixture
def pagina_vehiculo(browser: Browser):
    assert os.path.exists(SESION_PATH), (
        "Falta tests/interfaz/sesion.json. Ejecuta playwright codegen --save-storage primero."
    )
    context = browser.new_context(
        storage_state=SESION_PATH,
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()
    yield page
    context.close()


def test_ui_vehiculo_lista_detalles_y_galeria(pagina_vehiculo):
    errores_js = []
    pagina_vehiculo.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-lista")
    assert "/login" not in pagina_vehiculo.url, "Sesión expirada: vuelve a generar sesion.json"

    expect(pagina_vehiculo.get_by_role("link", name="Registrar Vehículo")).to_be_visible()
    expect(pagina_vehiculo.locator("#tablaVehiculos")).to_be_visible()

    # Probar Modal de Expediente / Detalles si hay al menos un vehículo
    botones_detalle = pagina_vehiculo.locator("button[data-bs-target='#modalDetalles']")
    if botones_detalle.count() > 0:
        botones_detalle.first.click()
        modal_det = pagina_vehiculo.locator("#modalDetalles")
        expect(modal_det).to_be_visible()
        expect(pagina_vehiculo.locator("#det-placa")).not_to_be_empty()
        expect(pagina_vehiculo.locator("#det-vehiculo")).not_to_be_empty()
        pagina_vehiculo.locator("#modalDetalles button[data-bs-dismiss='modal']").first.click()
        expect(modal_det).to_be_hidden()

    # Probar Modal de Galería de Fotos si existe un vehículo con fotos
    botones_galeria = pagina_vehiculo.locator("[data-bs-target='#modalGaleriaFotos']")
    if botones_galeria.count() > 0:
        botones_galeria.first.click()
        modal_gal = pagina_vehiculo.locator("#modalGaleriaFotos")
        expect(modal_gal).to_be_visible()
        expect(pagina_vehiculo.locator("#carruselVehiculo")).to_be_visible()
        pagina_vehiculo.locator("#modalGaleriaFotos button[data-bs-dismiss='modal']").first.click()
        expect(modal_gal).to_be_hidden()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_vehiculo_registro_y_modales_rapidos(pagina_vehiculo):
    errores_js = []
    pagina_vehiculo.on("pageerror", lambda err: errores_js.append(str(err)))

    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-registrar")
    assert "/login" not in pagina_vehiculo.url, "Sesión expirada: vuelve a generar sesion.json"

    # Verificar secciones principales del formulario
    expect(pagina_vehiculo.locator("input[name='fecha_ingreso']")).to_be_visible()
    expect(pagina_vehiculo.locator("input[name='placa']")).to_be_visible()
    expect(pagina_vehiculo.locator("#select-modelo")).to_be_visible()
    expect(pagina_vehiculo.locator("#select-marca")).to_be_visible()
    expect(pagina_vehiculo.locator("#select-propietario")).to_be_visible()
    expect(pagina_vehiculo.locator("#input-imagenes")).to_be_visible()
    expect(pagina_vehiculo.locator("input[name='precio']")).to_be_visible()
    expect(pagina_vehiculo.locator("textarea[name='descripcion_catalogo']")).to_be_visible()

    # Verificar validación HTML5 de placa obligatoria
    placa_valida = pagina_vehiculo.evaluate(
        "document.querySelector('input[name=\"placa\"]').checkValidity()"
    )
    assert placa_valida is False

    # Probar selección en cascada Modelo -> Marca Asignada
    opciones_modelo = pagina_vehiculo.locator("#select-modelo option:not([disabled])")
    if opciones_modelo.count() > 0:
        valor_modelo = opciones_modelo.first.get_attribute("value")
        marca_esperada = opciones_modelo.first.get_attribute("data-marca")
        pagina_vehiculo.locator("#select-modelo").select_option(valor_modelo)
        if marca_esperada:
            expect(pagina_vehiculo.locator("#select-marca")).to_have_value(marca_esperada)

    # Probar apertura y cierre de los 3 modales rápidos (Modelo, Marca, Propietario)
    for modal_id in ("#modalCrearModelo", "#modalCrearMarca", "#modalCrearPropietario"):
        pagina_vehiculo.locator(f"a[data-bs-target='{modal_id}']").click()
        modal = pagina_vehiculo.locator(modal_id)
        expect(modal).to_be_visible()
        pagina_vehiculo.locator(f"{modal_id} button[data-bs-dismiss='modal']").first.click()
        expect(modal).to_be_hidden()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_vehiculo_editar_y_historial(pagina_vehiculo):
    errores_js = []
    pagina_vehiculo.on("pageerror", lambda err: errores_js.append(str(err)))

    # Ir a Editar desde el primer vehículo de la lista (si existe)
    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-lista")
    assert "/login" not in pagina_vehiculo.url, "Sesión expirada: vuelve a generar sesion.json"

    enlaces_editar = pagina_vehiculo.locator("a[href*='/vehiculos-editar/']")
    if enlaces_editar.count() > 0:
        enlaces_editar.first.click()
        expect(pagina_vehiculo.locator("#form-editar-vehiculo")).to_be_visible()
        expect(pagina_vehiculo.locator("input[name='placa']")).not_to_have_value("")
        expect(pagina_vehiculo.locator("input[name='precio']")).not_to_have_value("")
        expect(pagina_vehiculo.locator("#galeria-fotos-actuales")).to_be_visible()
        expect(pagina_vehiculo.locator("#input-nuevas-fotos")).to_be_visible()

    # Verificar vista Historial de Movimientos
    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-historial")
    expect(pagina_vehiculo.locator("#tablaHistorial")).to_be_visible()

    assert errores_js == [], f"Errores JS detectados: {errores_js}"


def test_ui_vehiculo_responsive_movil(pagina_vehiculo):
    pagina_vehiculo.set_viewport_size({"width": 375, "height": 812})
    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-lista")
    assert "/login" not in pagina_vehiculo.url, "Sesión expirada: vuelve a generar sesion.json"
    expect(pagina_vehiculo.locator("#tablaVehiculos")).to_be_visible()

    pagina_vehiculo.goto(f"{BASE_URL}/vehiculos-registrar")
    expect(pagina_vehiculo.locator("input[name='placa']")).to_be_visible()