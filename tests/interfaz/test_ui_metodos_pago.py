from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def test_ui_metodos_pago_estructura_y_modal(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/metodos-pago/gestion")

    expect(page.get_by_role("heading", name="Gestión de Métodos de Pago")).to_be_visible()
    btn_nuevo = page.get_by_role("button", name="Nuevo Método")
    expect(btn_nuevo).to_be_visible()

    expect(page.locator("table thead th")).to_have_text(
        ["ID", "Método de Pago", "Requiere Referencia", "Estado", "Acciones"]
    )

    # Abrir modal crear
    btn_nuevo.click()
    modal = page.locator("#modalMetodo")
    expect(modal).to_be_visible()
    expect(page.locator("#modalTitulo")).to_have_text("Nuevo Método de Pago")
    expect(page.locator("#nombre_metodo")).to_have_value("")
    expect(page.locator("#requiere_referencia option")).to_have_text(["Sí", "No"])
    expect(page.locator("#estado option")).to_have_text(["Activo", "Inactivo"])

    # Camino triste UI: nombre vacío bloqueado por HTML5 required
    page.locator("#formMetodo button[type='submit']").click()
    expect(modal).to_be_visible()
    assert page.locator("#nombre_metodo").evaluate("el => el.checkValidity()") is False

    # Cerrar modal
    modal.get_by_role("button", name="Cancelar").click()
    expect(modal).to_be_hidden()