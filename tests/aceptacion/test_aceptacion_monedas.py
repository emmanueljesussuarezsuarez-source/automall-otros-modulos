import random
import string
from playwright.sync_api import Page, expect
from .conftest import BASE_URL


def _sufijo(n=5):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def test_aceptacion_monedas_fisicas_crud_completo(login_admin: Page):
    """Criterio: Crear, editar y desactivar una moneda física con persistencia en BD."""
    page = login_admin
    page.goto(f"{BASE_URL}/monedas/gestion")

    suf = _sufijo()
    nombre = f"Moneda Test {suf}"
    nombre_edit = f"Moneda Edit {suf}"
    simbolo = f"M{suf[:2]}"

    # 1. Crear
    page.get_by_role("button", name="Nuevo Registro").click()
    page.locator("#nombre_registro").fill(nombre)
    page.locator("#simbolo_registro").fill(simbolo)
    page.locator("#estado_registro").select_option("Activo")
    page.locator("#formMoneda button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila = page.locator("#seccionMonedas tbody tr", has_text=nombre)
    expect(fila).to_be_visible()
    expect(fila).to_contain_text(simbolo)
    expect(fila.locator(".badge")).to_have_text("Activo")

    # 2. Editar
    fila.locator("button.btn-outline-primary").click()
    expect(page.locator("#modalTitulo")).to_have_text("Editar Moneda")
    page.locator("#nombre_registro").fill(nombre_edit)
    page.locator("#simbolo_registro").fill("ED")
    page.locator("#formMoneda button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_edit = page.locator("#seccionMonedas tbody tr", has_text=nombre_edit)
    expect(fila_edit).to_be_visible()
    expect(fila_edit).to_contain_text("ED")

    # 3. Desactivar
    fila_edit.locator("button.btn-outline-danger").click()
    expect(page.locator(".swal2-title")).to_have_text("¿Estás seguro?")
    page.locator(".swal2-confirm").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Desactivada!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    fila_inactiva = page.locator("#seccionMonedas tbody tr", has_text=nombre_edit)
    expect(fila_inactiva.locator(".badge")).to_have_text("Inactivo")


def test_aceptacion_monedas_digitales_crud_completo(login_admin: Page):
    """Criterio: Crear, editar y desactivar una moneda digital con persistencia en BD."""
    page = login_admin
    page.goto(f"{BASE_URL}/monedas/gestion")

    suf = _sufijo()
    nombre = f"Crypto Test {suf}"
    nombre_edit = f"Crypto Edit {suf}"
    simbolo = f"C{suf[:2]}"

    # 1. Crear en pestaña Digitales
    page.locator("#btnDigitales").click()
    page.get_by_role("button", name="Nuevo Registro").click()
    page.locator("#nombre_registro").fill(nombre)
    page.locator("#simbolo_registro").fill(simbolo)
    page.locator("#estado_registro").select_option("1")
    page.locator("#formMoneda button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    # Tras recargar, volver a seleccionar pestaña Digitales
    page.locator("#btnDigitales").click()
    fila = page.locator("#seccionDigitales tbody tr", has_text=nombre)
    expect(fila).to_be_visible()
    expect(fila).to_contain_text(simbolo)
    expect(fila.locator(".badge")).to_have_text("Activo")

    # 2. Editar
    fila.locator("button.btn-outline-primary").click()
    expect(page.locator("#modalTitulo")).to_have_text("Editar Moneda Digital")
    page.locator("#nombre_registro").fill(nombre_edit)
    page.locator("#formMoneda button[type='submit']").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Éxito!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    page.locator("#btnDigitales").click()
    fila_edit = page.locator("#seccionDigitales tbody tr", has_text=nombre_edit)
    expect(fila_edit).to_be_visible()

    # 3. Desactivar
    fila_edit.locator("button.btn-outline-danger").click()
    expect(page.locator(".swal2-title")).to_have_text("¿Estás seguro?")
    page.locator(".swal2-confirm").click()

    expect(page.locator(".swal2-title")).to_have_text("¡Desactivada!")
    page.locator(".swal2-confirm").click()
    page.wait_for_load_state("networkidle")

    page.locator("#btnDigitales").click()
    fila_inactiva = page.locator("#seccionDigitales tbody tr", has_text=nombre_edit)
    expect(fila_inactiva.locator(".badge")).to_have_text("Inactivo")


def test_aceptacion_monedas_acceso_denegado_cliente(login_cliente: Page):
    """Camino triste: Cliente no tiene acceso al módulo de monedas."""
    page = login_cliente
    response = page.goto(f"{BASE_URL}/monedas/gestion")
    assert response.status in (401, 403) or "/monedas/gestion" not in page.url