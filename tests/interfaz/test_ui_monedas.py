from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def test_ui_monedas_estructura_y_cambio_pestanas(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/monedas/gestion")

    expect(page.get_by_role("heading", name="Gestión de Monedas")).to_be_visible()
    expect(page.get_by_role("button", name="Nuevo Registro")).to_be_visible()

    btn_monedas = page.locator("#btnMonedas")
    btn_digitales = page.locator("#btnDigitales")
    sec_monedas = page.locator("#seccionMonedas")
    sec_digitales = page.locator("#seccionDigitales")

    # Estado inicial: Monedas visible, Digitales oculto
    expect(sec_monedas).to_be_visible()
    expect(sec_digitales).to_be_hidden()
    expect(btn_monedas).to_have_class("btn btn-primary")
    expect(btn_digitales).to_have_class("btn btn-outline-primary")
    expect(sec_monedas.locator("thead th")).to_have_text(
        ["ID", "Moneda", "Símbolo", "Estado", "Acciones"]
    )

    # Cambiar a pestaña Monedas Digitales
    btn_digitales.click()
    expect(sec_monedas).to_be_hidden()
    expect(sec_digitales).to_be_visible()
    expect(btn_digitales).to_have_class("btn btn-primary")
    expect(btn_monedas).to_have_class("btn btn-outline-primary")
    expect(sec_digitales.locator("thead th")).to_have_text(
        ["ID", "Moneda Digital", "Símbolo", "Estado", "Acciones"]
    )


def test_ui_monedas_modal_dinamico_y_validaciones(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/monedas/gestion")

    modal = page.locator("#modalMoneda")

    # 1. Modal en modo Moneda física
    page.get_by_role("button", name="Nuevo Registro").click()
    expect(modal).to_be_visible()
    expect(page.locator("#modalTitulo")).to_have_text("Nueva Moneda")
    expect(page.locator("#nombre_registro")).to_have_attribute("name", "nombre_moneda")
    expect(page.locator("#estado_registro option")).to_have_text(["Activo", "Inactivo"])

    # Camino triste UI: campo nombre vacío no permite enviar
    page.locator("#formMoneda button[type='submit']").click()
    expect(modal).to_be_visible()
    assert page.locator("#nombre_registro").evaluate("el => el.checkValidity()") is False

    modal.get_by_role("button", name="Cancelar").click()
    expect(modal).to_be_hidden()

    # 2. Modal en modo Moneda Digital
    page.locator("#btnDigitales").click()
    page.get_by_role("button", name="Nuevo Registro").click()
    expect(modal).to_be_visible()
    expect(page.locator("#modalTitulo")).to_have_text("Nueva Moneda Digital")
    expect(page.locator("#nombre_registro")).to_have_attribute("name", "nombre_digital")
    expect(page.locator("#simbolo_registro")).to_have_attribute("name", "simbolo_digital")
    expect(page.locator("#estado_registro")).to_have_value("1")

    modal.get_by_role("button", name="Cancelar").click()
    expect(modal).to_be_hidden()