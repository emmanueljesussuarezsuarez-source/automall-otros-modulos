"""
Pruebas de Interfaz (UI / End-to-End) con Playwright — Módulo Mantenimiento Operacional
Archivo: tests/ui/test_mantenimiento_operacional_ui.py
Base de datos real de prueba: automall_test y seguridad_test
"""

from datetime import date
import re

from playwright.sync_api import expect

from models.mantenimiento_operacional import MantenimientoOperacional
from models.taller import Taller
from tests.ui.conftest import obtener_conexion_negocio_test


def _hoy_str():
    """Retorna la fecha actual en formato YYYY-MM-DD."""
    return date.today().strftime("%Y-%m-%d")


def _crear_taller_activo_ui(nombre="Taller UI Mant"):
    """Crea un taller activo en automall_test y retorna su cod_taller."""
    Taller.guardar(nombre, "Avenida Principal Local 10", "1", "18998754")
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT cod_taller FROM taller WHERE nombre_taller = %s LIMIT 1",
            (nombre,),
        )
        fila = cursor.fetchone()
        return fila[0] if fila else None
    finally:
        cursor.close()
        conn.close()


def _crear_mantenimiento_y_obtener_id(descripcion="Mantto inicial UI", cod_taller=None):
    """Registra un mantenimiento activo en automall_test y retorna su cod_mantenimiento."""
    if cod_taller is None:
        cod_taller = _crear_taller_activo_ui()

    MantenimientoOperacional.guardar(
        descripcion,
        "18998754",
        "Preventivo",
        _hoy_str(),
        None,
        "GH567IJ",
        str(cod_taller),
        "18998754",
        costo_base=150.0,
        costo_final=None,
        detalles=[{"descripcion_detalle": "Filtro aceite UI", "cantidad": 2}],
    )

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT cod_mantenimiento FROM mantenimiento WHERE descripcion_general = %s LIMIT 1",
            (descripcion,),
        )
        fila = cursor.fetchone()
        return fila[0] if fila else None
    finally:
        cursor.close()
        conn.close()


def test_cp_man_ui_01_login_exitoso(page, ui_base_url):
    """CP-MAN-UI-01: La página de login carga y permite iniciar sesión."""
    page.goto(f"{ui_base_url}/login")
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()

    page.fill("#emailInput", "prueba@gmail.com")
    page.fill("#passwordInput", "12345678")

    boton = page.locator("#btnSubmit")
    expect(boton).to_be_enabled()
    boton.click()

    expect(page).to_have_url(f"{ui_base_url}/", timeout=10000)


def test_cp_man_ui_02_pagina_crear_mantenimiento_carga(admin_page, ui_base_url):
    """CP-MAN-UI-02: La página de crear mantenimiento operacional carga correctamente."""
    _crear_taller_activo_ui()

    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    admin_page.click('a[href="/mantenimiento-operacional/crear"]')

    expect(admin_page).to_have_url(f"{ui_base_url}/mantenimiento-operacional/crear", timeout=10000)
    expect(admin_page.get_by_role("heading", name="Registrar Mantenimiento Operacional")).to_be_visible()
    expect(admin_page.locator("#placa")).to_be_visible()
    expect(admin_page.locator("#cod_taller")).to_be_visible()
    expect(admin_page.locator("#quien_autoriza")).to_be_visible()
    expect(admin_page.locator("#tipo")).to_be_visible()
    expect(admin_page.locator("#fecha_solicitud")).to_be_visible()
    expect(admin_page.locator("#descripcion_general")).to_be_visible()
    expect(admin_page.get_by_role("button", name="Guardar")).to_be_visible()


def test_cp_man_ui_03_crear_mantenimiento_y_mensaje_exito(admin_page, ui_base_url):
    """CP-MAN-UI-03: Se puede crear un mantenimiento, muestra éxito y redirige a la lista."""
    cod_taller = _crear_taller_activo_ui()
    assert cod_taller is not None

    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional/crear")

    admin_page.select_option("#placa", "GH567IJ")
    admin_page.select_option("#cod_taller", str(cod_taller))
    admin_page.select_option("#quien_autoriza", "18998754")
    admin_page.select_option("#tipo", "Preventivo")
    admin_page.fill("#fecha_solicitud", _hoy_str())
    admin_page.fill("#descripcion_general", "Mantto preventivo UI")
    admin_page.fill("#costo_base", "150.00")
    admin_page.fill('input[name="descripcion_detalle_0"]', "Filtro aceite UI")
    admin_page.fill('input[name="cantidad_0"]', "2")
    admin_page.get_by_role("button", name="Guardar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/mantenimiento-operacional", timeout=10000)
    alerta = admin_page.locator(".swal2-popup")
    expect(alerta).to_be_visible(timeout=10000)
    expect(alerta).to_contain_text("Mantenimiento registrado correctamente.")
    expect(admin_page.locator("#tablaMantenimientoOperacional")).to_contain_text("Mantto preventivo UI")


def test_cp_man_ui_04_lista_muestra_mantenimientos(admin_page, ui_base_url):
    """CP-MAN-UI-04: La lista de mantenimientos muestra los registros correctamente."""
    _crear_mantenimiento_y_obtener_id("Mantto listado UI")

    admin_page.set_viewport_size({"width": 1920, "height": 1080})
    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    tabla = admin_page.locator("#tablaMantenimientoOperacional")

    expect(tabla).to_be_visible(timeout=5000)
    expect(tabla).to_contain_text("Mantto listado UI")
    expect(tabla).to_contain_text("Activo")
    expect(tabla).to_contain_text("Preventivo")
    expect(tabla).to_contain_text("GH567IJ")
    expect(tabla).to_contain_text("Taller UI Mant")


def test_cp_man_ui_05_editar_mantenimiento_abre_formulario_y_actualiza(admin_page, ui_base_url):
    """CP-MAN-UI-05: El botón de editar abre el formulario con datos cargados y actualiza."""
    _crear_mantenimiento_y_obtener_id("Mantto original UI")

    admin_page.set_viewport_size({"width": 1920, "height": 1080})
    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    fila = admin_page.locator("#tablaMantenimientoOperacional tbody tr", has_text="Mantto original UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator('a[href^="/mantenimiento-operacional/editar/"]').click()
    expect(admin_page).to_have_url(re.compile(r"/mantenimiento-operacional/editar/\d+$"), timeout=10000)
    expect(admin_page.get_by_role("heading", name="Editar Mantenimiento Operacional")).to_be_visible()

    expect(admin_page.locator("#descripcion_general")).to_have_value("Mantto original UI")
    expect(admin_page.locator('input[name="descripcion_detalle_0"]')).to_have_value("Filtro aceite UI")

    admin_page.locator("#descripcion_general").fill("Mantto editado UI")
    admin_page.select_option("#tipo", "Correctivo")
    admin_page.locator("#costo_base").fill("220.00")
    admin_page.locator('input[name="descripcion_detalle_0"]').fill("Pastillas freno UI")
    admin_page.locator('input[name="cantidad_0"]').fill("4")
    admin_page.get_by_role("button", name="Actualizar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/mantenimiento-operacional", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Mantenimiento actualizado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaMantenimientoOperacional")).to_contain_text("Mantto editado UI")


def test_cp_man_ui_06_finalizar_mantenimiento_desde_modal(admin_page, ui_base_url):
    """CP-MAN-UI-06: El botón de finalizar abre confirmación, modal y cierra la orden."""
    _crear_mantenimiento_y_obtener_id("Mantto finalizar UI")

    admin_page.set_viewport_size({"width": 1920, "height": 1080})
    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    fila = admin_page.locator("#tablaMantenimientoOperacional tbody tr", has_text="Mantto finalizar UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-finalizar-mantenimiento").click()

    confirmacion = admin_page.locator(".swal2-popup")
    expect(confirmacion).to_be_visible(timeout=5000)
    expect(confirmacion).to_contain_text("¿Deseas finalizar este mantenimiento?")
    confirmacion.locator(".swal2-confirm").click()

    expect(admin_page).to_have_url(
        re.compile(r"/mantenimiento-operacional/finalizar/\d+/GH567IJ$"),
        timeout=10000,
    )
    modal = admin_page.locator("#modalFinalizar")
    expect(modal).to_be_visible(timeout=5000)

    modal.locator("#costo_final").fill("250.00")
    modal.get_by_role("button", name="Finalizar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/mantenimiento-operacional", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Mantenimiento finalizado correctamente.",
        timeout=10000,
    )

    fila_actualizada = admin_page.locator("#tablaMantenimientoOperacional tbody tr", has_text="Mantto finalizar UI")
    expect(fila_actualizada).to_contain_text("Finalizado")
    expect(fila_actualizada).to_contain_text("$250.00")


def test_cp_man_ui_07_ver_recibo_mantenimiento_finalizado(admin_page, ui_base_url):
    """CP-MAN-UI-07: El botón Ver Recibo abre el comprobante del mantenimiento finalizado."""
    cod_mantenimiento = _crear_mantenimiento_y_obtener_id("Mantto recibo UI")
    assert cod_mantenimiento is not None
    MantenimientoOperacional.finalizar(cod_mantenimiento, "GH567IJ", "18998754", costo_final=275.0)

    admin_page.set_viewport_size({"width": 1920, "height": 1080})
    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    fila = admin_page.locator("#tablaMantenimientoOperacional tbody tr", has_text="Mantto recibo UI")
    expect(fila).to_be_visible(timeout=5000)

    btn_recibo = fila.locator('a[href^="/mantenimiento-operacional/ver-recibo/"]')
    expect(btn_recibo).to_be_visible()

    with admin_page.expect_popup(timeout=10000) as popup_info:
        btn_recibo.click()

    pagina_recibo = popup_info.value
    pagina_recibo.wait_for_load_state()

    expect(pagina_recibo).to_have_url(
        re.compile(rf"/mantenimiento-operacional/ver-recibo/{cod_mantenimiento}$")
    )
    expect(pagina_recibo.get_by_text("RECIBO DE MANTENIMIENTO")).to_be_visible()
    expect(pagina_recibo.locator("body")).to_contain_text("Mantto recibo UI")
    expect(pagina_recibo.locator("body")).to_contain_text("GH567IJ")
    pagina_recibo.close()


def test_cp_man_ui_08_eliminar_desactiva_mantenimiento_y_actualiza_lista(admin_page, ui_base_url):
    """CP-MAN-UI-08: El botón de eliminar desactiva el mantenimiento y actualiza la lista."""
    _crear_mantenimiento_y_obtener_id("Mantto eliminar UI")

    admin_page.set_viewport_size({"width": 1920, "height": 1080})
    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    fila = admin_page.locator("#tablaMantenimientoOperacional tbody tr", has_text="Mantto eliminar UI")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-eliminar-mantenimiento").click()

    confirmacion = admin_page.locator(".swal2-popup")
    expect(confirmacion).to_be_visible(timeout=5000)
    expect(confirmacion).to_contain_text("¿Deseas eliminar este mantenimiento?")
    confirmacion.locator(".swal2-confirm").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/mantenimiento-operacional", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Mantenimiento inactivado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaMantenimientoOperacional")).not_to_contain_text("Mantto eliminar UI")


def test_cp_man_ui_09_boton_reporte_abre_modal_y_genera_pdf(admin_page, ui_base_url):
    """CP-MAN-UI-09: El botón Reporte abre el modal de filtros y genera el reporte PDF."""
    _crear_mantenimiento_y_obtener_id("Mantto reporte UI")

    admin_page.goto(f"{ui_base_url}/mantenimiento-operacional")
    admin_page.click('button[data-bs-target="#modalReporteMantenimiento"]')

    modal = admin_page.locator("#modalReporteMantenimiento")
    expect(modal).to_be_visible(timeout=5000)
    expect(modal.locator("#placa")).to_be_visible()
    expect(modal.locator("#estado")).to_be_visible()
    expect(modal.locator("#cod_taller")).to_be_visible()

    with admin_page.context.expect_event(
        "response",
        predicate=lambda r: "/mantenimiento-operacional/reporte/generar" in r.url,
        timeout=10000,
    ) as respuesta_info:
        modal.get_by_role("button", name="Descargar PDF").click()

    respuesta_pdf = respuesta_info.value
    assert respuesta_pdf.status == 200
    assert "application/pdf" in respuesta_pdf.headers.get("content-type", "")


def test_cp_man_ui_10_sin_sesion_redirige_login(page, ui_base_url):
    """CP-MAN-UI-10: Un usuario sin sesión es redirigido a la página de login."""
    page.goto(f"{ui_base_url}/mantenimiento-operacional")

    expect(page).to_have_url(f"{ui_base_url}/login", timeout=10000)
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()