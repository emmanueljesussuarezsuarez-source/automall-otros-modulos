import random
import re
from playwright.sync_api import Page, expect
from .conftest import BASE_URL, iniciar_sesion


def _seleccionar_moneda_usd(page: Page):
    moneda_val = page.locator("#cod_moneda").evaluate(
        """sel => {
            const opts = Array.from(sel.options);
            const usd = opts.find(o => /usd|dolar|dólar/i.test(o.textContent));
            return usd ? usd.value : (opts[0] ? opts[0].value : '');
        }"""
    )
    if moneda_val:
        page.locator("#cod_moneda").select_option(moneda_val)


def _seleccionar_primer_banco(page: Page):
    banco_val = page.locator("#cod_banco").evaluate(
        "sel => { const o = Array.from(sel.options).find(x => x.value && !x.disabled); return o ? o.value : ''; }"
    )
    if banco_val:
        page.locator("#cod_banco").select_option(banco_val)


def test_aceptacion_pagos_flujo_completo_y_cambio_estados_cruzados(page: Page):
    """
    Flujo transaccional End-to-End completo:
    1. Admin registra venta a crédito (2 cuotas) -> Venta queda Pendiente.
    2. Camino triste: intentar pagar un monto mayor al saldo pendiente es rechazado.
    3. Admin registra Pago 1 (Cuota #1 por Transferencia) -> Cuota #1 pasa a Pagada, cuenta sigue Pendiente.
    4. Admin registra Pago 2 (Cuota #2 en Efectivo) -> Cuenta pasa a Pagado y Venta pasa a Completado.
    5. Admin anula Pago 2 -> Pago pasa a Anulado, Cuota #2 vuelve a Pendiente, Cuenta y Venta vuelven a Pendiente.
    6. Cliente verifica su historial, cronograma y detalle del pago anulado.
    7. Limpieza: Admin anula Pago 1 y la Venta de prueba para devolver el vehículo a Disponible.
    """
    page.on("popup", lambda popup: popup.close())
    ref_unica = f"REFP{random.randint(10000, 99999)}"

    # 1. INICIAR SESIÓN COMO ADMIN Y CREAR VENTA A CRÉDITO (2 CUOTAS)
    iniciar_sesion(page, "prueba@gmail.com", "12345678")
    page.goto(f"{BASE_URL}/ventas/registrar_venta")

    page.locator("#select_cliente_lista").select_option("29880513")
    expect(page.locator("#id_cliente_hidden")).to_have_value("29880513")
    page.locator("#btn_ir_paso_2").click()

    opciones_v = page.locator("#select_vehiculo_lista option:not([disabled])")
    assert opciones_v.count() > 0, "No hay vehículos disponibles para la prueba."
    placas = [opciones_v.nth(i).get_attribute("value") for i in range(opciones_v.count())]
    placa = "OP123QR" if "OP123QR" in placas else placas[0]

    page.locator("#select_vehiculo_lista").select_option(placa)
    expect(page.locator("#id_vehiculo_hidden")).to_have_value(placa)
    page.locator("#btn_ir_paso_3").click()

    page.locator("#tipo_operacion").select_option("credito")
    page.locator("#monto_recibido").fill("0")
    page.locator("#frecuencia_pago").select_option("Mensual")
    page.locator("#cantidad_cuotas").fill("2")
    page.locator("#tasa_interes").fill("0")
    page.locator("#btn-finalizar").click()

    expect(page.locator(".swal2-title")).to_have_text("Éxito")
    page.locator(".swal2-confirm").click()
    page.wait_for_url(f"{BASE_URL}/ventas/lista_ventas")

    # 2. IR A REGISTRAR PAGO Y PROBAR CAMINO TRISTE (MONTO MAYOR AL SALDO)
    page.goto(f"{BASE_URL}/pagos/registrar_pago")
    page.locator("#cedula_cliente").select_option("29880513")

    opcion_cuenta = page.locator("#cod_cuentas option", has_text=placa)
    expect(opcion_cuenta).to_be_attached()
    cod_cuenta = opcion_cuenta.get_attribute("value")
    page.locator("#cod_cuentas").select_option(cod_cuenta)

    expect(page.locator("#bloque_cuotas_cuenta")).to_be_visible()
    expect(page.locator("#tbody_cuotas_cuenta tr")).to_have_count(2)

    # Camino triste: monto excede saldo
    page.locator("#cod_metodo").select_option("2")  # Efectivo
    _seleccionar_moneda_usd(page)
    page.locator("#monto_pago").fill("999999.00")
    page.locator("#btn-procesar").click()
    expect(page.locator("#monto_pago")).to_have_class(re.compile(r"is-invalid"))

    # 3. PAGAR CUOTA #1 (TRANSFERENCIA BANCARIA) -> CUOTA #1 PAGADA, CUENTA PENDIENTE
    page.locator("#tbody_cuotas_cuenta .btn-elegir-cuota").nth(0).click()
    page.locator("#cod_metodo").select_option("5")  # Transferencia
    _seleccionar_moneda_usd(page)
    _seleccionar_primer_banco(page)
    page.locator("#referencia").fill(ref_unica)
    page.locator("#descripcion").fill("Pago cuota uno prueba")
    page.locator("#btn-procesar").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Pago registrado!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    # Verificar estado en listar_admin
    page.goto(f"{BASE_URL}/pagos/listar_admin")
    page.locator("#inputBuscarPlaca").fill(placa)
    fila_p1 = page.locator("tr.fila-pago:visible", has_text=ref_unica).first
    expect(fila_p1).to_be_visible()
    expect(fila_p1).to_contain_text("Pendiente")

    page.locator("#tab-admin-cuotas-btn").click()
    cuota1_pagada = page.locator(
        f"tr.fila-cuota-admin[data-placa='{placa}'][data-estado='pagada']:visible",
        has_text="#1 / 2",
    ).first
    cuota2_pendiente = page.locator(
        f"tr.fila-cuota-admin[data-placa='{placa}'][data-estado='pendiente']:visible",
        has_text="#2 / 2",
    ).first
    expect(cuota1_pagada).to_be_visible()
    expect(cuota2_pendiente).to_be_visible()

    # 4. PAGAR CUOTA #2 (EFECTIVO) -> CUENTA PASA A PAGADO Y VENTA A COMPLETADO
    page.goto(f"{BASE_URL}/pagos/registrar_pago")
    page.locator("#cedula_cliente").select_option("29880513")
    expect(page.locator("#cod_cuentas option", has_text=placa)).to_be_attached()
    page.locator("#cod_cuentas").select_option(cod_cuenta)
    expect(page.locator("#bloque_cuotas_cuenta")).to_be_visible()

    page.locator("#tbody_cuotas_cuenta .btn-elegir-cuota").first.click()
    page.locator("#cod_metodo").select_option("2")  # Efectivo
    _seleccionar_moneda_usd(page)
    page.locator("#descripcion").fill("Pago cuota dos final")
    page.locator("#btn-procesar").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Pago registrado!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    # Verificar cuenta en Pagado
    page.goto(f"{BASE_URL}/pagos/listar_admin")
    page.locator("#inputBuscarPlaca").fill(placa)
    fila_p1_pagado = page.locator("tr.fila-pago:visible", has_text=ref_unica).first
    expect(fila_p1_pagado).to_contain_text("Pagado")
    expect(fila_p1_pagado).to_contain_text("Restan: $0.00")

    # Verificar cambio de estado cruzado en VENTAS -> Completado
    page.goto(f"{BASE_URL}/ventas/lista_ventas")
    page.locator("#inputPlaca").fill(placa)
    fila_venta = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila_venta).to_contain_text("Completado")
    expect(fila_venta).to_contain_text("2/2 cuotas")

    # 5. ANULAR PAGO 2 -> CUOTA #2 VUELVE A PENDIENTE, CUENTA Y VENTA VUELVEN A PENDIENTE
    page.goto(f"{BASE_URL}/pagos/listar_admin")
    page.locator("#inputBuscarPlaca").fill(placa)
    fila_efectivo = (
        page.locator("tr.fila-pago:visible", has_text="Efectivo")
        .filter(has=page.locator("button[title='Anular Pago']"))
        .first
    )
    fila_efectivo.locator("button[title='Anular Pago']").click()

    modal_anular = page.locator("#modalAnularPago")
    expect(modal_anular).to_be_visible()
    page.locator("#motivo_anulacion").fill("Error de prueba de aceptacion")
    modal_anular.locator("button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    page.locator("#inputBuscarPlaca").fill(placa)
    expect(page.locator("tr.fila-pago:visible", has_text="Efectivo").first).to_contain_text("Anulado")
    expect(page.locator("tr.fila-pago:visible", has_text=ref_unica).first).to_contain_text("Pendiente")

    # Cuota #2 revertida a Pendiente
    page.locator("#tab-admin-cuotas-btn").click()
    expect(
        page.locator(
            f"tr.fila-cuota-admin[data-placa='{placa}'][data-estado='pagada']:visible",
            has_text="#1 / 2",
        ).first
    ).to_be_visible()
    expect(
        page.locator(
            f"tr.fila-cuota-admin[data-placa='{placa}'][data-estado='pendiente']:visible",
            has_text="#2 / 2",
        ).first
    ).to_be_visible()

    # Venta revertida a Pendiente (1/2 cuotas)
    page.goto(f"{BASE_URL}/ventas/lista_ventas")
    page.locator("#inputPlaca").fill(placa)
    fila_venta = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila_venta).to_contain_text("Pendiente")
    expect(fila_venta).to_contain_text("1/2 cuotas")

    # 6. VERIFICACIÓN COMO CLIENTE EN /pagos/listar_pagos
    page.goto(f"{BASE_URL}/logout")
    iniciar_sesion(page, "darye@gmail.com", "12345678")
    page.goto(f"{BASE_URL}/pagos/listar_pagos")

    expect(page.get_by_role("heading", name="Mis Pagos y Cuotas")).to_be_visible()
    page.locator("#selectorVehiculo").select_option(placa)
    expect(page.locator("tr.fila-pago:visible", has_text="Pago Anulado").first).to_be_visible()

    page.locator("#tab-cuotas-btn").click()
    expect(
        page.locator(f"tr.fila-cuota-cliente[data-placa='{placa}']:visible", has_text="Cuota #1 / 2")
        .filter(has_text="Pagada")
        .first
    ).to_be_visible()
    expect(
        page.locator(f"tr.fila-cuota-cliente[data-placa='{placa}']:visible", has_text="Cuota #2 / 2")
        .filter(has_text="Pendiente")
        .first
    ).to_be_visible()

    # 7. LIMPIEZA: ADMIN ANULA PAGO 1 Y ANULA VENTA PARA DEJAR VEHÍCULO DISPONIBLE
    page.goto(f"{BASE_URL}/logout")
    iniciar_sesion(page, "prueba@gmail.com", "12345678")

    page.goto(f"{BASE_URL}/pagos/listar_admin")
    page.locator("#inputBuscarPlaca").fill(placa)
    (
        page.locator("tr.fila-pago:visible", has_text=ref_unica)
        .filter(has=page.locator("button[title='Anular Pago']"))
        .first.locator("button[title='Anular Pago']")
        .click()
    )
    page.locator("#motivo_anulacion").fill("Limpieza de prueba")
    page.locator("#modalAnularPago button[type='submit']").click()
    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()

    page.goto(f"{BASE_URL}/ventas/lista_ventas")
    page.locator("#inputPlaca").fill(placa)
    (
        page.locator("tr.fila-venta:visible", has_text=placa)
        .filter(has=page.locator("button[title='Anular Venta']:not([disabled])"))
        .first.locator("button[title='Anular Venta']")
        .click()
    )
    page.locator(".modal.show button[type='submit']").click()
    page.locator(".swal2-confirm").click()
    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()


def test_aceptacion_pagos_admin_acceso_denegado_cliente(login_cliente: Page):
    """Camino triste: El cliente no puede acceder al panel administrativo de pagos."""
    page = login_cliente
    response = page.goto(f"{BASE_URL}/pagos/listar_admin")
    assert response.status in (401, 403) or "/pagos/listar_admin" not in page.url