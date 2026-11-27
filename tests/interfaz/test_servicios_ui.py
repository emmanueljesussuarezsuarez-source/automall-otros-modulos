"""
Pruebas de Interfaz (UI / End-to-End) con Playwright — Módulo Servicios
Archivo: tests/ui/test_servicios_ui.py
Base de datos real de prueba: automall_test y seguridad_test
"""

from datetime import date
import re

from playwright.sync_api import expect

from models.servicios import Servicios
from tests.ui.conftest import obtener_conexion_negocio_test


def _hoy_str():
    """Retorna la fecha actual en formato YYYY-MM-DD."""
    return date.today().strftime("%Y-%m-%d")


def _crear_servicio_y_obtener_id(nombre_servicio, descripcion="Detalle inicial UI"):
    """Registra un servicio activo en automall_test y retorna su cod_servicios."""
    Servicios.guardar(
        nombre_servicio,
        "40.00",
        None,
        descripcion,
        _hoy_str(),
        "GH567IJ",
        "18998754",
    )
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT cod_servicios FROM servicios WHERE nombre_servicio = %s LIMIT 1",
            (nombre_servicio,),
        )
        fila = cursor.fetchone()
        return fila[0] if fila else None
    finally:
        cursor.close()
        conn.close()


def test_cp_ser_ui_01_login_exitoso(page, ui_base_url):
    """CP-SER-UI-01: La página de login carga y permite iniciar sesión."""
    page.goto(f"{ui_base_url}/login")
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()

    page.fill("#emailInput", "prueba@gmail.com")
    page.fill("#passwordInput", "12345678")

    boton = page.locator("#btnSubmit")
    expect(boton).to_be_enabled()
    boton.click()

    expect(page).to_have_url(f"{ui_base_url}/", timeout=10000)


def test_cp_ser_ui_02_pagina_crear_servicio_carga(admin_page, ui_base_url):
    """CP-SER-UI-02: La página de crear servicio carga correctamente."""
    admin_page.goto(f"{ui_base_url}/servicios")
    admin_page.click('a[href="/servicios/nuevo"]')

    expect(admin_page).to_have_url(f"{ui_base_url}/servicios/nuevo", timeout=10000)
    expect(admin_page.get_by_role("heading", name="Registrar Servicio")).to_be_visible()
    expect(admin_page.locator("#placa")).to_be_visible()
    expect(admin_page.locator("#nombre_servicio")).to_be_visible()
    expect(admin_page.locator("#costo_base")).to_be_visible()
    expect(admin_page.locator("#fecha_realizacion")).to_be_visible()
    expect(admin_page.locator("#descripcion_especifica")).to_be_visible()
    expect(admin_page.get_by_role("button", name="Guardar")).to_be_visible()


def test_cp_ser_ui_03_crear_servicio_y_mensaje_exito(admin_page, ui_base_url):
    """CP-SER-UI-03: Se puede crear un servicio, muestra éxito y redirige a la lista."""
    admin_page.goto(f"{ui_base_url}/servicios/nuevo")

    admin_page.select_option("#placa", "GH567IJ")
    admin_page.fill("#nombre_servicio", "Lavado General UI")
    admin_page.fill("#costo_base", "45.00")
    admin_page.fill("#fecha_realizacion", _hoy_str())
    admin_page.fill("#descripcion_especifica", "Lavado basico UI")
    admin_page.get_by_role("button", name="Guardar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/servicios", timeout=10000)
    alerta = admin_page.locator(".swal2-popup")
    expect(alerta).to_be_visible(timeout=10000)
    expect(alerta).to_contain_text("Servicio registrado correctamente.")
    expect(admin_page.locator("#tablaServicios")).to_contain_text("Lavado General UI")


def test_cp_ser_ui_04_lista_muestra_servicios(admin_page, ui_base_url):
    """CP-SER-UI-04: La lista de servicios muestra los registros correctamente."""
    _crear_servicio_y_obtener_id("Diagnostico UI Listado", "Revision general")

    admin_page.set_viewport_size({"width": 1600, "height": 900})
    admin_page.goto(f"{ui_base_url}/servicios")
    tabla = admin_page.locator("#tablaServicios")

    expect(tabla).to_be_visible(timeout=5000)
    expect(tabla).to_contain_text("Diagnostico UI Listado")
    expect(tabla).to_contain_text("Activo")
    expect(tabla).to_contain_text("$40.00")
    expect(tabla).to_contain_text("GH567IJ")


def test_cp_ser_ui_05_editar_servicio_abre_formulario_y_actualiza(admin_page, ui_base_url):
    """CP-SER-UI-05: El botón de editar abre el formulario con datos cargados y actualiza."""
    _crear_servicio_y_obtener_id("Servicio Original UI", "Detalle inicial UI")

    admin_page.set_viewport_size({"width": 1600, "height": 900})
    admin_page.goto(f"{ui_base_url}/servicios")
    fila = admin_page.locator("#tablaServicios tbody tr", has_text="Servicio Original UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator('a[href^="/servicios/editar/"]').click()
    expect(admin_page).to_have_url(re.compile(r"/servicios/editar/\d+$"), timeout=10000)
    expect(admin_page.get_by_role("heading", name="Editar Servicio")).to_be_visible()

    expect(admin_page.locator("#nombre_servicio")).to_have_value("Servicio Original UI")
    expect(admin_page.locator("#descripcion_especifica")).to_have_value("Detalle inicial UI")

    admin_page.locator("#nombre_servicio").fill("Servicio Editado UI")
    admin_page.locator("#costo_base").fill("75.00")
    admin_page.locator("#descripcion_especifica").fill("Detalle editado UI")
    admin_page.get_by_role("button", name="Actualizar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/servicios", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Servicio actualizado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaServicios")).to_contain_text("Servicio Editado UI")


def test_cp_ser_ui_06_finalizar_servicio_desde_boton(admin_page, ui_base_url):
    """CP-SER-UI-06: El botón de finalizar registra costo final y actualiza el estado."""
    _crear_servicio_y_obtener_id("Servicio Finalizar UI", "Finalizar orden UI")

    admin_page.set_viewport_size({"width": 1600, "height": 900})
    admin_page.goto(f"{ui_base_url}/servicios")
    fila = admin_page.locator("#tablaServicios tbody tr", has_text="Servicio Finalizar UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-finalizar-servicio").click()

    alerta_costo = admin_page.locator(".swal2-popup")
    expect(alerta_costo).to_be_visible(timeout=5000)
    expect(alerta_costo).to_contain_text("Ingresar Costo Final")
    alerta_costo.locator(".swal2-input").fill("80.00")
    alerta_costo.locator(".swal2-confirm").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/servicios", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Servicio finalizado y vehículo reactivado.",
        timeout=10000,
    )

    fila_actualizada = admin_page.locator("#tablaServicios tbody tr", has_text="Servicio Finalizar UI")
    expect(fila_actualizada).to_contain_text("Finalizado")
    expect(fila_actualizada).to_contain_text("$80.00")


def test_cp_ser_ui_07_ver_recibo_servicio_finalizado(admin_page, ui_base_url):
    """CP-SER-UI-07: El botón Ver Recibo de Servicio abre el comprobante del servicio finalizado."""
    cod_servicios = _crear_servicio_y_obtener_id("Servicio Recibo UI", "Recibo servicio UI")
    assert cod_servicios is not None
    Servicios.finalizar(cod_servicios, "GH567IJ", "18998754", "95.00")

    admin_page.set_viewport_size({"width": 1600, "height": 900})
    admin_page.goto(f"{ui_base_url}/servicios")
    fila = admin_page.locator("#tablaServicios tbody tr", has_text="Servicio Recibo UI")
    expect(fila).to_be_visible(timeout=5000)

    btn_recibo = fila.locator('a[href^="/servicios/recibo/"]')
    expect(btn_recibo).to_be_visible()

    with admin_page.expect_popup(timeout=10000) as popup_info:
        btn_recibo.click()

    pagina_recibo = popup_info.value
    pagina_recibo.wait_for_load_state()

    expect(pagina_recibo).to_have_url(re.compile(rf"/servicios/recibo/{cod_servicios}$"))
    expect(pagina_recibo.get_by_text("RECIBO DE SERVICIO")).to_be_visible()
    expect(pagina_recibo.locator("body")).to_contain_text("Servicio Recibo UI")
    expect(pagina_recibo.locator("body")).to_contain_text("GH567IJ")
    pagina_recibo.close()


def test_cp_ser_ui_08_eliminar_desactiva_servicio_y_actualiza_lista(admin_page, ui_base_url):
    """CP-SER-UI-08: El botón de eliminar desactiva el servicio y actualiza la lista."""
    _crear_servicio_y_obtener_id("Servicio Eliminar UI", "Inactivar orden UI")

    admin_page.set_viewport_size({"width": 1600, "height": 900})
    admin_page.goto(f"{ui_base_url}/servicios")
    fila = admin_page.locator("#tablaServicios tbody tr", has_text="Servicio Eliminar UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-eliminar-servicio").click()

    confirmacion = admin_page.locator(".swal2-popup")
    expect(confirmacion).to_be_visible(timeout=5000)
    expect(confirmacion).to_contain_text("¿Deseas eliminar este servicio?")
    confirmacion.locator(".swal2-confirm").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/servicios", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Servicio inactivado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaServicios")).not_to_contain_text("Servicio Eliminar UI")


def test_cp_ser_ui_09_boton_reporte_abre_modal_y_genera_pdf(admin_page, ui_base_url):
    """CP-SER-UI-09: El botón Reporte abre el modal de filtros y genera el reporte PDF."""
    _crear_servicio_y_obtener_id("Servicio Reporte UI", "Reporte activo UI")

    admin_page.goto(f"{ui_base_url}/servicios")
    admin_page.click('button[data-bs-target="#modalReporteServicios"]')

    modal = admin_page.locator("#modalReporteServicios")
    expect(modal).to_be_visible(timeout=5000)
    expect(modal.locator("#nombre_servicio_reporte")).to_be_visible()
    expect(modal.locator("#estado_reporte")).to_be_visible()
    expect(modal.locator("#placa_reporte")).to_be_visible()

    with admin_page.context.expect_event(
        "response",
        predicate=lambda r: "/servicios/reporte/generar" in r.url,
        timeout=10000,
    ) as respuesta_info:
        modal.get_by_role("button", name="Descargar PDF").click()

    respuesta_pdf = respuesta_info.value
    assert respuesta_pdf.status == 200
    assert "application/pdf" in respuesta_pdf.headers.get("content-type", "")


def test_cp_ser_ui_10_sin_sesion_redirige_login(page, ui_base_url):
    """CP-SER-UI-10: Un usuario sin sesión es redirigido a la página de login."""
    page.goto(f"{ui_base_url}/servicios")

    expect(page).to_have_url(f"{ui_base_url}/login", timeout=10000)
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()