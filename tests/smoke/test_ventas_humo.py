import uuid
import pytest
from models.db import ConexionBD


@pytest.fixture(autouse=True)
def entorno_testing_bd(monkeypatch):
    """Garantiza que toda la sesión de pruebas de humo apunte a automall_test y seguridad_test."""
    monkeypatch.setenv("FLASK_ENV", "testing")


@pytest.fixture
def usuario_prueba_bd():
    """Obtiene los datos reales del usuario prueba@gmail.com desde seguridad_test."""
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
    return usuario


@pytest.fixture
def sesion_usuario_prueba(client, usuario_prueba_bd):
    """Inicia sesión real con el usuario de prueba en Flask."""
    with client.session_transaction() as sess:
        sess["usuario_nombre"] = usuario_prueba_bd["nombre"]
        sess["cedula_usuario"] = usuario_prueba_bd["cedula_usuario"]
        sess["cod_rol"] = usuario_prueba_bd["cod_rol"]
        sess["rol"] = usuario_prueba_bd["cod_rol"]
    return client


@pytest.fixture
def vehiculo_disponible_temporal():
    """
    Obtiene un vehículo con entrada en catalogo en automall_test y asegura temporalmente
    su estado 'Disponible' durante la prueba, restaurando su estado original al finalizar.
    """
    con = ConexionBD.obtener_conexion()
    assert con.database == "automall_test"
    cur = con.cursor(dictionary=True)

    placa = None
    estado_original = None

    try:
        cur.execute("""
            SELECT v.placa, v.estado, c.precio
            FROM vehiculo v
            INNER JOIN catalogo c ON v.placa = c.placa
            ORDER BY (v.estado = 'Disponible') DESC
            LIMIT 1
        """)
        vehiculo = cur.fetchone()
        if not vehiculo:
            pytest.skip("No hay vehículos con catálogo en automall_test para probar el flujo real de ventas.")

        placa = vehiculo["placa"]
        estado_original = vehiculo["estado"]
        precio = float(vehiculo["precio"] or 0)
        if precio <= 200:
            precio = 1000.0

        if estado_original != "Disponible":
            cur.execute("UPDATE vehiculo SET estado = 'Disponible' WHERE placa = %s", (placa,))
            con.commit()

        # Buscar una moneda USD y un cliente real en seguridad_test
        cur.execute("""
            SELECT cod_moneda
            FROM moneda
            WHERE LOWER(nombre_moneda) NOT LIKE '%bol%'
              AND LOWER(IFNULL(simbolo, '')) NOT LIKE '%bs%'
            LIMIT 1
        """)
        moneda = cur.fetchone()
        if not moneda:
            cur.execute("SELECT cod_moneda FROM moneda LIMIT 1")
            moneda = cur.fetchone()
        cod_moneda = moneda["cod_moneda"] if moneda else 1

        yield {"placa": placa, "precio": precio, "cod_moneda": cod_moneda}
    finally:
        try:
            if placa is not None and estado_original is not None:
                cur.execute("UPDATE vehiculo SET estado = %s WHERE placa = %s", (estado_original, placa))
                con.commit()
        finally:
            cur.close()
            con.close()


def _limpiar_venta_completa(cod_venta):
    if not cod_venta:
        return
    con = ConexionBD.obtener_conexion()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT cod_cuentas FROM cuentas_por_cobrar WHERE cod_venta = %s", (cod_venta,))
        cuentas = [r["cod_cuentas"] for r in cur.fetchall()]
        if cuentas:
            ph_c = ",".join(["%s"] * len(cuentas))
            cur.execute(f"SELECT cod_pagos FROM pago_cuentas WHERE cod_cuentas IN ({ph_c})", tuple(cuentas))
            pagos = [r["cod_pagos"] for r in cur.fetchall()]
            if pagos:
                ph_p = ",".join(["%s"] * len(pagos))
                cur.execute(f"DELETE FROM det_pago WHERE cod_pagos IN ({ph_p})", tuple(pagos))
                cur.execute(f"DELETE FROM pago_cuentas WHERE cod_pagos IN ({ph_p})", tuple(pagos))
            cur.execute(f"DELETE FROM cuentas_por_cobrar WHERE cod_cuentas IN ({ph_c})", tuple(cuentas))
        cur.execute("DELETE FROM det_venta WHERE cod_venta = %s", (cod_venta,))
        cur.execute("DELETE FROM ventas WHERE cod_venta = %s", (cod_venta,))
        con.commit()
    finally:
        cur.close()
        con.close()


# ==============================================================================
# 1. CAMINO FELIZ: VISTAS GET Y APIS DE BÚSQUEDA REALES
# ==============================================================================

def test_humo_ventas_vistas_get_reales(sesion_usuario_prueba):
    """Humo: Verifica carga real de /ventas/registrar_venta y /ventas/lista_ventas desde BD de pruebas."""
    assert sesion_usuario_prueba.get("/ventas/registrar_venta").status_code == 200
    assert sesion_usuario_prueba.get("/ventas/lista_ventas").status_code == 200


def test_humo_ventas_api_buscar_cliente_real_y_404(sesion_usuario_prueba, usuario_prueba_bd):
    """Humo: Busca el cliente/usuario real en seguridad_test y verifica 404 ante término inexistente."""
    cedula = str(usuario_prueba_bd["cedula_usuario"])

    res_ok = sesion_usuario_prueba.get(f"/ventas/api/cliente/{cedula}")
    assert res_ok.status_code == 200
    assert res_ok.get_json()["exito"] is True

    res_404 = sesion_usuario_prueba.get("/ventas/api/cliente/NOEXISTE999999")
    assert res_404.status_code == 404
    assert res_404.get_json()["exito"] is False


def test_humo_ventas_api_buscar_vehiculo_real_y_404(sesion_usuario_prueba, vehiculo_disponible_temporal):
    """Humo: Busca un vehículo disponible real en automall_test y verifica 404 para placa inexistente."""
    placa = vehiculo_disponible_temporal["placa"]

    res_ok = sesion_usuario_prueba.get(f"/ventas/api/vehiculo/{placa}")
    assert res_ok.status_code == 200
    json_ok = res_ok.get_json()
    assert json_ok["exito"] is True
    assert json_ok["vehiculo"]["placa"] == placa
    assert isinstance(json_ok["vehiculo"]["precio"], float)

    res_404 = sesion_usuario_prueba.get("/ventas/api/vehiculo/ZZZ999NOEXISTE")
    assert res_404.status_code == 404
    assert res_404.get_json()["exito"] is False


# ==============================================================================
# 2. REGISTRO RÁPIDO DE CLIENTE EN SEGURIDAD_TEST
# ==============================================================================

def test_humo_ventas_api_registrar_cliente_rapido_real_y_validaciones(sesion_usuario_prueba, usuario_prueba_bd):
    """Humo: Registra cliente temporal en seguridad_test (201), rechaza duplicado (400) y limpia."""
    sufijo_num = f"{uuid.uuid4().int % 900000 + 100000}"
    cedula_temp = f"28{sufijo_num}"
    correo_temp = f"smoke_{uuid.uuid4().hex[:6]}@example.com"

    try:
        # 1. Campos faltantes -> 400
        res_faltan = sesion_usuario_prueba.post(
            "/ventas/api/cliente/registrar",
            json={"cedula": cedula_temp, "nombre": "Ana"}
        )
        assert res_faltan.status_code == 400
        assert res_faltan.get_json()["exito"] is False

        # 2. Registro exitoso -> 201 en seguridad_test.t_usuario
        payload = {
            "cedula": cedula_temp,
            "nombre": "Ana",
            "apellido": "Smoke",
            "telefono": "04149876543",
            "direccion": "Lara",
            "correo": correo_temp,
        }
        res_ok = sesion_usuario_prueba.post("/ventas/api/cliente/registrar", json=payload)
        assert res_ok.status_code == 201
        assert res_ok.get_json()["exito"] is True

        # 3. Duplicado con la misma cédula/correo -> 400
        res_dup = sesion_usuario_prueba.post("/ventas/api/cliente/registrar", json=payload)
        assert res_dup.status_code == 400
        assert res_dup.get_json()["exito"] is False
    finally:
        con_seg = ConexionBD.obtener_conexion_seguridad()
        try:
            cur = con_seg.cursor()
            cur.execute("DELETE FROM t_usuario WHERE cedula_usuario = %s", (cedula_temp,))
            con_seg.commit()
            cur.close()
        finally:
            con_seg.close()


# ==============================================================================
# 3. FLUJO TRANSACCIONAL COMPLETO: REGISTRAR -> FACTURA PDF -> EDITAR -> ANULAR
# ==============================================================================

def test_humo_ventas_ciclo_completo_real_con_pdf_edicion_y_anulacion(
    sesion_usuario_prueba, usuario_prueba_bd, vehiculo_disponible_temporal
):
    """
    Humo End-to-End: Registra venta real en automall_test -> genera factura PDF ->
    edita cuenta por cobrar -> anula venta liberando vehículo -> limpia todo en finally.
    """
    placa = vehiculo_disponible_temporal["placa"]
    precio = vehiculo_disponible_temporal["precio"]
    cod_moneda = vehiculo_disponible_temporal["cod_moneda"]
    cedula_cliente = usuario_prueba_bd["cedula_usuario"]
    cod_venta_creada = None

    try:
        # 1. REGISTRAR VENTA (POST /ventas/registrar_venta)
        payload_venta = {
            "cedula_cliente": cedula_cliente,
            "placa": placa,
            "tipo_venta": "credito",
            "poder": False,
            "traspaso_papel": False,
            "monto_recibido": 100.00,
            "precio_vehiculo": precio,
            "deuda_pendiente": round(precio - 100.00, 2),
            "fecha_vencimiento": "2027-12-31",
            "cod_metodo": "2",  # Efectivo
            "cod_moneda": cod_moneda,
            "referencia": "",
        }
        res_reg = sesion_usuario_prueba.post("/ventas/registrar_venta", json=payload_venta)
        assert res_reg.status_code == 200
        json_reg = res_reg.get_json()
        assert json_reg["exito"] is True
        cod_venta_creada = json_reg["cod_venta"]
        assert json_reg["pdf_url"] == f"/ventas/factura/{cod_venta_creada}"

        # Confirmar vehículo marcado como 'Vendido' en automall_test
        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT estado FROM vehiculo WHERE placa = %s", (placa,))
            assert cur.fetchone()["estado"] == "Vendido"
            cur.close()
        finally:
            con.close()

        # 2. GENERAR FACTURA PDF REAL (GET /ventas/factura/<cod_venta>)
        res_pdf = sesion_usuario_prueba.get(f"/ventas/factura/{cod_venta_creada}")
        assert res_pdf.status_code == 200
        assert res_pdf.content_type == "application/pdf"
        assert res_pdf.data.startswith(b"%PDF")
        assert f"comprobante_venta_{cod_venta_creada}.pdf" in res_pdf.headers.get("Content-Disposition", "")

        # 3. EDITAR VENTA (POST /ventas/editar)
        nueva_deuda_total = precio + 200.00
        res_edit = sesion_usuario_prueba.post(
            "/ventas/editar",
            data={
                "cod_venta": str(cod_venta_creada),
                "cedula_cliente": str(cedula_cliente),
                "tipo_venta": "credito",
                "deuda_total": str(nueva_deuda_total),
                "fecha_vencimiento": "2028-01-15",
            },
            follow_redirects=False
        )
        assert res_edit.status_code == 302
        assert "/ventas/lista_ventas" in res_edit.location

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT deuda_total, deuda FROM cuentas_por_cobrar WHERE cod_venta = %s", (cod_venta_creada,))
            cxc_edit = cur.fetchone()
            cur.close()
        finally:
            con.close()
        assert float(cxc_edit["deuda_total"]) == nueva_deuda_total

        # 4. ANULAR / ELIMINAR VENTA (POST /ventas/eliminar/<id>)
        res_elim = sesion_usuario_prueba.post(f"/ventas/eliminar/{cod_venta_creada}", follow_redirects=False)
        assert res_elim.status_code == 302
        assert "/ventas/lista_ventas" in res_elim.location

        con = ConexionBD.obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT estado FROM ventas WHERE cod_venta = %s", (cod_venta_creada,))
            assert cur.fetchone()["estado"] == "Anulada"
            cur.execute("SELECT estado, deuda FROM cuentas_por_cobrar WHERE cod_venta = %s", (cod_venta_creada,))
            cxc_final = cur.fetchone()
            assert str(cxc_final["estado"]).lower() == "anulada"
            assert float(cxc_final["deuda"]) == 0.0
            cur.execute("SELECT estado FROM vehiculo WHERE placa = %s", (placa,))
            assert cur.fetchone()["estado"] == "Disponible"
            cur.close()
        finally:
            con.close()

    finally:
        _limpiar_venta_completa(cod_venta_creada)


# ==============================================================================
# 4. VALIDACIONES (CAMINO TRISTE) E IDS INEXISTENTES (999999)
# ==============================================================================

def test_humo_ventas_registrar_rechaza_json_vacio_y_datos_invalidos(sesion_usuario_prueba):
    """Humo (Camino triste): JSON vacío o datos inválidos retornan HTTP 400 controlado."""
    res_vacio = sesion_usuario_prueba.post("/ventas/registrar_venta", json={})
    assert res_vacio.status_code == 400
    assert res_vacio.get_json()["exito"] is False

    res_invalido = sesion_usuario_prueba.post(
        "/ventas/registrar_venta",
        json={"cedula_cliente": "", "placa": "", "monto_recibido": -50, "precio_vehiculo": 0}
    )
    assert res_invalido.status_code == 400
    assert res_invalido.get_json()["exito"] is False


def test_humo_ventas_editar_datos_invalidos_muestra_alerta(sesion_usuario_prueba):
    """Humo (Camino triste): Editar venta con monto negativo o inexistente no da 500 y muestra alerta."""
    res = sesion_usuario_prueba.post(
        "/ventas/editar",
        data={"cod_venta": "999999", "deuda_total": "-100", "fecha_vencimiento": "2027-01-01"},
        follow_redirects=False
    )
    assert res.status_code == 302
    with sesion_usuario_prueba.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert any(cat == "danger" for cat, _ in flashes)


def test_humo_ventas_ids_inexistentes_controlados(sesion_usuario_prueba):
    """Humo (IDs inexistentes): Factura PDF y eliminación de ID 999999 no deben caer en 500."""
    res_pdf = sesion_usuario_prueba.get("/ventas/factura/999999")
    assert res_pdf.status_code != 500
    assert res_pdf.status_code in (302, 400, 404)

    res_elim = sesion_usuario_prueba.post("/ventas/eliminar/999999", follow_redirects=False)
    assert res_elim.status_code != 500
    with sesion_usuario_prueba.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert any(cat == "danger" for cat, _ in flashes)


# ==============================================================================
# 5. SEGURIDAD Y CONTROL DE ACCESO (SIN SESIÓN Y ROL SIN PRIVILEGIOS)
# ==============================================================================

def test_humo_ventas_sin_sesion_bloquea_todas_las_rutas(client):
    """Humo Seguridad: Peticiones sin iniciar sesión bloquean las rutas de Ventas."""
    assert client.get("/ventas/registrar_venta").status_code in (302, 401, 403)
    assert client.get("/ventas/lista_ventas").status_code in (302, 401, 403)
    assert client.get("/ventas/api/cliente/12345678").status_code in (302, 401, 403)
    assert client.get("/ventas/api/vehiculo/ABC123").status_code in (302, 401, 403)
    assert client.get("/ventas/factura/1").status_code in (302, 401, 403)
    assert client.post("/ventas/api/cliente/registrar", json={"cedula": "123"}).status_code in (302, 401, 403)
    assert client.post("/ventas/registrar_venta", json={"placa": "ABC123"}).status_code in (302, 401, 403)
    assert client.post("/ventas/editar", data={"cod_venta": "1"}).status_code in (302, 401, 403)
    assert client.post("/ventas/eliminar/1").status_code in (302, 401, 403)


def test_humo_ventas_rol_sin_privilegios_bloquea_rutas_protegidas(client):
    """Humo Seguridad: Un rol sin permisos en 'Ventas' en seguridad_test no puede listar, crear, editar ni anular."""
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
                  WHERE rp.cod_rol = r.cod_rol AND m.nombre_modulo = 'Ventas'
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

    assert client.get("/ventas/lista_ventas").status_code in (302, 401, 403)
    assert client.post("/ventas/api/cliente/registrar", json={"cedula": "123"}).status_code in (302, 401, 403)
    assert client.post("/ventas/registrar_venta", json={"placa": "ABC123"}).status_code in (302, 401, 403)
    assert client.post("/ventas/editar", data={"cod_venta": "1"}).status_code in (302, 401, 403)
    assert client.post("/ventas/eliminar/1").status_code in (302, 401, 403)