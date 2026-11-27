# tests/interfaz/test_ui_citas.py
import pytest
from playwright.sync_api import expect
from tests.interfaz.conftest import inyectar_sesion_admin, inyectar_sesion_cliente


class TestUICitas:
    def test_ci_cita_01_sin_sesion_redirige_a_login(self, page, base_url):
        """CI-CITA-01: Navegar a /consultar sin sesión redirige a /login."""
        page.goto(f"{base_url}/consultar")
        page.wait_for_url("**/login**", timeout=5000)
        assert "/login" in page.url

    def test_ci_cita_02_consultar_citas_como_admin(self, page, base_url):
        """CI-CITA-02: Admin ve #tablaCitas con columna 'Nombre del cliente' y botón 'Agendar Nueva Cita'."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/consultar")
        expect(page.locator("#tablaCitas")).to_be_visible()
        expect(page.locator("#tablaCitas thead")).to_contain_text("Nombre del cliente")
        expect(page.locator("a:has-text('Agendar Nueva Cita')")).to_be_visible()

    def test_ci_cita_03_consultar_citas_como_cliente(self, page, base_url):
        """CI-CITA-03: Cliente ve #tablaCitas sin la columna de administrador 'Nombre del cliente'."""
        inyectar_sesion_cliente(page.context, base_url)
        page.goto(f"{base_url}/consultar")
        expect(page.locator("#tablaCitas")).to_be_visible()
        expect(page.locator("#tablaCitas thead")).not_to_contain_text("Nombre del cliente")

    def test_ci_cita_04_agendar_como_cliente_oculta_select_cliente(self, page, base_url):
        """CI-CITA-04: En /agendar como cliente se muestran fecha, hora y vehículo, sin #select-cliente."""
        inyectar_sesion_cliente(page.context, base_url)
        page.goto(f"{base_url}/agendar")
        expect(page.locator("input[placeholder='Seleccione la fecha...']").last).to_be_visible()
        expect(page.locator("#hora_cita")).to_be_visible()
        expect(page.locator("#select-vehiculo")).to_be_visible()
        expect(page.locator("#select-cliente")).to_have_count(0)

    def test_ci_cita_05_agendar_como_admin_muestra_select_cliente(self, page, base_url):
        """CI-CITA-05: En /agendar como admin se muestra el selector #select-cliente."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/agendar")
        expect(page.locator("#select-cliente")).to_be_visible()
        expect(page.locator("#select-vehiculo")).to_be_visible()

    def test_ci_cita_06_previsualizacion_dinamica_vehiculo(self, page, base_url):
        """CI-CITA-06: Seleccionar un vehículo en #select-vehiculo actualiza #contenedor-previsualizacion."""
        inyectar_sesion_cliente(page.context, base_url)
        page.goto(f"{base_url}/agendar")
        preview_antes = page.locator("#contenedor-previsualizacion").inner_text()
        cod_vehiculo = page.locator("#select-vehiculo option[value]:not([value=''])").first.get_attribute("value")
        assert cod_vehiculo, "No hay vehículos disponibles en #select-vehiculo."
        page.select_option("#select-vehiculo", value=cod_vehiculo)
        preview_despues = page.locator("#contenedor-previsualizacion").inner_text()
        assert preview_despues != preview_antes

    def test_ci_cita_07_agendar_cita_valida_como_cliente(self, page, base_url):
        """CI-CITA-07: Completar fecha, hora y vehículo como cliente y enviar /agendar crea la cita."""
        inyectar_sesion_cliente(page.context, base_url)
        page.goto(f"{base_url}/agendar")
        page.locator("#fecha_cita").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('2029-09-16', true) : (el.value = '2029-09-16')"
        )
        page.locator("#hora_cita").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('11:00', true) : (el.value = '11:00')"
        )
        cod_vehiculo = page.locator("#select-vehiculo option[value]:not([value=''])").first.get_attribute("value")
        assert cod_vehiculo, "No hay vehículos disponibles en #select-vehiculo."
        page.select_option("#select-vehiculo", value=cod_vehiculo)
        page.click("#btn-agendar")
        page.wait_for_load_state("networkidle")
        expect(page.locator("body")).to_be_visible()

    def test_ci_cita_08_modal_foto_y_modificar_cita_admin(self, page, base_url, ui_server):
        """CI-CITA-08: Como admin en /consultar, abrir modal de foto y modal de modificar cita."""
        cod_cita = str(ui_server["cod_cita_ui"])
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/consultar")

        # Abrir modal de foto del vehículo
        btn_foto = page.locator(".btn-ver-foto").first
        expect(btn_foto).to_be_visible(timeout=5000)
        btn_foto.click()
        expect(page.locator("#modalFotoVehiculo")).to_be_visible()
        page.click("#modalFotoVehiculo .btn-close")

        # Abrir modal de modificar sobre la cita de prueba
        search = page.locator("#tablaCitas_filter input[type='search']")
        search.fill(cod_cita)
        btn_edit = page.locator(f"button.btn-editar-cita[data-cod='{cod_cita}']")
        expect(btn_edit).to_be_visible(timeout=5000)
        btn_edit.click()
        expect(page.locator("#modalModificar")).to_be_visible()
        expect(page.locator("#modal_cod_cita")).to_have_value(cod_cita)

    def test_ci_cita_09_confirmar_modificacion_desde_modal_admin(self, page, base_url, ui_server):
        """CI-CITA-09: Como admin, completar el modal de modificar cita y confirmar SweetAlert2 'Sí, Guardar'."""
        cod_cita = str(ui_server["cod_cita_ui"])
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/consultar")

        # Buscar y abrir modal de modificar
        page.locator("#tablaCitas_filter input[type='search']").fill(cod_cita)
        btn_edit = page.locator(f"button.btn-editar-cita[data-cod='{cod_cita}']")
        expect(btn_edit).to_be_visible(timeout=5000)
        btn_edit.click()
        expect(page.locator("#modalModificar")).to_be_visible()

        # Cambiar hora vía Flatpickr
        page.locator("#modal_hora").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('10:00', true) : (el.value = '10:00')"
        )
        # Cambiar fecha vía Flatpickr (admin puede editarla)
        page.locator("#modal_fecha").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('2029-10-20', true) : (el.value = '2029-10-20')"
        )
        # Cambiar estado
        page.select_option("#modal_estado", value="Pendiente")

        # Enviar formulario → SweetAlert2 "¿Guardar Cambios?"
        page.click("#btn-guardar-modificar-cita")
        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Guardar')")

        assert "/consultar" in page.url

    def test_ci_cita_10_eliminar_cita_desde_tabla_admin(self, page, base_url, ui_server):
        """CI-CITA-10: Como admin, eliminar una cita confirmando SweetAlert2 'Sí, Eliminar'."""
        cod_cita = str(ui_server["cod_cita_ui"])
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/consultar")

        # Buscar la cita de prueba en DataTable
        page.locator("#tablaCitas_filter input[type='search']").fill(cod_cita)
        btn_cancel = page.locator(f"button.btn-cancelar-cita[data-cod='{cod_cita}']")
        expect(btn_cancel).to_be_visible(timeout=5000)
        btn_cancel.click()

        # Confirmar SweetAlert2 "¿Eliminar Cita?"
        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Eliminar')")

        assert "/consultar" in page.url
