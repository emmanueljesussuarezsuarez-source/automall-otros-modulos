# tests/aceptacion/test_aceptacion_citas.py
from playwright.sync_api import expect
from tests.aceptacion.conftest import (
    UAT_ADMIN_EMAIL,
    UAT_ADMIN_PASS,
    UAT_CLIENTE_EMAIL,
    UAT_CLIENTE_PASS,
    UAT_CLIENTE_CEDULA,
    hacer_login_ui,
)


class TestAceptacionCitas:
    def test_ca_cita_01_cliente_agenda_cita_y_visualiza_en_consultar(self, page, base_url):
        """CA-CITA-01: Cliente inicia sesión por UI, agenda una nueva cita y verifica su registro en /consultar."""
        hacer_login_ui(page, base_url, UAT_CLIENTE_EMAIL, UAT_CLIENTE_PASS)
        page.goto(f"{base_url}/agendar")

        page.locator("#fecha_cita").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('2029-11-15', true) : (el.value = '2029-11-15')"
        )
        page.locator("#hora_cita").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('10:00', true) : (el.value = '10:00')"
        )
        cod_vehiculo = page.locator("#select-vehiculo option[value]:not([value=''])").first.get_attribute("value")
        assert cod_vehiculo, "No hay vehículos disponibles en #select-vehiculo."
        page.select_option("#select-vehiculo", value=cod_vehiculo)

        page.click("#btn-agendar")
        btn_confirmar = page.locator(".swal2-popup button:has-text('Sí, Agendar Cita')")
        expect(btn_confirmar).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            btn_confirmar.click()

        assert "/consultar" in page.url
        expect(page.locator("#tablaCitas tbody")).to_contain_text("2029-11-15")

    def test_ca_cita_02_cliente_consulta_sus_citas_sin_columnas_admin(self, page, base_url):
        """CA-CITA-02: Cliente consulta sus citas en /consultar con vista restringida a su rol."""
        hacer_login_ui(page, base_url, UAT_CLIENTE_EMAIL, UAT_CLIENTE_PASS)
        page.goto(f"{base_url}/consultar")

        expect(page.locator("#tablaCitas")).to_be_visible(timeout=5000)
        expect(page.locator("#tablaCitas thead")).not_to_contain_text("Nombre del cliente")
        expect(page.locator("#tablaCitas tbody")).to_contain_text("2029-11-15")

    def test_ca_cita_03_admin_reprograma_cita_desde_modal(self, page, base_url):
        """CA-CITA-03: Administrador inicia sesión, busca la cita del cliente, la reprograma y verifica el cambio."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/consultar")

        page.locator("#tablaCitas_filter input[type='search']").fill(UAT_CLIENTE_CEDULA)
        btn_edit = page.locator("button.btn-editar-cita").first
        expect(btn_edit).to_be_visible(timeout=5000)
        btn_edit.click()

        expect(page.locator("#modalModificar")).to_be_visible()
        page.locator("#modal_fecha").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('2029-11-20', true) : (el.value = '2029-11-20')"
        )
        page.locator("#modal_hora").evaluate(
            "el => el._flatpickr ? el._flatpickr.setDate('11:30', true) : (el.value = '11:30')"
        )
        page.select_option("#modal_estado", value="Pendiente")

        page.click("#btn-guardar-modificar-cita")
        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Guardar')")

        page.locator("#tablaCitas_filter input[type='search']").fill(UAT_CLIENTE_CEDULA)
        expect(page.locator("#tablaCitas tbody")).to_contain_text("2029-11-20")

    def test_ca_cita_04_admin_elimina_cita_de_prueba(self, page, base_url):
        """CA-CITA-04: Administrador elimina la cita reprogramada y confirma que desaparece del listado."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/consultar")

        page.locator("#tablaCitas_filter input[type='search']").fill(UAT_CLIENTE_CEDULA)
        btn_del = page.locator("button.btn-cancelar-cita").first
        expect(btn_del).to_be_visible(timeout=5000)
        btn_del.click()

        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Eliminar')")

        page.locator("#tablaCitas_filter input[type='search']").fill(UAT_CLIENTE_CEDULA)
        expect(page.locator("#tablaCitas tbody")).not_to_contain_text("2029-11-20")
