from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def _obtener_placa_disponible(page: Page, preferida: str = "") -> str:
    opciones = page.locator("#select_vehiculo_lista option:not([disabled])")
    assert opciones.count() > 0, "No hay vehículos disponibles en inventario."
    placas = [opciones.nth(i).get_attribute("value") for i in range(opciones.count())]
    if preferida and preferida in placas:
        return preferida
    return placas[0]


def test_aceptacion_venta_contado_y_anulacion_libera_vehiculo(login_admin: Page):
    """
    Criterio: Registrar venta de contado, validar que aparezca Completada y el vehículo salga
    del inventario disponible; luego anularla y validar que el vehículo regrese a Disponible.
    """
    page = login_admin
    # Evitar que el window.open del PDF robe foco
    page.on("popup", lambda popup: popup.close())

    page.goto(f"{BASE_URL}/ventas/registrar_venta")

    # Paso 1: Cliente
    page.locator("#select_cliente_lista").select_option("29880513")
    expect(page.locator("#id_cliente_hidden")).to_have_value("29880513")
    page.locator("#btn_ir_paso_2").click()

    # Paso 2: Vehículo disponible (preferiblemente GH567IJ)
    placa = _obtener_placa_disponible(page, "GH567IJ")
    page.locator("#select_vehiculo_lista").select_option(placa)
    expect(page.locator("#id_vehiculo_hidden")).to_have_value(placa)
    page.locator("#tiene_poder").check()
    page.locator("#traspaso_papel").check()
    page.locator("#btn_ir_paso_3").click()

    # Paso 3: Contado en Efectivo (cod_metodo = 2)
    page.locator("#tipo_operacion").select_option("contado")
    page.locator("#cod_metodo").select_option("2")
    page.locator("#btn-finalizar").click()

    expect(page.locator(".swal2-title")).to_have_text("Éxito")
    page.locator(".swal2-confirm").click()
    page.wait_for_url(f"{BASE_URL}/ventas/lista_ventas")

    # Verificar en Historial de Ventas
    page.locator("#inputPlaca").fill(placa)
    fila = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila).to_be_visible()
    expect(fila).to_contain_text("Contado")
    expect(fila).to_contain_text("Completado")

    # Verificar cambio de estado en inventario: vehículo ya no aparece disponible
    page.goto(f"{BASE_URL}/ventas/registrar_venta")
    placas_restantes = page.locator(f"#select_vehiculo_lista option[value='{placa}']")
    expect(placas_restantes).to_have_count(0)

    # Anular venta y verificar que libera el vehículo
    page.goto(f"{BASE_URL}/ventas/lista_ventas")
    page.locator("#inputPlaca").fill(placa)
    fila = page.locator("tr.fila-venta:visible", has_text=placa).first
    fila.locator("button[title='Anular Venta']").click()

    modal_anular = page.locator(".modal.show")
    expect(modal_anular).to_be_visible()
    modal_anular.locator("button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¿Confirmar Anulación?")
    page.locator(".swal2-confirm").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    page.locator("#inputPlaca").fill(placa)
    fila_anulada = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila_anulada).to_contain_text("Anulada")
    expect(fila_anulada.locator("button[title='Anular Venta']")).to_be_disabled()

    # Verificar que el vehículo volvió a estar Disponible
    page.goto(f"{BASE_URL}/ventas/registrar_venta")
    expect(page.locator(f"#select_vehiculo_lista option[value='{placa}']")).to_have_count(1)


def test_aceptacion_venta_credito_crear_editar_y_anular(login_admin: Page):
    """
    Criterio: Registrar venta a crédito con cronograma de cuotas, editar plan de cuotas y luego anular.
    """
    page = login_admin
    page.on("popup", lambda popup: popup.close())

    page.goto(f"{BASE_URL}/ventas/registrar_venta")

    page.locator("#select_cliente_lista").select_option("29880513")
    expect(page.locator("#id_cliente_hidden")).to_have_value("29880513")
    page.locator("#btn_ir_paso_2").click()

    placa = _obtener_placa_disponible(page, "KL890MN")
    page.locator("#select_vehiculo_lista").select_option(placa)
    expect(page.locator("#id_vehiculo_hidden")).to_have_value(placa)
    page.locator("#btn_ir_paso_3").click()

    # Configurar crédito sin inicial, 3 cuotas mensuales
    page.locator("#tipo_operacion").select_option("credito")
    page.locator("#monto_recibido").fill("0")
    page.locator("#frecuencia_pago").select_option("Mensual")
    page.locator("#cantidad_cuotas").fill("3")
    page.locator("#tasa_interes").fill("0")
    expect(page.locator("#tbody_preview_cuotas tr")).to_have_count(3)

    page.locator("#btn-finalizar").click()
    expect(page.locator(".swal2-title")).to_have_text("Éxito")
    page.locator(".swal2-confirm").click()
    page.wait_for_url(f"{BASE_URL}/ventas/lista_ventas")

    page.locator("#inputPlaca").fill(placa)
    fila = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila).to_contain_text("Crédito")
    expect(fila).to_contain_text("0/3 cuotas")
    expect(fila).to_contain_text("Pendiente")

    # Abrir detalle y verificar cronograma de 3 cuotas
    fila.locator("button[title='Ver Detalles']").click()
    modal_det = page.locator(".modal.show")
    expect(modal_det).to_be_visible()
    expect(modal_det.locator("tbody tr")).to_have_count(3)
    modal_det.get_by_role("button", name="Cerrar").click()
    expect(modal_det).to_be_hidden()

    # Editar plan de cuotas a 4 cuotas
    fila.locator("button[title='Editar Venta']").click()
    modal_edit = page.locator(".modal.show")
    expect(modal_edit).to_be_visible()
    modal_edit.locator("input[name='cantidad_cuotas']").fill("4")
    modal_edit.locator("button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¿Guardar cambios?")
    page.locator(".swal2-confirm").click()
    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    page.locator("#inputPlaca").fill(placa)
    fila_editada = page.locator("tr.fila-venta:visible", has_text=placa).first
    expect(fila_editada).to_contain_text("0/4 cuotas")

    # Limpieza: Anular venta para devolver el vehículo a Disponible
    fila_editada.locator("button[title='Anular Venta']").click()
    page.locator(".modal.show button[type='submit']").click()
    page.locator(".swal2-confirm").click()
    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()


def test_aceptacion_ventas_acceso_denegado_cliente(login_cliente: Page):
    """Camino triste: Un cliente no debe acceder al historial administrativo de ventas."""
    page = login_cliente
    response = page.goto(f"{BASE_URL}/ventas/lista_ventas")
    assert response.status in (401, 403) or "/ventas/lista_ventas" not in page.url