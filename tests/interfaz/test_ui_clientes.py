# tests/interfaz/test_ui_clientes.py
import pytest
from playwright.sync_api import expect
from tests.interfaz.conftest import inyectar_sesion_admin, limpiar_usuario


class TestUIClientes:
    def test_ci_clie_01_sin_sesion_redirige_a_login(self, page, base_url):
        """CI-CLIE-01: Navegar a /clientes sin sesión redirige a /login."""
        page.goto(f"{base_url}/clientes")
        page.wait_for_url("**/login**", timeout=5000)
        assert "/login" in page.url

    def test_ci_clie_02_listado_clientes_admin(self, page, base_url):
        """CI-CLIE-02: Como admin, /clientes muestra la tabla #tablaClientes y botón Registrar Cliente."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/clientes")
        expect(page.locator("#tablaClientes")).to_be_visible()
        expect(page.locator("a:has-text('Registrar Cliente')")).to_be_visible()

    def test_ci_clie_03_busqueda_datatables_clientes(self, page, base_url):
        """CI-CLIE-03: El buscador de DataTables filtra los registros en #tablaClientes."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/clientes")
        search = page.locator("#tablaClientes_filter input[type='search']")
        expect(search).to_be_visible(timeout=5000)
        search.fill("11111112")
        expect(page.locator("#tablaClientes tbody")).to_contain_text("11111112")

    def test_ci_clie_04_formulario_registrar_clientes_carga(self, page, base_url):
        """CI-CLIE-04: /registrar_clientes muestra todos los campos requeridos del formulario."""
        page.goto(f"{base_url}/registrar_clientes")
        for selector in ["#cedula", "#nombre", "#apellido", "#telefono", "#direccion", "#email", "#password"]:
            expect(page.locator(selector)).to_be_visible()

    def test_ci_clie_05_registro_datos_invalidos_no_registra(self, page, base_url):
        """CI-CLIE-05: Enviar formulario con cédula inválida mantiene al usuario en /registrar_clientes."""
        page.goto(f"{base_url}/registrar_clientes")
        page.fill("#cedula", "ABC123")
        page.fill("#nombre", "Prueba")
        page.fill("#apellido", "UI")
        page.fill("#telefono", "04141234567")
        page.fill("#direccion", "Calle UI 1")
        page.fill("#email", "invalido_ui@test.com")
        page.fill("#password", "ValidPass1!")
        page.click("button[type='submit']")
        assert "/registrar_clientes" in page.url

    def test_ci_clie_06_registro_cliente_valido_en_ui(self, page, base_url):
        """CI-CLIE-06: Registrar cliente válido (77665599) redirige y aparece en el listado."""
        limpiar_usuario("77665599", "ui_reg@automall.com")
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/registrar_clientes")
        page.fill("#cedula", "77665599")
        page.fill("#nombre", "Playwright")
        page.fill("#apellido", "Cliente")
        page.fill("#telefono", "04141234567")
        page.fill("#direccion", "Avenida Principal UI 123")
        page.fill("#email", "ui_reg@automall.com")
        page.fill("#password", "UiPass123*")
        with page.expect_navigation(timeout=10000):
            page.click("button[type='submit']")

        page.goto(f"{base_url}/clientes")
        expect(page.locator("#tablaClientes")).to_contain_text("77665599", timeout=5000)

    def test_ci_clie_07_modal_editar_cliente(self, page, base_url):
        """CI-CLIE-07: Al pulsar editar en 77665599 se abre #modalEditarCliente precargado y guarda cambios."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/clientes")
        search = page.locator("#tablaClientes_filter input[type='search']")
        search.fill("77665599")
        btn_edit = page.locator("button.btn-editar-cliente[data-cedula='77665599']")
        expect(btn_edit).to_be_visible(timeout=5000)
        btn_edit.click()

        expect(page.locator("#modalEditarCliente")).to_be_visible()
        expect(page.locator("#editar_nombre")).to_have_value("Playwright")
        page.fill("#editar_nombre", "PlaywrightEdit")
        page.click("#modalEditarCliente button[type='submit']")
        btn_confirm_edit = page.locator(".swal2-popup button:has-text('Sí, Guardar')")
        expect(btn_confirm_edit).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=10000):
            btn_confirm_edit.click()
        expect(page.locator("#tablaClientes")).to_contain_text("PlaywrightEdit")

    def test_ci_clie_08_modal_eliminar_cliente(self, page, base_url):
        """CI-CLIE-08: Al pulsar eliminar en 77665599 se abre confirmación SweetAlert2 y elimina al cliente."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/clientes")
        search = page.locator("#tablaClientes_filter input[type='search']")
        search.fill("77665599")
        btn_del = page.locator("button.btn-eliminar-cliente[data-cedula='77665599']")
        expect(btn_del).to_be_visible(timeout=5000)
        btn_del.click()

        btn_confirm = page.locator(".swal2-popup button:has-text('Sí, Eliminar')")
        expect(btn_confirm).to_be_visible(timeout=5000)
        with page.expect_navigation(timeout=10000):
            btn_confirm.click()
        search = page.locator("#tablaClientes_filter input[type='search']")
        search.fill("77665599")
        expect(page.locator("#tablaClientes tbody")).not_to_contain_text("PlaywrightEdit")
