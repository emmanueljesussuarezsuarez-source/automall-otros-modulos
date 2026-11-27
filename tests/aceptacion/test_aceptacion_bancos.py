import re
import random
import string
from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def _sufijo_letras(n=5):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def test_aceptacion_bancos_flujo_completo_crud(login_admin: Page):
    """Criterio: El administrador puede crear, editar y desactivar un banco persistiendo en BD."""
    page = login_admin
    page.goto(f"{BASE_URL}/bancos/gestion")

    sufijo = _sufijo_letras()
    nombre_original = f"Banco Prueba {sufijo}"
    nombre_editado = f"Banco Editado {sufijo}"

    # 1. Crear banco
    page.get_by_role("button", name="Nuevo Banco").click()
    page.locator("#nombre_banco").fill(nombre_original)
    page.locator("#estado").select_option("Activo")
    page.locator("#formBanco button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila = page.locator("tbody tr", has_text=nombre_original)
    expect(fila).to_be_visible()
    expect(fila.locator(".badge")).to_have_text("Activo")

    # 2. Editar banco
    fila.locator("button.btn-outline-primary").click()
    expect(page.locator("#modalTitulo")).to_have_text("Editar Banco")
    page.locator("#nombre_banco").fill(nombre_editado)
    page.locator("#formBanco button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_editada = page.locator("tbody tr", has_text=nombre_editado)
    expect(fila_editada).to_be_visible()

    # 3. Desactivar banco (cambio de estado a Inactivo)
    fila_editada.locator("button.btn-outline-danger").click()
    expect(page.locator(".swal2-title")).to_have_text("¿Estás seguro?")
    page.locator(".swal2-confirm").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Desactivado!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_inactiva = page.locator("tbody tr", has_text=nombre_editado)
    expect(fila_inactiva).to_be_visible()
    expect(fila_inactiva.locator(".badge")).to_have_text("Inactivo")


def test_aceptacion_bancos_acceso_denegado_cliente(login_cliente: Page):
    """Camino triste: Un cliente no debe poder acceder a la gestión de bancos."""
    page = login_cliente
    response = page.goto(f"{BASE_URL}/bancos/gestion")
    # Verifica que no cargue la tabla de gestión (bloqueo por permisos o redirección)
    assert response.status in (401, 403) or "/bancos/gestion" not in page.url