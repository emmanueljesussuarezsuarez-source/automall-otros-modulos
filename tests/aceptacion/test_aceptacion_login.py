# tests/aceptacion/test_aceptacion_login.py
from playwright.sync_api import expect
from tests.aceptacion.conftest import (
    UAT_ADMIN_EMAIL,
    UAT_ADMIN_PASS,
    inyectar_captcha_cookie,
    hacer_login_ui,
)


class TestAceptacionLogin:
    def test_ca_log_01_acceso_protegido_y_login_exitoso(self, page, base_url):
        """CA-LOG-01: Usuario sin sesión es redirigido a /login, inicia sesión por UI y accede al sistema."""
        page.goto(f"{base_url}/clientes")
        page.wait_for_url("**/login**", timeout=5000)
        assert "/login" in page.url

        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        assert page.url.rstrip("/") == base_url.rstrip("/")

    def test_ca_log_02_rechazo_captcha_incorrecto_muestra_alerta_persistente(self, page, base_url):
        """CA-LOG-02: Ante CAPTCHA incorrecto el sistema rechaza el ingreso y mantiene visible la alerta de error."""
        page.goto(f"{base_url}/login")
        inyectar_captcha_cookie(page.context, base_url, "UATOK")
        page.fill("#emailInput", UAT_ADMIN_EMAIL)
        page.fill("#passwordInput", UAT_ADMIN_PASS)
        page.fill("#captchaInput", "MALO1")
        page.click("#btnSubmit")

        alerta = page.locator("#js-error-container .alert-danger")
        expect(alerta).to_be_visible(timeout=5000)
        page.wait_for_timeout(500)
        expect(alerta).to_be_visible()
        assert "/login" in page.url

    def test_ca_log_03_flujo_navegacion_recuperar_clave(self, page, base_url):
        """CA-LOG-03: Usuario accede desde /login al flujo de recuperación de contraseña."""
        page.goto(f"{base_url}/login")
        page.click("a:has-text('¿La olvidaste?')")
        page.wait_for_url("**/recuperar**", timeout=5000)
        expect(page.locator("body")).to_contain_text("Recuperar")

    def test_ca_log_04_cierre_sesion_bloquea_rutas_privadas(self, page, base_url):
        """CA-LOG-04: Cerrar sesión invalida el acceso y bloquea el ingreso posterior a rutas protegidas."""
        hacer_login_ui(page, base_url, UAT_ADMIN_EMAIL, UAT_ADMIN_PASS)
        page.goto(f"{base_url}/logout")
        page.wait_for_url("**/login**", timeout=5000)

        page.goto(f"{base_url}/clientes")
        page.wait_for_url("**/login**", timeout=5000)
        assert "/login" in page.url
