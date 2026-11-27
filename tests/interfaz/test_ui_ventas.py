import re
from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def test_ui_ventas_wizard_pasos_y_navegacion_triste_y_feliz(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/ventas/registrar_venta")

    expect(page.get_by_role("heading", name="Registro de Ventas y Facturación")).to_be_visible()
    expect(page.locator("#step-1")).to_be_visible()
    expect(page.locator("#step-2")).to_be_hidden()
    expect(page.locator("#step-3")).to_be_hidden()

    # Camino triste Paso 1: intentar avanzar sin cliente muestra SweetAlert
    page.locator("#btn_ir_paso_2").click()
    expect(page.locator(".swal2-title")).to_have_text("Atención")
    expect(page.locator(".swal2-html-container")).to_contain_text("Debe identificar un cliente primero")
    page.locator(".swal2-confirm").click()
    expect(page.locator("#step-1")).to_be_visible()

    # Abrir y cerrar Modal de Cliente Rápido
    page.get_by_role("button", name="Registrar nuevo cliente").click()
    modal_cli = page.locator("#modalClienteRapido")
    expect(modal_cli).to_be_visible()
    expect(page.locator("#rapido_cedula")).to_be_visible()
    expect(page.locator("#rapido_password")).to_be_visible()
    modal_cli.get_by_role("button", name="Cancelar").click()
    expect(modal_cli).to_be_hidden()

    # Seleccionar cliente existente (29880513) y verificar ficha
    page.locator("#select_cliente_lista").select_option("29880513")
    expect(page.locator("#id_cliente_hidden")).to_have_value("29880513")
    expect(page.locator("#lbl_cliente_doc")).to_have_text("29880513")
    expect(page.locator("#lbl_cliente_nombre")).not_to_have_text("-")

    # Ir al Paso 2
    page.locator("#btn_ir_paso_2").click()
    expect(page.locator("#step-2")).to_be_visible()

    # Camino triste Paso 2: intentar avanzar sin vehículo
    page.locator("#btn_ir_paso_3").click()
    expect(page.locator(".swal2-title")).to_have_text("Atención")
    expect(page.locator(".swal2-html-container")).to_contain_text("Debe seleccionar un vehículo válido")
    page.locator(".swal2-confirm").click()
    expect(page.locator("#step-2")).to_be_visible()

    # Seleccionar primer vehículo disponible
    opciones_v = page.locator("#select_vehiculo_lista option:not([disabled])")
    assert opciones_v.count() > 0, "Debe existir al menos 1 vehículo disponible para la prueba."
    primera_placa = opciones_v.first.get_attribute("value")

    page.locator("#select_vehiculo_lista").select_option(primera_placa)
    expect(page.locator("#id_vehiculo_hidden")).to_have_value(primera_placa)
    expect(page.locator("#v_precio")).not_to_have_text("$ 0.00")

    # Ir al Paso 3
    page.locator("#btn_ir_paso_3").click()
    expect(page.locator("#step-3")).to_be_visible()


def test_ui_ventas_paso3_metodos_credito_y_validaciones(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/ventas/registrar_venta")

    # Llegar al Paso 3
    page.locator("#select_cliente_lista").select_option("29880513")
    expect(page.locator("#id_cliente_hidden")).to_have_value("29880513")
    page.locator("#btn_ir_paso_2").click()

    primera_placa = page.locator("#select_vehiculo_lista option:not([disabled])").first.get_attribute("value")
    page.locator("#select_vehiculo_lista").select_option(primera_placa)
    expect(page.locator("#id_vehiculo_hidden")).to_have_value(primera_placa)
    page.locator("#btn_ir_paso_3").click()

    # Dinámica de métodos de pago: Efectivo (2) oculta banco, digital y referencia
    page.locator("#cod_metodo").select_option("2")
    expect(page.locator("#wrapper_moneda")).to_be_visible()
    expect(page.locator("#wrapper_banco")).to_be_hidden()
    expect(page.locator("#wrapper_moneda_digital")).to_be_hidden()
    expect(page.locator("#wrapper_referencia")).to_be_hidden()

    # Transferencia (5) muestra banco y referencia
    page.locator("#cod_metodo").select_option("5")
    expect(page.locator("#wrapper_banco")).to_be_visible()
    expect(page.locator("#wrapper_referencia")).to_be_visible()
    expect(page.locator("#wrapper_moneda_digital")).to_be_hidden()

    # Binance (1) muestra moneda digital y oculta banco y moneda física
    page.locator("#cod_metodo").select_option("1")
    expect(page.locator("#wrapper_moneda_digital")).to_be_visible()
    expect(page.locator("#wrapper_banco")).to_be_hidden()
    expect(page.locator("#wrapper_moneda")).to_be_hidden()

    # Cambiar a Crédito: aparece bloque de cuotas y previsualización dinámica
    page.locator("#tipo_operacion").select_option("credito")
    expect(page.locator("#wrapper_credito")).to_be_visible()

    page.locator("#monto_recibido").fill("0")
    page.locator("#cantidad_cuotas").fill("4")
    page.locator("#tasa_interes").fill("10")
    expect(page.locator("#tbody_preview_cuotas tr")).to_have_count(4)
    expect(page.locator("#deuda_usd")).not_to_have_text("USD: $0.00")

    # Camino triste UI: inicial >= precio en modalidad crédito (con método seleccionado para que dispare validacion_venta.js)
    page.locator("#monto_recibido").fill("999999")
    page.locator("#cod_metodo").select_option("2")
    page.locator("#monto_recibido").fill("999999")
    page.locator("#cod_metodo").select_option("2")
    page.locator("#cod_moneda").select_option(index=0)
    page.locator("#btn-finalizar").click()
    expect(page.locator("#monto_recibido")).to_have_class(re.compile(r"is-invalid"))
    expect(page.locator("#step-3 .invalid-feedback").first).to_contain_text(
        "Si la inicial cubre el 100% del vehículo, seleccione venta de Contado."
    )


def test_ui_ventas_listado_estructura_y_busqueda(login_admin: Page):
    page = login_admin
    page.goto(f"{BASE_URL}/ventas/lista_ventas")

    expect(page.get_by_role("heading", name="Historial de Ventas")).to_be_visible()
    expect(page.get_by_role("link", name="Registrar Venta")).to_be_visible()
    expect(page.locator("#inputPlaca")).to_be_visible()

    expect(page.locator("#tablaVentas thead th")).to_have_text(
        ["ID", "Fecha", "Cliente", "Vehículo", "Modalidad", "Deuda Total", "Último Abono", "Saldo Pendiente", "Estado", "Acciones"]
    )

    # Filtro por placa inexistente (ventas_listado.js usa evento keyup)
    page.locator("#inputPlaca").fill("PLACAINEXISTENTE999")
    page.locator("#inputPlaca").dispatch_event("keyup")
    expect(page.locator("#infoPaginacion")).to_have_text("Mostrando 0 de 0 ventas")