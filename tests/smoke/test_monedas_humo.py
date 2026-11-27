import uuid
import pytest
from models.db import ConexionBD


@pytest.fixture(autouse=True)
def entorno_testing_bd(monkeypatch):
    """Garantiza que toda la sesión de pruebas de humo apunte a automall_test y seguridad_test."""
    monkeypatch.setenv("FLASK_ENV", "testing")


@pytest.fixture
def sesion_usuario_prueba(client):
    """
    Consulta el usuario real prueba@gmail.com en seguridad_test e inicia su sesión
    para navegar los módulos protegidos sin mocks.
    """
    conexion_seg = ConexionBD.obtener_conexion_seguridad()
    try:
        assert conexion_seg.database == "seguridad_test", (
            f"Seguridad: se esperaba 'seguridad_test' y se conectó a '{conexion_seg.database}'"
        )
        cursor = conexion_seg.cursor(dictionary=True)
        cursor.execute(
            "SELECT cedula_usuario, nombre, cod_rol FROM t_usuario WHERE correo = %s LIMIT 1",
            ("prueba@gmail.com",)
        )
        usuario = cursor.fetchone()
        cursor.close()
    finally:
        conexion_seg.close()

    assert usuario is not None, "No existe el usuario 'prueba@gmail.com' en seguridad_test.t_usuario"

    with client.session_transaction() as sess:
        sess["usuario_nombre"] = usuario["nombre"]
        sess["cedula_usuario"] = usuario["cedula_usuario"]
        sess["cod_rol"] = usuario["cod_rol"]
        sess["rol"] = usuario["cod_rol"]

    return client


def _contar_monedas(nombre):
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM moneda WHERE nombre_moneda = %s", (nombre,))
        total = cur.fetchone()[0]
        cur.close()
        return total
    finally:
        con.close()


def _limpiar_monedas(*nombres):
    nombres_validos = [n for n in nombres if n]
    if not nombres_validos:
        return
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        placeholders = ",".join(["%s"] * len(nombres_validos))
        cur.execute(f"DELETE FROM moneda WHERE nombre_moneda IN ({placeholders})", tuple(nombres_validos))
        con.commit()
        cur.close()
    finally:
        con.close()


def _contar_digitales(nombre):
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM moneda_digital WHERE nombre_digital = %s", (nombre,))
        total = cur.fetchone()[0]
        cur.close()
        return total
    finally:
        con.close()


def _limpiar_digitales(*nombres):
    nombres_validos = [n for n in nombres if n]
    if not nombres_validos:
        return
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        placeholders = ",".join(["%s"] * len(nombres_validos))
        cur.execute(f"DELETE FROM moneda_digital WHERE nombre_digital IN ({placeholders})", tuple(nombres_validos))
        con.commit()
        cur.close()
    finally:
        con.close()


# ==============================================================================
# 1. CAMINO FELIZ: VISTA GET Y CICLOS CRUD REALES (REGULAR Y DIGITAL)
# ==============================================================================

def test_humo_monedas_gestion_get_real(sesion_usuario_prueba):
    """Humo: Verifica que GET /monedas/gestion cargue la vista real desde automall_test."""
    con = ConexionBD.obtener_conexion()
    try:
        assert con.database == "automall_test"
    finally:
        con.close()

    response = sesion_usuario_prueba.get("/monedas/gestion")

    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_humo_monedas_regulares_ciclo_crud_real_automall_test(sesion_usuario_prueba):
    """Humo End-to-End: Crear -> Editar -> Eliminar lógico en /monedas contra automall_test."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_inicial = f"Mon Smoke {sufijo}"
    nombre_editado = f"Mon Edit {sufijo}"
    cod_moneda = None

    try:
        # 1. CREAR
        res_crear = sesion_usuario_prueba.post(
            "/monedas/crear",
            data={"nombre_moneda": nombre_inicial, "simbolo": "MS", "estado": "Activo"}
        )
        assert res_crear.status_code == 200
        assert res_crear.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_moneda, nombre_moneda, simbolo, estado FROM moneda WHERE nombre_moneda = %s", (nombre_inicial,))
            fila = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila is not None, "La moneda no se guardó en automall_test.moneda"
        cod_moneda = fila["cod_moneda"]
        assert fila["simbolo"] == "MS"

        # 2. EDITAR
        res_editar = sesion_usuario_prueba.post(
            f"/monedas/editar/{cod_moneda}",
            data={"nombre_moneda": nombre_editado, "simbolo": "ME", "estado": "Activo"}
        )
        assert res_editar.status_code == 200
        assert res_editar.get_json()["status"] == "success"

        # 3. ELIMINAR LÓGICO
        res_eliminar = sesion_usuario_prueba.post(f"/monedas/eliminar/{cod_moneda}")
        assert res_eliminar.status_code == 200
        assert res_eliminar.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT nombre_moneda, simbolo, estado FROM moneda WHERE cod_moneda = %s", (cod_moneda,))
            fila_final = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila_final["nombre_moneda"] == nombre_editado
        assert fila_final["simbolo"] == "ME"
        assert fila_final["estado"] == "Inactivo"

    finally:
        _limpiar_monedas(nombre_inicial, nombre_editado)


def test_humo_monedas_digitales_ciclo_crud_real_automall_test(sesion_usuario_prueba):
    """Humo End-to-End: Crear -> Editar -> Eliminar lógico en /monedas-digitales contra automall_test."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_inicial = f"Dig Smoke {sufijo}"
    nombre_editado = f"Dig Edit {sufijo}"
    cod_digital = None

    try:
        # 1. CREAR
        res_crear = sesion_usuario_prueba.post(
            "/monedas-digitales/crear",
            data={"nombre_digital": nombre_inicial, "simbolo_digital": "DS", "estado_digital": "1"}
        )
        assert res_crear.status_code == 200
        assert res_crear.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute(
                "SELECT cod_mon_digital, nombre_digital, simbolo_digital, estado FROM moneda_digital WHERE nombre_digital = %s",
                (nombre_inicial,)
            )
            fila = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila is not None, "La moneda digital no se guardó en automall_test.moneda_digital"
        cod_digital = fila["cod_mon_digital"]
        assert fila["simbolo_digital"] == "DS"

        # 2. EDITAR
        res_editar = sesion_usuario_prueba.post(
            f"/monedas-digitales/editar/{cod_digital}",
            data={"nombre_digital": nombre_editado, "simbolo_digital": "DE", "estado_digital": "1"}
        )
        assert res_editar.status_code == 200
        assert res_editar.get_json()["status"] == "success"

        # 3. ELIMINAR LÓGICO
        res_eliminar = sesion_usuario_prueba.post(f"/monedas-digitales/eliminar/{cod_digital}")
        assert res_eliminar.status_code == 200
        assert res_eliminar.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT nombre_digital, simbolo_digital, estado FROM moneda_digital WHERE cod_mon_digital = %s", (cod_digital,))
            fila_final = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila_final["nombre_digital"] == nombre_editado
        assert fila_final["simbolo_digital"] == "DE"
        assert fila_final["estado"] == 0

    finally:
        _limpiar_digitales(nombre_inicial, nombre_editado)


# ==============================================================================
# 2. VALIDACIONES Y REGLAS DE NEGOCIO (CAMINO TRISTE REAL)
# ==============================================================================

@pytest.mark.parametrize("payload", [
    {},
    {"nombre_moneda": "", "simbolo": "$", "estado": "Activo"},
    {"nombre_moneda": "   ", "simbolo": "$", "estado": "Activo"},
    {"nombre_moneda": "D", "simbolo": "$", "estado": "Activo"},
    {"nombre_moneda": "M" * 51, "simbolo": "$", "estado": "Activo"},
    {"nombre_moneda": "Moneda Simb Largo", "simbolo": "S" * 11, "estado": "Activo"},
    {"nombre_moneda": "Moneda Est Malo", "simbolo": "EM", "estado": "Invalido"},
])
def test_humo_moneda_regular_crear_rechaza_entradas_invalidas(sesion_usuario_prueba, payload):
    """Humo (Camino triste): Rechaza datos inválidos al crear moneda regular con HTTP 400."""
    try:
        response = sesion_usuario_prueba.post("/monedas/crear", data=payload)
        assert response.status_code == 400
        assert response.get_json()["status"] == "error"
    finally:
        if payload.get("nombre_moneda"):
            _limpiar_monedas(payload["nombre_moneda"].strip())


def test_humo_moneda_regular_editar_rechaza_entradas_invalidas_y_duplicados(sesion_usuario_prueba):
    """Humo (Camino triste + Integridad): Rechaza duplicados al crear/editar y entradas inválidas al editar."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_uno = f"Mon Dup Uno {sufijo}"
    nombre_dos = f"Mon Dup Dos {sufijo}"

    try:
        assert sesion_usuario_prueba.post("/monedas/crear", data={"nombre_moneda": nombre_uno, "simbolo": "U", "estado": "Activo"}).status_code == 200
        assert sesion_usuario_prueba.post("/monedas/crear", data={"nombre_moneda": nombre_dos, "simbolo": "D", "estado": "Activo"}).status_code == 200

        # Duplicado al crear
        res_dup_crear = sesion_usuario_prueba.post("/monedas/crear", data={"nombre_moneda": nombre_uno, "simbolo": "U", "estado": "Activo"})
        assert res_dup_crear.status_code == 400
        assert _contar_monedas(nombre_uno) == 1

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_moneda FROM moneda WHERE nombre_moneda = %s", (nombre_dos,))
            cod_dos = cur.fetchone()["cod_moneda"]
            cur.close()
        finally:
            con.close()

        # Duplicado al editar
        res_dup_edit = sesion_usuario_prueba.post(f"/monedas/editar/{cod_dos}", data={"nombre_moneda": nombre_uno, "simbolo": "D", "estado": "Activo"})
        assert res_dup_edit.status_code == 400
        assert _contar_monedas(nombre_uno) == 1

        # Entradas inválidas al editar
        assert sesion_usuario_prueba.post(f"/monedas/editar/{cod_dos}", data={"nombre_moneda": "X", "simbolo": "D", "estado": "Activo"}).status_code == 400
        assert sesion_usuario_prueba.post(f"/monedas/editar/{cod_dos}", data={"nombre_moneda": nombre_dos, "simbolo": "D", "estado": "Malo"}).status_code == 400
    finally:
        _limpiar_monedas(nombre_uno, nombre_dos)


@pytest.mark.parametrize("payload", [
    {},
    {"nombre_digital": "", "simbolo_digital": "BTC", "estado_digital": "1"},
    {"nombre_digital": "B", "simbolo_digital": "BTC", "estado_digital": "1"},
    {"nombre_digital": "B" * 51, "simbolo_digital": "BTC", "estado_digital": "1"},
    {"nombre_digital": "Dig Simb Largo", "simbolo_digital": "S" * 31, "estado_digital": "1"},
    {"nombre_digital": "Dig Estado Texto", "simbolo_digital": "DET", "estado_digital": "abc"},
    {"nombre_digital": "Dig Estado Raro", "simbolo_digital": "DER", "estado_digital": "99"},
])
def test_humo_moneda_digital_crear_rechaza_entradas_invalidas(sesion_usuario_prueba, payload):
    """Humo (Camino triste): Rechaza datos inválidos al crear moneda digital con HTTP 400."""
    try:
        response = sesion_usuario_prueba.post("/monedas-digitales/crear", data=payload)
        assert response.status_code == 400
        assert response.get_json()["status"] == "error"
    finally:
        if payload.get("nombre_digital"):
            _limpiar_digitales(payload["nombre_digital"].strip())


def test_humo_moneda_digital_rechaza_duplicados(sesion_usuario_prueba):
    """Humo (Integridad BD): Rechaza duplicados al crear y renombrar monedas digitales."""
    sufijo = uuid.uuid4().hex[:6].upper()
    dig_uno = f"Dig Dup Uno {sufijo}"
    dig_dos = f"Dig Dup Dos {sufijo}"

    try:
        assert sesion_usuario_prueba.post("/monedas-digitales/crear", data={"nombre_digital": dig_uno, "simbolo_digital": "DU1", "estado_digital": "1"}).status_code == 200
        assert sesion_usuario_prueba.post("/monedas-digitales/crear", data={"nombre_digital": dig_dos, "simbolo_digital": "DU2", "estado_digital": "1"}).status_code == 200

        # Duplicado al crear
        res_dup = sesion_usuario_prueba.post("/monedas-digitales/crear", data={"nombre_digital": dig_uno, "simbolo_digital": "DU1", "estado_digital": "1"})
        assert res_dup.status_code == 400
        assert _contar_digitales(dig_uno) == 1

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_mon_digital FROM moneda_digital WHERE nombre_digital = %s", (dig_dos,))
            cod_dos = cur.fetchone()["cod_mon_digital"]
            cur.close()
        finally:
            con.close()

        # Duplicado al editar
        res_dup_edit = sesion_usuario_prueba.post(f"/monedas-digitales/editar/{cod_dos}", data={"nombre_digital": dig_uno, "simbolo_digital": "DU2", "estado_digital": "1"})
        assert res_dup_edit.status_code == 400
        assert _contar_digitales(dig_uno) == 1
    finally:
        _limpiar_digitales(dig_uno, dig_dos)


# ==============================================================================
# 3. MANEJO DE IDS INEXISTENTES (REGULAR Y DIGITAL)
# ==============================================================================

def test_humo_monedas_ids_inexistentes_controlados(sesion_usuario_prueba):
    """Humo: Editar o eliminar ID 999999 (regular y digital) responde error controlado y no 500."""
    res_edit = sesion_usuario_prueba.post("/monedas/editar/999999", data={"nombre_moneda": "Fantasma", "simbolo": "F", "estado": "Activo"})
    assert res_edit.status_code in (400, 404)
    assert res_edit.get_json()["status"] == "error"

    res_elim = sesion_usuario_prueba.post("/monedas/eliminar/999999")
    assert res_elim.status_code in (400, 404)
    assert res_elim.get_json()["status"] == "error"

    res_edit_dig = sesion_usuario_prueba.post("/monedas-digitales/editar/999999", data={"nombre_digital": "Fantasma", "simbolo_digital": "F", "estado_digital": "1"})
    assert res_edit_dig.status_code in (400, 404)
    assert res_edit_dig.get_json()["status"] == "error"

    res_elim_dig = sesion_usuario_prueba.post("/monedas-digitales/eliminar/999999")
    assert res_elim_dig.status_code in (400, 404)
    assert res_elim_dig.get_json()["status"] == "error"


# ==============================================================================
# 4. SEGURIDAD Y CONTROL DE ACCESO (SIN SESIÓN Y ROL SIN PRIVILEGIOS)
# ==============================================================================

def test_humo_monedas_sin_sesion_bloquea_rutas(client):
    """Humo Seguridad: Peticiones sin iniciar sesión bloquean las 7 rutas de monedas."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nom_mon = f"Mon Intruso {sufijo}"
    nom_dig = f"Dig Intruso {sufijo}"

    try:
        assert client.get("/monedas/gestion").status_code in (302, 401, 403)
        assert client.post("/monedas/crear", data={"nombre_moneda": nom_mon, "simbolo": "MI", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/monedas/editar/1", data={"nombre_moneda": "Hack", "simbolo": "H", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/monedas/eliminar/1").status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/crear", data={"nombre_digital": nom_dig, "simbolo_digital": "DI", "estado_digital": "1"}).status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/editar/1", data={"nombre_digital": "Hack", "simbolo_digital": "H", "estado_digital": "1"}).status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/eliminar/1").status_code in (302, 401, 403)

        assert _contar_monedas(nom_mon) == 0
        assert _contar_digitales(nom_dig) == 0
    finally:
        _limpiar_monedas(nom_mon)
        _limpiar_digitales(nom_dig)


def test_humo_monedas_rol_sin_privilegios_bloquea_rutas(client):
    """Humo Seguridad: Un rol sin permisos en 'Monedas' en seguridad_test no puede acceder ni modificar."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nom_mon = f"Mon SinPerm {sufijo}"
    nom_dig = f"Dig SinPerm {sufijo}"

    con_seg = ConexionBD.obtener_conexion_seguridad()
    try:
        cur = con_seg.cursor(dictionary=True)
        cur.execute("""
            SELECT r.cod_rol
            FROM t_rol r
            WHERE r.cod_rol != 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM t_rol_permiso rp
                  INNER JOIN t_permiso p ON rp.cod_permiso = p.cod_permiso
                  INNER JOIN t_modulo m ON p.cod_modulo = m.cod_modulo
                  WHERE rp.cod_rol = r.cod_rol AND m.nombre_modulo = 'Monedas'
              )
            LIMIT 1
        """)
        fila_rol = cur.fetchone()
        cur.close()
    finally:
        con_seg.close()

    cod_rol_sin_permiso = fila_rol["cod_rol"] if fila_rol else 4

    with client.session_transaction() as sess:
        sess["usuario_nombre"] = "Usuario Sin Privilegios"
        sess["cedula_usuario"] = "99999999"
        sess["cod_rol"] = cod_rol_sin_permiso
        sess["rol"] = cod_rol_sin_permiso

    try:
        assert client.get("/monedas/gestion").status_code in (302, 401, 403)
        assert client.post("/monedas/crear", data={"nombre_moneda": nom_mon, "simbolo": "MP", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/monedas/editar/1", data={"nombre_moneda": "Hack", "simbolo": "H", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/monedas/eliminar/1").status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/crear", data={"nombre_digital": nom_dig, "simbolo_digital": "DP", "estado_digital": "1"}).status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/editar/1", data={"nombre_digital": "Hack", "simbolo_digital": "H", "estado_digital": "1"}).status_code in (302, 401, 403)
        assert client.post("/monedas-digitales/eliminar/1").status_code in (302, 401, 403)

        assert _contar_monedas(nom_mon) == 0
        assert _contar_digitales(nom_dig) == 0
    finally:
        _limpiar_monedas(nom_mon)
        _limpiar_digitales(nom_dig)