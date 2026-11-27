import re
from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def test_ui_pagos_registrar_elementos_y_metodos_dinamicos(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/pagos/registrar_pago")

    expect(page.get_by_role("heading", name="Registrar Pago / Abono de Cuenta")).to_be_visible()
    expect(page.locator("#lbl_tasa")).to_be_visible()
    expect(page.locator("#btn-actualizar-tasa")).to_be_visible()
    expect(page.locator("#cedula_cliente")).to_be_visible()
    expect(page.locator("#cod_cuentas")).to_be_visible()
    expect(page.locator("#monto_pago")).to_be_visible()
    expect(page.locator("#lbl_nuevo_saldo")).to_be_visible()

    # Método Efectivo (2): oculta banco y digital, deshabilita referencia
    page.locator("#cod_metodo").select_option("2")
    expect(page.locator("#wrapper_moneda")).to_be_visible()
    expect(page.locator("#div_banco")).to_be_hidden()
    expect(page.locator("#wrapper_moneda_digital")).to_be_hidden()
    expect(page.locator("#referencia")).to_be_disabled()

    # Método Transferencia Bancaria (5): muestra banco y habilita referencia
    page.locator("#cod_metodo").select_option("5")
    expect(page.locator("#wrapper_moneda")).to_be_visible()
    expect(page.locator("#div_banco")).to_be_visible()
    expect(page.locator("#wrapper_moneda_digital")).to_be_hidden()
    expect(page.locator("#referencia")).to_be_enabled()

    # Método Digital Binance (1): muestra billetera digital, oculta moneda física y banco
    page.locator("#cod_metodo").select_option("1")
    expect(page.locator("#wrapper_moneda_digital")).to_be_visible()
    expect(page.locator("#wrapper_moneda")).to_be_hidden()
    expect(page.locator("#div_banco")).to_be_hidden()
    expect(page.locator("#referencia")).to_be_enabled()


def test_ui_pagos_validacion_campos_obligatorios(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/pagos/registrar_pago")

    # Camino triste UI: enviar sin seleccionar cuenta ni monto
    page.locator("#cod_metodo").select_option("2")
    page.locator("#btn-procesar").evaluate("btn => btn.closest('form').noValidate = true")
    page.locator("#btn-procesar").click()

    expect(page.locator("#cod_cuentas")).to_have_class(re.compile(r"is-invalid"))
    expect(page.locator("#monto_pago")).to_have_class(re.compile(r"is-invalid"))


def test_ui_pagos_listar_admin_pestanas_y_filtros(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/pagos/listar_admin")

    expect(page.get_by_role("heading", name="Control General de Pagos y Cuotas")).to_be_visible()
    expect(page.locator("#inputBuscarPlaca")).to_be_visible()
    expect(page.get_by_role("link", name="Registrar Pago")).to_be_visible()

    # Pestaña 1 visible por defecto
    expect(page.locator("#pane-admin-pagos")).to_be_visible()
    expect(page.locator("#pane-admin-cuotas")).to_be_hidden()

    # Cambiar a pestaña Control de Cuotas y Cobranza
    page.locator("#tab-admin-cuotas-btn").click()
    expect(page.locator("#pane-admin-cuotas")).to_be_visible()
    expect(page.locator("#filtroEstadoCuotaAdmin")).to_be_visible()
    expect(page.locator("#filtroEstadoCuotaAdmin option")).to_have_text(
        ["Todos los estados", "Vencidas", "Pendientes", "Parciales", "Pagadas"]
    )