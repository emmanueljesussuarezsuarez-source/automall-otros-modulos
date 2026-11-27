# tests/aceptacion/test_aceptacion_clientes.py
from playwright.sync_api import expect
from tests.aceptacion.conftest import (
    UAT_ADMIN_EMAIL,
    UAT_ADMIN_PASS,
    UAT_REG_CEDULA,
    UAT_REG_EMAIL,
    hacer_login_ui,
)


class TestAceptacionClientes:
    def test_ca_clie_01_consultar_listado_clientes(self, page, base_url):
        """CA-CLIE-01: Administrador inicia sesión por UI y consulta el listado de clientes."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/clientes")
        expect(page.locator("#tablaClientes")).to_be_visible(timeout=5000)
        expect(page.locator("#tablaClientes_filter input[type='search']")).to_be_visible()

    def test_ca_clie_02_registrar_nuevo_cliente_y_verificar_en_tabla(self, page, base_url):
        """CA-CLIE-02: Administrador registra un nuevo cliente y valida que aparezca en el listado."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/registrar_clientes")

        page.fill("#cedula", UAT_REG_CEDULA)
        page.fill("#nombre", "Carlos")
        page.fill("#apellido", "Uat")
        page.fill("#telefono", "04149998877")
        page.fill("#direccion", "Avenida Bolivar Norte 200")
        page.fill("#email", UAT_REG_EMAIL)
        page.fill("#password", "UatPass123*")

        with page.expect_navigation(timeout=8000):
            page.click("button[type='submit']")

        if "/clientes" not in page.url:
            page.goto(f"{base_url}/clientes")

        page.locator("#tablaClientes_filter input[type='search']").fill(UAT_REG_CEDULA)
        expect(page.locator("#tablaClientes tbody")).to_contain_text(UAT_REG_CEDULA)

    def test_ca_clie_03_modificar_cliente_y_verificar_persistencia(self, page, base_url):
        """CA-CLIE-03: Administrador edita un cliente mediante modal + SweetAlert2 y verifica el cambio."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/clientes")

        page.locator("#tablaClientes_filter input[type='search']").fill(UAT_REG_CEDULA)
        btn_edit = page.locator(f"button.btn-editar-cliente[data-cedula='{UAT_REG_CEDULA}']")
        expect(btn_edit).to_be_visible(timeout=5000)
        btn_edit.click()

        expect(page.locator("#modalEditarCliente")).to_be_visible()
        page.fill("#editar_nombre", "CarlosEdit")
        page.click("#modalEditarCliente button[type='submit']")

        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Guardar')")

        page.locator("#tablaClientes_filter input[type='search']").fill(UAT_REG_CEDULA)
        expect(page.locator("#tablaClientes tbody")).to_contain_text("CarlosEdit")

    def test_ca_clie_04_eliminar_cliente_y_confirmar_desaparicion(self, page, base_url):
        """CA-CLIE-04: Administrador elimina al cliente de prueba y confirma que ya no existe en la tabla."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/clientes")

        page.locator("#tablaClientes_filter input[type='search']").fill(UAT_REG_CEDULA)
        btn_del = page.locator(f"button.btn-eliminar-cliente[data-cedula='{UAT_REG_CEDULA}']")
        expect(btn_del).to_be_visible(timeout=5000)
        btn_del.click()

        expect(page.locator(".swal2-popup")).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=8000):
            page.click(".swal2-popup button:has-text('Sí, Eliminar')")

        page.locator("#tablaClientes_filter input[type='search']").fill(UAT_REG_CEDULA)
        expect(page.locator("#tablaClientes tbody")).not_to_contain_text(UAT_REG_CEDULA)
