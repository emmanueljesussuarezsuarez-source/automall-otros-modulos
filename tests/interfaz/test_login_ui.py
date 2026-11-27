from playwright.sync_api import Page, expect


class TestLoginInterfaz:

    def test_UI_LOGIN_001_formulario_visible(self, page: Page, base_url: str):
        """Verifica que el formulario y sus campos aparezcan."""
        page.goto(f"{base_url}/login")

        formulario = page.locator("#formLogin")
        expect(formulario).to_be_visible()
        expect(page.locator("#emailInput")).to_be_visible()
        expect(page.locator("#passwordInput")).to_be_visible()
        expect(page.locator("#btnSubmit")).to_be_visible()

    def test_UI_LOGIN_002_boton_inicialmente_deshabilitado(self, page: Page, base_url: str):
        """Verifica que el botón no permita enviar un formulario vacío."""
        page.goto(f"{base_url}/login")
        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_UI_LOGIN_003_correo_invalido_no_habilita_boton(self, page: Page, base_url: str):
        """Comprueba que un correo inválido no habilite el botón."""
        page.goto(f"{base_url}/login")

        page.fill("#emailInput", "correo_invalido")
        page.fill("#passwordInput", "Password123")
        page.fill("#captchaInput", "ABCDE")

        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_UI_LOGIN_004_contrasena_corta_no_habilita_boton(self, page: Page, base_url: str):
        """Comprueba que una contraseña menor de 8 caracteres sea rechazada."""
        page.goto(f"{base_url}/login")

        page.fill("#emailInput", "prueba@example.com")
        page.fill("#passwordInput", "12345")
        page.fill("#captchaInput", "ABCDE")

        expect(page.locator("#btnSubmit")).to_be_disabled()

    def test_UI_LOGIN_005_limite_contrasena_20_caracteres(self, page: Page, base_url: str):
        """Comprueba que JavaScript limite la contraseña a 20 caracteres."""
        page.goto(f"{base_url}/login")

        page.fill("#emailInput", "prueba@example.com")
        page.fill("#passwordInput", "1234567890123456789012345")

        valor = page.locator("#passwordInput").input_value()
        assert len(valor) == 20

    def test_UI_LOGIN_006_correo_y_contrasena_validos_habilitan_boton(self, page: Page, base_url: str):
        """Comprueba que los campos válidos habiliten el botón."""
        page.goto(f"{base_url}/login")

        page.fill("#emailInput", "prueba@example.com")
        page.fill("#passwordInput", "Password123")
        page.fill("#captchaInput", "ABCDE")

        expect(page.locator("#btnSubmit")).to_be_enabled()
