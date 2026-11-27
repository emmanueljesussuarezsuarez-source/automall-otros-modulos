import random
import string
from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def _sufijo(n=5):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def test_aceptacion_metodos_pago_crud_completo(login_admin: Page):
    """Criterio: Crear (con requiere_referencia), editar y desactivar un método de pago."""
    page = login_admin
    page.goto(f"{BASE_URL}/metodos-pago/gestion")

    suf = _sufijo()
    nombre = f"Metodo Test {suf}"
    nombre_edit = f"Metodo Edit {suf}"

    # 1. Crear método que requiere referencia = Sí
    page.get_by_role("button", name="Nuevo Método").click()
    page.locator("#nombre_metodo").fill(nombre)
    page.locator("#requiere_referencia").select_option("1")
    page.locator("#estado").select_option("Activo")
    page.locator("#formMetodo button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila = page.locator("tbody tr", has_text=nombre)
    expect(fila).to_be_visible()
    expect(fila.locator("td").nth(2).locator(".badge")).to_have_text("Sí")
    expect(fila.locator("td").nth(3).locator(".badge")).to_have_text("Activo")

    # 2. Editar (cambiar nombre y requiere_referencia a No)
    fila.locator("button.btn-outline-primary").click()
    expect(page.locator("#modalTitulo")).to_have_text("Editar Método")
    page.locator("#nombre_metodo").fill(nombre_edit)
    page.locator("#requiere_referencia").select_option("0")
    page.locator("#formMetodo button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_edit = page.locator("tbody tr", has_text=nombre_edit)
    expect(fila_edit).to_be_visible()
    expect(fila_edit.locator("td").nth(2).locator(".badge")).to_have_text("No")

    # 3. Desactivar
    fila_edit.locator("button.btn-outline-danger").click()
    expect(page.locator(".swal2-title")).to_have_text("¿Estás seguro?")
    page.locator(".swal2-confirm").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Desactivado!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_inactiva = page.locator("tbody tr", has_text=nombre_edit)
    expect(fila_inactiva.locator("td").nth(3).locator(".badge")).to_have_text("Inactivo")


def test_aceptacion_metodos_pago_acceso_denegado_cliente(login_cliente: Page):
    """Camino triste: Un cliente no debe poder gestionar métodos de pago."""
    page = login_cliente
    response = page.goto(f"{BASE_URL}/metodos-pago/gestion")
    assert response.status in (401, 403) or "/metodos-pago/gestion" not in page.url