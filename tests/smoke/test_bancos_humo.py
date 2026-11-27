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


def _contar_bancos_por_nombre(nombre):
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM banco WHERE nombre_banco = %s", (nombre,))
        total = cur.fetchone()[0]
        cur.close()
        return total
    finally:
        con.close()


def _limpiar_bancos_por_nombre(*nombres):
    nombres_validos = [n for n in nombres if n]
    if not nombres_validos:
        return
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        placeholders = ",".join(["%s"] * len(nombres_validos))
        cur.execute(f"DELETE FROM banco WHERE nombre_banco IN ({placeholders})", tuple(nombres_validos))
        con.commit()
        cur.close()
    finally:
        con.close()


# ==============================================================================
# 1. ARRANQUE, CONEXIONES Y CAMINO FELIZ (CRUD REAL)
# ==============================================================================

def test_humo_app_y_conexiones_bd_prueba(client):
    """Humo: Verifica arranque de Flask, conexión a automall_test/seguridad_test y rutas base."""
    con_neg = ConexionBD.obtener_conexion()
    con_seg = ConexionBD.obtener_conexion_seguridad()
    try:
        assert con_neg.database == "automall_test"
        assert con_seg.database == "seguridad_test"
        assert con_neg.is_connected()
        assert con_seg.is_connected()
    finally:
        con_neg.close()
        con_seg.close()

    assert client.get("/").status_code == 200
    assert client.get("/login").status_code == 200


def test_humo_bancos_gestion_get_real(sesion_usuario_prueba):
    """Humo: Verifica que GET /bancos/gestion cargue la vista real consultando automall_test."""
    response = sesion_usuario_prueba.get("/bancos/gestion")

    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_humo_bancos_ciclo_crud_real_automall_test(sesion_usuario_prueba):
    """Humo End-to-End: Crear -> Editar -> Eliminar lógico en /bancos contra automall_test."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_inicial = f"Banco Smoke {sufijo}"
    nombre_editado = f"Banco Smoke Edit {sufijo}"
    cod_banco_creado = None

    try:
        # 1. CREAR
        res_crear = sesion_usuario_prueba.post(
            "/bancos/gestion",
            data={"nombre_banco": nombre_inicial, "estado": "Activo"}
        )
        assert res_crear.status_code == 200
        assert res_crear.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_banco, nombre_banco, estado FROM banco WHERE nombre_banco = %s", (nombre_inicial,))
            fila = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila is not None
        cod_banco_creado = fila["cod_banco"]

        # 2. EDITAR
        res_editar = sesion_usuario_prueba.post(
            f"/bancos/editar/{cod_banco_creado}",
            data={"nombre_banco": nombre_editado, "estado": "Activo"}
        )
        assert res_editar.status_code == 200
        assert res_editar.get_json()["status"] == "success"

        # 3. ELIMINAR LÓGICO
        res_eliminar = sesion_usuario_prueba.post(f"/bancos/eliminar/{cod_banco_creado}")
        assert res_eliminar.status_code == 200
        assert res_eliminar.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT nombre_banco, estado FROM banco WHERE cod_banco = %s", (cod_banco_creado,))
            fila_final = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila_final["nombre_banco"] == nombre_editado
        assert fila_final["estado"] == "Inactivo"

    finally:
        _limpiar_bancos_por_nombre(nombre_inicial, nombre_editado)


# ==============================================================================
# 2. VALIDACIONES DE ENTRADA Y REGLAS DE NEGOCIO (CAMINO TRISTE REAL)
# ==============================================================================

@pytest.mark.parametrize("payload", [
    {},                                                 # Sin parámetro nombre_banco
    {"nombre_banco": "", "estado": "Activo"},           # Vacío
    {"nombre_banco": "   ", "estado": "Activo"},        # Solo espacios
    {"nombre_banco": "A", "estado": "Activo"},          # Muy corto (< 2)
    {"nombre_banco": "B" * 51, "estado": "Activo"},     # Excede VARCHAR(50)
])
def test_humo_bancos_crear_rechaza_entradas_invalidas(sesion_usuario_prueba, payload):
    """Humo (Camino triste): Rechaza nombres vacíos, faltantes, cortos o > 50 chars con HTTP 400."""
    response = sesion_usuario_prueba.post("/bancos/gestion", data=payload)

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["status"] == "error"
    assert "Validación:" in json_data["message"]


@pytest.mark.parametrize("nombre_invalido", ["", "   ", "X", "B" * 51])
def test_humo_bancos_editar_rechaza_entradas_invalidas(sesion_usuario_prueba, nombre_invalido):
    """Humo (Camino triste): Rechaza edición con nombre vacío, corto o > 50 chars sin alterar BD."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_real = f"Banco Val Edit {sufijo}"

    try:
        res_crear = sesion_usuario_prueba.post(
            "/bancos/gestion",
            data={"nombre_banco": nombre_real, "estado": "Activo"}
        )
        assert res_crear.status_code == 200

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_banco FROM banco WHERE nombre_banco = %s", (nombre_real,))
            cod_banco = cur.fetchone()["cod_banco"]
            cur.close()
        finally:
            con.close()

        res_edit = sesion_usuario_prueba.post(
            f"/bancos/editar/{cod_banco}",
            data={"nombre_banco": nombre_invalido, "estado": "Activo"}
        )
        assert res_edit.status_code == 400
        assert res_edit.get_json()["status"] == "error"
        assert _contar_bancos_por_nombre(nombre_real) == 1
    finally:
        _limpiar_bancos_por_nombre(nombre_real)


def test_humo_bancos_rechaza_duplicados_en_creacion_y_edicion(sesion_usuario_prueba):
    """Humo (Integridad BD): Rechaza crear o renombrar un banco con un nombre ya existente."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_uno = f"Banco Dup Uno {sufijo}"
    nombre_dos = f"Banco Dup Dos {sufijo}"

    try:
        # Crear dos bancos válidos distintos
        assert sesion_usuario_prueba.post("/bancos/gestion", data={"nombre_banco": nombre_uno, "estado": "Activo"}).status_code == 200
        assert sesion_usuario_prueba.post("/bancos/gestion", data={"nombre_banco": nombre_dos, "estado": "Activo"}).status_code == 200

        # 1. Intentar duplicar al crear
        res_dup_crear = sesion_usuario_prueba.post(
            "/bancos/gestion",
            data={"nombre_banco": nombre_uno, "estado": "Activo"}
        )
        assert res_dup_crear.status_code == 400
        assert res_dup_crear.get_json()["status"] == "error"
        assert _contar_bancos_por_nombre(nombre_uno) == 1

        # 2. Intentar renombrar el banco dos con el nombre del banco uno
        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_banco FROM banco WHERE nombre_banco = %s", (nombre_dos,))
            cod_dos = cur.fetchone()["cod_banco"]
            cur.close()
        finally:
            con.close()

        res_dup_editar = sesion_usuario_prueba.post(
            f"/bancos/editar/{cod_dos}",
            data={"nombre_banco": nombre_uno, "estado": "Activo"}
        )
        assert res_dup_editar.status_code == 400
        assert res_dup_editar.get_json()["status"] == "error"
        assert _contar_bancos_por_nombre(nombre_uno) == 1

    finally:
        _limpiar_bancos_por_nombre(nombre_uno, nombre_dos)


def test_humo_bancos_estado_invalido_rechazado(sesion_usuario_prueba):
    """Humo (Camino triste): Verifica rechazo al enviar un estado distinto a 'Activo' o 'Inactivo'."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_estado_malo = f"Banco Est Malo {sufijo}"

    try:
        response = sesion_usuario_prueba.post(
            "/bancos/gestion",
            data={"nombre_banco": nombre_estado_malo, "estado": "EstadoInvalido"}
        )
        assert response.status_code == 400
        assert response.get_json()["status"] == "error"
        assert _contar_bancos_por_nombre(nombre_estado_malo) == 0
    finally:
        _limpiar_bancos_por_nombre(nombre_estado_malo)


# ==============================================================================
# 3. MANEJO DE IDS INEXISTENTES
# ==============================================================================

def test_humo_bancos_ids_inexistentes_controlados(sesion_usuario_prueba):
    """
    Humo: Verifica que editar o eliminar el ID inexistente 999999 no genere error 500
    y responda con error controlado (400/404).
    """
    res_edit = sesion_usuario_prueba.post(
        "/bancos/editar/999999",
        data={"nombre_banco": "Banco Fantasma", "estado": "Activo"}
    )
    assert res_edit.status_code != 500
    assert res_edit.status_code in (400, 404)
    assert res_edit.get_json()["status"] == "error"

    res_elim = sesion_usuario_prueba.post("/bancos/eliminar/999999")
    assert res_elim.status_code != 500
    assert res_elim.status_code in (400, 404)
    assert res_elim.get_json()["status"] == "error"


# ==============================================================================
# 4. SEGURIDAD Y CONTROL DE ACCESO (SIN SESIÓN Y ROL SIN PRIVILEGIOS)
# ==============================================================================

def test_humo_bancos_sin_sesion_bloquea_rutas(client):
    """Humo Seguridad: Peticiones sin iniciar sesión deben ser bloqueadas (302/401/403)."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_intruso = f"Banco Intruso {sufijo}"

    try:
        assert client.get("/bancos/gestion").status_code in (302, 401, 403)
        assert client.post("/bancos/gestion", data={"nombre_banco": nombre_intruso, "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/bancos/editar/1", data={"nombre_banco": "Hack", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/bancos/eliminar/1").status_code in (302, 401, 403)

        assert _contar_bancos_por_nombre(nombre_intruso) == 0
    finally:
        _limpiar_bancos_por_nombre(nombre_intruso)


def test_humo_bancos_rol_sin_privilegios_bloquea_rutas(client):
    """Humo Seguridad: Un usuario autenticado con un rol sin permisos en Bancos no puede acceder ni modificar."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_sin_perm = f"Banco SinPerm {sufijo}"

    # Buscar un rol existente en seguridad_test sin permiso sobre 'Bancos' (ej. rol 4 Cliente)
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
                  WHERE rp.cod_rol = r.cod_rol AND m.nombre_modulo = 'Bancos'
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
        assert client.get("/bancos/gestion").status_code in (302, 401, 403)
        assert client.post("/bancos/gestion", data={"nombre_banco": nombre_sin_perm, "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/bancos/editar/1", data={"nombre_banco": "Cambio", "estado": "Activo"}).status_code in (302, 401, 403)
        assert client.post("/bancos/eliminar/1").status_code in (302, 401, 403)

        assert _contar_bancos_por_nombre(nombre_sin_perm) == 0
    finally:
        _limpiar_bancos_por_nombre(nombre_sin_perm)