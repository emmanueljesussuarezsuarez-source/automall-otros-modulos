"""
Pruebas de Interfaz (UI / End-to-End) con Playwright — Módulo Taller
Archivo: tests/ui/test_taller_ui.py
Base de datos real de prueba: automall_test y seguridad_test
"""

from playwright.sync_api import expect

from models.taller import Taller


def _abrir_y_guardar_taller(admin_page, ui_base_url, nombre, direccion):
    """Abre /taller, despliega el modal de registro, llena el formulario y guarda."""
    admin_page.goto(f"{ui_base_url}/taller")
    admin_page.click('button[data-bs-target="#modalRegistrarTaller"]')

    modal = admin_page.locator("#modalRegistrarTaller")
    expect(modal).to_be_visible(timeout=5000)
    expect(modal.locator("#nombre_taller")).to_be_visible()

    modal.locator("#nombre_taller").fill(nombre)
    modal.locator("#direccion").fill(direccion)
    modal.get_by_role("button", name="Guardar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/taller", timeout=10000)


def test_cp_tal_ui_01_login_exitoso(page, ui_base_url):
    """CP-TAL-UI-01: La página de login carga y permite iniciar sesión."""
    page.goto(f"{ui_base_url}/login")
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()

    page.fill("#emailInput", "prueba@gmail.com")
    page.fill("#passwordInput", "12345678")

    boton = page.locator("#btnSubmit")
    expect(boton).to_be_enabled()
    boton.click()

    expect(page).to_have_url(f"{ui_base_url}/", timeout=10000)


def test_cp_tal_ui_02_modal_crear_taller_carga(admin_page, ui_base_url):
    """CP-TAL-UI-02: El botón de registrar abre el modal de creación con sus campos."""
    admin_page.goto(f"{ui_base_url}/taller")
    admin_page.click('button[data-bs-target="#modalRegistrarTaller"]')

    modal = admin_page.locator("#modalRegistrarTaller")
    expect(modal).to_be_visible(timeout=5000)
    expect(modal.get_by_text("Registrar Taller")).to_be_visible()
    expect(modal.locator("#nombre_taller")).to_be_visible()
    expect(modal.locator("#direccion")).to_be_visible()
    expect(modal.get_by_role("button", name="Guardar")).to_be_visible()


def test_cp_tal_ui_03_crear_taller_desde_formulario(admin_page, ui_base_url):
    """CP-TAL-UI-03: Se puede crear un taller llenando el formulario y haciendo clic en guardar."""
    _abrir_y_guardar_taller(
        admin_page,
        ui_base_url,
        "Taller UI Central",
        "Avenida Libertador Calle 12",
    )

    expect(admin_page.locator("#tablaTalleres")).to_contain_text("Taller UI Central")


def test_cp_tal_ui_04_mensaje_exito_y_redireccion(admin_page, ui_base_url):
    """CP-TAL-UI-04: Aparece el mensaje de éxito y redirige a la lista."""
    _abrir_y_guardar_taller(
        admin_page,
        ui_base_url,
        "Taller UI Mensaje",
        "Calle Principal Sector Centro",
    )

    alerta = admin_page.locator(".swal2-popup")
    expect(alerta).to_be_visible(timeout=10000)
    expect(alerta).to_contain_text("Taller registrado correctamente.")


def test_cp_tal_ui_05_lista_muestra_talleres(admin_page, ui_base_url):
    """CP-TAL-UI-05: La lista de talleres muestra los registros correctamente."""
    Taller.guardar("Taller UI Listado", "Carrera 18 con Calle 22", "1", "18998754")

    admin_page.goto(f"{ui_base_url}/taller")
    tabla = admin_page.locator("#tablaTalleres")

    expect(tabla).to_be_visible(timeout=5000)
    expect(tabla).to_contain_text("Taller UI Listado")
    expect(tabla).to_contain_text("Carrera 18 con Calle 22")
    expect(tabla).to_contain_text("Activo")


def test_cp_tal_ui_06_editar_taller_abre_modal_y_actualiza(admin_page, ui_base_url):
    """CP-TAL-UI-06: El botón de editar abre el formulario con los datos cargados y actualiza."""
    Taller.guardar("Taller UI Original", "Avenida Original Local 10", "1", "18998754")

    admin_page.goto(f"{ui_base_url}/taller")
    fila = admin_page.locator("#tablaTalleres tbody tr", has_text="Taller UI Original")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-editar-taller").click()

    modal = admin_page.locator("#modalEditarTaller")
    expect(modal).to_be_visible(timeout=5000)
    expect(modal.locator("#edit_nombre_taller")).to_have_value("Taller UI Original")
    expect(modal.locator("#edit_direccion")).to_have_value("Avenida Original Local 10")

    modal.locator("#edit_nombre_taller").fill("Taller UI Modificado")
    modal.locator("#edit_direccion").fill("Avenida Venezuela Local 45")
    modal.get_by_role("button", name="Actualizar").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/taller", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Taller actualizado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaTalleres")).to_contain_text("Taller UI Modificado")


def test_cp_tal_ui_07_eliminar_desactiva_taller_y_actualiza_lista(admin_page, ui_base_url):
    """CP-TAL-UI-07: El botón de eliminar desactiva el taller y actualiza la lista."""
    Taller.guardar("Taller UI Eliminar", "Avenida Eliminar Calle 30", "1", "18998754")

    admin_page.goto(f"{ui_base_url}/taller")
    fila = admin_page.locator("#tablaTalleres tbody tr", has_text="Taller UI Eliminar")
    expect(fila).to_be_visible(timeout=5000)

    fila.locator(".btn-eliminar-taller").click()

    confirmacion = admin_page.locator(".swal2-popup")
    expect(confirmacion).to_be_visible(timeout=5000)
    expect(confirmacion).to_contain_text("¿Deseas eliminar este taller?")
    confirmacion.locator(".swal2-confirm").click()

    expect(admin_page).to_have_url(f"{ui_base_url}/taller", timeout=10000)
    expect(admin_page.locator(".swal2-popup")).to_contain_text(
        "Taller desactivado correctamente.",
        timeout=10000,
    )
    expect(admin_page.locator("#tablaTalleres")).not_to_contain_text("Taller UI Eliminar")


def test_cp_tal_ui_08_sin_sesion_redirige_login(page, ui_base_url):
    """CP-TAL-UI-08: Un usuario sin sesión es redirigido a la página de login."""
    page.goto(f"{ui_base_url}/taller")

    expect(page).to_have_url(f"{ui_base_url}/login", timeout=10000)
    expect(page.get_by_text("¡Hola de nuevo!")).to_be_visible()