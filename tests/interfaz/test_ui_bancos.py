from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def test_ui_bancos_estructura_y_modal(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/bancos/gestion")

    # Elementos de cabecera y tabla
    expect(page.get_by_role("heading", name="Gestión de Bancos")).to_be_visible()
    btn_nuevo = page.get_by_role("button", name="Nuevo Banco")
    expect(btn_nuevo).to_be_visible()

    encabezados = page.locator("table thead th")
    expect(encabezados).to_have_text(["ID", "Nombre del Banco", "Estado", "Acciones"])

    # Abrir modal crear
    btn_nuevo.click()
    modal = page.locator("#modalBanco")
    expect(modal).to_be_visible()
    expect(page.locator("#modalTitulo")).to_have_text("Nuevo Banco")
    expect(page.locator("#nombre_banco")).to_have_value("")
    expect(page.locator("#estado")).to_have_value("Activo")

    # Camino triste UI: intentar guardar vacío activa validación HTML5
    page.locator("#formBanco button[type='submit']").click()
    expect(modal).to_be_visible()
    assert page.locator("#nombre_banco").evaluate("el => el.checkValidity()") is False

    # Cerrar modal con botón Cancelar
    modal.get_by_role("button", name="Cancelar").click()
    expect(modal).to_be_hidden()