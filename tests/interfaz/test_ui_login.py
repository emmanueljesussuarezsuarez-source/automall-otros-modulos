# tests/interfaz/test_ui_login.py
import pytest
from playwright.sync_api import expect
from tests.interfaz.conftest import inyectar_captcha_cookie, inyectar_sesion_admin


class TestUILogin:
    def test_ci_log_01_carga_formulario_login(self, page, base_url):
        """CI-LOG-01: La vista /login carga controles y botón inicialmente deshabilitado."""
        page.goto(f"{base_url}/login")
        expect(page.locator("h3")).to_contain_text("Hola de nuevo")
        expect(page.locator("#emailInput")).to_be_visible()
        expect(page.locator("#passwordInput")).to_be_visible()
        expect(page.locator("#captchaInput")).to_be_visible()
        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_ci_log_02_captcha_visible_y_recarga(self, page, base_url):
        """CI-LOG-02: La imagen CAPTCHA carga correctamente y el botón recargar cambia el src."""
        page.goto(f"{base_url}/login")
        img = page.locator("#imgCaptcha")
        expect(img).to_be_visible()
        natural_w = img.evaluate("el => el.naturalWidth")
        assert natural_w > 0

        src_inicial = img.get_attribute("src")
        page.click("#btnRecargarCaptcha")
        src_nuevo = img.get_attribute("src")
        assert src_nuevo != src_inicial

    def test_ci_log_03_validacion_correo_invalido_en_vivo(self, page, base_url):
        """CI-LOG-03: Ingresar un correo sin formato válido muestra alerta en #js-error-container."""
        page.goto(f"{base_url}/login")
        page.fill("#emailInput", "correo_invalido")
        expect(page.locator("#js-error-container")).to_contain_text("formato del correo")
        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_ci_log_04_validacion_password_corta_en_vivo(self, page, base_url):
        """CI-LOG-04: Contraseña menor a 8 caracteres muestra mensaje de faltantes en rojo."""
        page.goto(f"{base_url}/login")
        page.fill("#passwordInput", "12345")
        expect(page.locator("#passwordHelp")).to_contain_text("Te faltan 3 caracteres")
        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_ci_log_05_habilita_boton_con_formato_completo(self, page, base_url):
        """CI-LOG-05: Con correo, contraseña (8-20) y captcha de 5 caracteres se habilita #btnSubmit."""
        page.goto(f"{base_url}/login")
        page.fill("#emailInput", "usuario@automall.com")
        page.fill("#passwordInput", "Password123")
        page.fill("#captchaInput", "ABCDE")
        expect(page.locator("#btnSubmit")).to_be_enabled()

    def test_ci_log_06_login_captcha_incorrecto_muestra_error(self, page, base_url):
        """CI-LOG-06: Enviar login con captcha erróneo muestra alerta de error y limpia captcha."""
        page.goto(f"{base_url}/login")
        inyectar_captcha_cookie(page.context, base_url, codigo="SMOKE")
        page.fill("#emailInput", "ui_temp@automall.com")
        page.fill("#passwordInput", "UiPass123!")
        page.fill("#captchaInput", "MALO1")
        page.click("#btnSubmit")
        expect(page.locator("#js-error-container")).to_contain_text("CAPTCHA", timeout=5000)

    def test_ci_log_07_login_exitoso_redirige_a_inicio(self, page, base_url):
        """CI-LOG-07: Login con credenciales válidas y captcha coincidente redirige al inicio (/)."""
        page.goto(f"{base_url}/login")
        inyectar_captcha_cookie(page.context, base_url, codigo="SMOKE")
        page.fill("#emailInput", "ui_temp@automall.com")
        page.fill("#passwordInput", "UiPass123!")
        page.fill("#captchaInput", "SMOKE")
        page.click("#btnSubmit")
        page.wait_for_url(f"{base_url}/", timeout=5000)
        assert page.url == f"{base_url}/"

    def test_ci_log_08_enlace_olvido_password_navega_a_recuperar(self, page, base_url):
        """CI-LOG-08: El enlace '¿La olvidaste?' navega a /recuperar y carga el formulario."""
        page.goto(f"{base_url}/login")
        page.click("a:has-text('¿La olvidaste?')")
        page.wait_for_url(f"{base_url}/recuperar", timeout=5000)
        expect(page.locator("h3")).to_contain_text("Recuperar Acceso")
        expect(page.locator("input[name='email']")).to_be_visible()

    def test_ci_log_09_enlace_registrate_navega_a_registro(self, page, base_url):
        """CI-LOG-09: El botón 'Regístrate en AutoMall' navega al formulario de registro."""
        page.goto(f"{base_url}/login")
        page.click("a:has-text('Regístrate en AutoMall')")
        page.wait_for_load_state("networkidle")
        assert "/login" not in page.url

    def test_ci_log_10_logout_redirige_y_bloquea_ruta_protegida(self, page, base_url):
        """CI-LOG-10: Al cerrar sesión en /logout redirige a /login y bloquea /clientes."""
        inyectar_sesion_admin(page.context, base_url)
        page.goto(f"{base_url}/logout")
        page.wait_for_url("**/login**", timeout=5000)
        page.goto(f"{base_url}/clientes")
        page.wait_for_url("**/login**", timeout=5000)
        assert "/login" in page.url
