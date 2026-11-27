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


def _contar_metodos_por_nombre(nombre):
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM metodo_pago WHERE nombre_metodo = %s", (nombre,))
        total = cur.fetchone()[0]
        cur.close()
        return total
    finally:
        con.close()


def _limpiar_metodos_por_nombre(*nombres):
    nombres_validos = [n for n in nombres if n]
    if not nombres_validos:
        return
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor()
        placeholders = ",".join(["%s"] * len(nombres_validos))
        cur.execute(f"DELETE FROM metodo_pago WHERE nombre_metodo IN ({placeholders})", tuple(nombres_validos))
        con.commit()
        cur.close()
    finally:
        con.close()


# ==============================================================================
# 1. CAMINO FELIZ: VISTA GET Y CICLO CRUD REAL EN AUTOMALL_TEST
# ==============================================================================

def test_humo_metodos_gestion_get_real(sesion_usuario_prueba):
    """Humo: Verifica que GET /metodos-pago/gestion cargue la vista real desde automall_test."""
    con = ConexionBD.obtener_conexion()
    try:
        assert con.database == "automall_test"
    finally:
        con.close()

    response = sesion_usuario_prueba.get("/metodos-pago/gestion")

    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_humo_metodos_ciclo_crud_real_automall_test(sesion_usuario_prueba):
    """Humo End-to-End: Crear -> Editar -> Eliminar lógico en /metodos-pago contra automall_test."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_inicial = f"Metodo Smoke {sufijo}"
    nombre_editado = f"Metodo Edit {sufijo}"
    cod_metodo_creado = None

    try:
        # 1. CREAR
        res_crear = sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_inicial, "requiere_referencia": "1", "estado": "Activo"}
        )
        assert res_crear.status_code == 200
        assert res_crear.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute(
                "SELECT cod_metodo, nombre_metodo, requiere_referencia, estado FROM metodo_pago WHERE nombre_metodo = %s",
                (nombre_inicial,)
            )
            fila = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila is not None, "El método de pago creado no se guardó en automall_test.metodo_pago"
        cod_metodo_creado = fila["cod_metodo"]
        assert fila["requiere_referencia"] == 1

        # 2. EDITAR
        res_editar = sesion_usuario_prueba.post(
            f"/metodos-pago/editar/{cod_metodo_creado}",
            data={"nombre_metodo": nombre_editado, "requiere_referencia": "0", "estado": "Activo"}
        )
        assert res_editar.status_code == 200
        assert res_editar.get_json()["status"] == "success"

        # 3. ELIMINAR LÓGICO
        res_eliminar = sesion_usuario_prueba.post(f"/metodos-pago/eliminar/{cod_metodo_creado}")
        assert res_eliminar.status_code == 200
        assert res_eliminar.get_json()["status"] == "success"

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute(
                "SELECT nombre_metodo, requiere_referencia, estado FROM metodo_pago WHERE cod_metodo = %s",
                (cod_metodo_creado,)
            )
            fila_final = cur.fetchone()
            cur.close()
        finally:
            con.close()

        assert fila_final["nombre_metodo"] == nombre_editado
        assert fila_final["requiere_referencia"] == 0
        assert fila_final["estado"] == "Inactivo"

    finally:
        _limpiar_metodos_por_nombre(nombre_inicial, nombre_editado)


# ==============================================================================
# 2. VALIDACIONES DE ENTRADA Y REGLAS DE NEGOCIO (CAMINO TRISTE REAL)
# ==============================================================================

@pytest.mark.parametrize("payload", [
    {},
    {"nombre_metodo": "", "requiere_referencia": "1", "estado": "Activo"},
    {"nombre_metodo": "   ", "requiere_referencia": "1", "estado": "Activo"},
    {"nombre_metodo": "M", "requiere_referencia": "0", "estado": "Activo"},
    {"nombre_metodo": "M" * 51, "requiere_referencia": "1", "estado": "Activo"},
])
def test_humo_metodos_crear_rechaza_entradas_invalidas(sesion_usuario_prueba, payload):
    """Humo (Camino triste): Rechaza nombres vacíos, faltantes, cortos o > 50 chars con HTTP 400."""
    response = sesion_usuario_prueba.post("/metodos-pago/gestion", data=payload)

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["status"] == "error"
    assert "Validación:" in json_data["message"]


@pytest.mark.parametrize("nombre_invalido", ["", "   ", "X", "M" * 51])
def test_humo_metodos_editar_rechaza_entradas_invalidas(sesion_usuario_prueba, nombre_invalido):
    """Humo (Camino triste): Rechaza edición con nombre vacío, corto o > 50 chars sin alterar BD."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_real = f"Metodo Val {sufijo}"

    try:
        res_crear = sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_real, "requiere_referencia": "1", "estado": "Activo"}
        )
        assert res_crear.status_code == 200

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_metodo FROM metodo_pago WHERE nombre_metodo = %s", (nombre_real,))
            cod_metodo = cur.fetchone()["cod_metodo"]
            cur.close()
        finally:
            con.close()

        res_edit = sesion_usuario_prueba.post(
            f"/metodos-pago/editar/{cod_metodo}",
            data={"nombre_metodo": nombre_invalido, "requiere_referencia": "1", "estado": "Activo"}
        )
        assert res_edit.status_code == 400
        assert res_edit.get_json()["status"] == "error"
        assert _contar_metodos_por_nombre(nombre_real) == 1
    finally:
        _limpiar_metodos_por_nombre(nombre_real)


def test_humo_metodos_rechaza_duplicados_en_creacion_y_edicion(sesion_usuario_prueba):
    """Humo (Integridad BD): Rechaza crear o renombrar un método con un nombre ya existente."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_uno = f"Metodo Dup Uno {sufijo}"
    nombre_dos = f"Metodo Dup Dos {sufijo}"

    try:
        assert sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_uno, "requiere_referencia": "1", "estado": "Activo"}
        ).status_code == 200
        assert sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_dos, "requiere_referencia": "0", "estado": "Activo"}
        ).status_code == 200

        # 1. Duplicado al crear
        res_dup_crear = sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_uno, "requiere_referencia": "1", "estado": "Activo"}
        )
        assert res_dup_crear.status_code == 400
        assert res_dup_crear.get_json()["status"] == "error"
        assert _contar_metodos_por_nombre(nombre_uno) == 1

        # 2. Duplicado al editar
        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT cod_metodo FROM metodo_pago WHERE nombre_metodo = %s", (nombre_dos,))
            cod_dos = cur.fetchone()["cod_metodo"]
            cur.close()
        finally:
            con.close()

        res_dup_editar = sesion_usuario_prueba.post(
            f"/metodos-pago/editar/{cod_dos}",
            data={"nombre_metodo": nombre_uno, "requiere_referencia": "1", "estado": "Activo"}
        )
        assert res_dup_editar.status_code == 400
        assert res_dup_editar.get_json()["status"] == "error"
        assert _contar_metodos_por_nombre(nombre_uno) == 1

    finally:
        _limpiar_metodos_por_nombre(nombre_uno, nombre_dos)


def test_humo_metodos_estado_y_referencia_invalidos_rechazados(sesion_usuario_prueba):
    """Humo (Camino triste): Verifica rechazo al enviar estado o requiere_referencia inválidos."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_est = f"Metodo Est Malo {sufijo}"
    nombre_ref = f"Metodo Ref Mala {sufijo}"

    try:
        res_est = sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_est, "requiere_referencia": "1", "estado": "EstadoInvalido"}
        )
        assert res_est.status_code == 400
        assert res_est.get_json()["status"] == "error"
        assert _contar_metodos_por_nombre(nombre_est) == 0

        res_ref = sesion_usuario_prueba.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_ref, "requiere_referencia": "no_numerico", "estado": "Activo"}
        )
        assert res_ref.status_code == 400
        assert res_ref.get_json()["status"] == "error"
        assert _contar_metodos_por_nombre(nombre_ref) == 0
    finally:
        _limpiar_metodos_por_nombre(nombre_est, nombre_ref)


# ==============================================================================
# 3. MANEJO DE IDS INEXISTENTES
# ==============================================================================

def test_humo_metodos_ids_inexistentes_controlados(sesion_usuario_prueba):
    """Humo: Verifica que editar o eliminar ID 999999 devuelva error controlado (400/404) y no 500."""
    res_edit = sesion_usuario_prueba.post(
        "/metodos-pago/editar/999999",
        data={"nombre_metodo": "Metodo Fantasma", "requiere_referencia": "1", "estado": "Activo"}
    )
    assert res_edit.status_code != 500
    assert res_edit.status_code in (400, 404)
    assert res_edit.get_json()["status"] == "error"

    res_elim = sesion_usuario_prueba.post("/metodos-pago/eliminar/999999")
    assert res_elim.status_code != 500
    assert res_elim.status_code in (400, 404)
    assert res_elim.get_json()["status"] == "error"


# ==============================================================================
# 4. SEGURIDAD Y CONTROL DE ACCESO (SIN SESIÓN Y ROL SIN PRIVILEGIOS)
# ==============================================================================

def test_humo_metodos_sin_sesion_bloquea_rutas(client):
    """Humo Seguridad: Peticiones sin iniciar sesión deben ser bloqueadas (302/401/403)."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_intruso = f"Metodo Intruso {sufijo}"

    try:
        assert client.get("/metodos-pago/gestion").status_code in (302, 401, 403)
        assert client.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_intruso, "requiere_referencia": "1", "estado": "Activo"}
        ).status_code in (302, 401, 403)
        assert client.post(
            "/metodos-pago/editar/1",
            data={"nombre_metodo": "Hack", "requiere_referencia": "1", "estado": "Activo"}
        ).status_code in (302, 401, 403)
        assert client.post("/metodos-pago/eliminar/1").status_code in (302, 401, 403)

        assert _contar_metodos_por_nombre(nombre_intruso) == 0
    finally:
        _limpiar_metodos_por_nombre(nombre_intruso)


def test_humo_metodos_rol_sin_privilegios_bloquea_rutas(client):
    """Humo Seguridad: Un rol sin permisos en 'Metodo' en seguridad_test no puede acceder ni modificar."""
    sufijo = uuid.uuid4().hex[:6].upper()
    nombre_sin_perm = f"Metodo SinPerm {sufijo}"

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
                  WHERE rp.cod_rol = r.cod_rol AND m.nombre_modulo = 'Metodo'
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
        assert client.get("/metodos-pago/gestion").status_code in (302, 401, 403)
        assert client.post(
            "/metodos-pago/gestion",
            data={"nombre_metodo": nombre_sin_perm, "requiere_referencia": "1", "estado": "Activo"}
        ).status_code in (302, 401, 403)
        assert client.post(
            "/metodos-pago/editar/1",
            data={"nombre_metodo": "Cambio", "requiere_referencia": "1", "estado": "Activo"}
        ).status_code in (302, 401, 403)
        assert client.post("/metodos-pago/eliminar/1").status_code in (302, 401, 403)

        assert _contar_metodos_por_nombre(nombre_sin_perm) == 0
    finally:
        _limpiar_metodos_por_nombre(nombre_sin_perm)