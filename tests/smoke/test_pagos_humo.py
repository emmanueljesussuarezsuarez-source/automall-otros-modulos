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
def cuenta_pendiente_temporal(usuario_prueba_bd):
    """
    Crea una venta y cuenta por cobrar temporal en automall_test para probar
    procesar_pago y anular_pago contra datos reales, limpiando todo al finalizar.
    """
    con = ConexionBD.obtener_conexion()
    assert con.database == "automall_test"
    cur = con.cursor(dictionary=True)

    cod_venta = None
    cod_cuentas = None
    placa_usada = None
    estado_vehiculo_original = None

    try:
        cur.execute("SELECT placa, estado FROM vehiculo LIMIT 1")
        vehiculo = cur.fetchone()
        if not vehiculo:
            pytest.skip("No hay vehículos en automall_test para crear una cuenta por cobrar temporal.")

        placa_usada = vehiculo["placa"]
        estado_vehiculo_original = vehiculo["estado"]

        # Buscar una moneda en USD (no Bolívar) para no depender de tasa_cambio
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

        cedula = usuario_prueba_bd["cedula_usuario"]

        cur.execute(
            "INSERT INTO ventas (estado, fecha_venta, tipo_venta, cedula_usuario) VALUES ('procesada', CURDATE(), 'Crédito', %s)",
            (cedula,)
        )
        cod_venta = cur.lastrowid

        cur.execute(
            "INSERT INTO det_venta (poder, traspaso_papel, precio, placa, cod_venta) VALUES (0, 0, 1000.00, %s, %s)",
            (placa_usada, cod_venta)
        )

        cur.execute(
            """
            INSERT INTO cuentas_por_cobrar
            (deuda_total, deuda, fecha_emision, fecha_vencimiento, estado, cod_venta)
            VALUES (1000.00, 500.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'pendiente', %s)
            """,
            (cod_venta,)
        )
        cod_cuentas = cur.lastrowid
        con.commit()

        yield {
            "cod_venta": cod_venta,
            "cod_cuentas": cod_cuentas,
            "cod_moneda": cod_moneda,
            "cedula": cedula,
            "placa": placa_usada,
        }
    finally:
        # Limpieza en orden inverso respetando claves foráneas
        try:
            if cod_cuentas is not None:
                cur.execute("SELECT cod_pagos FROM pago_cuentas WHERE cod_cuentas = %s", (cod_cuentas,))
                pagos = [r["cod_pagos"] for r in cur.fetchall()]
                if pagos:
                    placeholders = ",".join(["%s"] * len(pagos))
                    cur.execute(f"DELETE FROM det_pago WHERE cod_pagos IN ({placeholders})", tuple(pagos))
                    cur.execute(f"DELETE FROM pago_cuentas WHERE cod_pagos IN ({placeholders})", tuple(pagos))
                cur.execute("DELETE FROM cuentas_por_cobrar WHERE cod_cuentas = %s", (cod_cuentas,))
            if cod_venta is not None:
                cur.execute("DELETE FROM det_venta WHERE cod_venta = %s", (cod_venta,))
                cur.execute("DELETE FROM ventas WHERE cod_venta = %s", (cod_venta,))
            if placa_usada is not None and estado_vehiculo_original is not None:
                cur.execute("UPDATE vehiculo SET estado = %s WHERE placa = %s", (estado_vehiculo_original, placa_usada))
            con.commit()
        finally:
            cur.close()
            con.close()


# ==============================================================================
# 1. CAMINO FELIZ: CONSULTAS GET Y VISTAS REALES EN AUTOMALL_TEST
# ==============================================================================

def test_humo_pagos_listados_y_api_deudas_get(sesion_usuario_prueba, usuario_prueba_bd):
    """Humo: Verifica carga real de listar_pagos, listar_admin y API obtener_deudas."""
    cedula = usuario_prueba_bd["cedula_usuario"]

    res_cliente = sesion_usuario_prueba.get("/pagos/listar_pagos")
    assert res_cliente.status_code == 200

    res_admin = sesion_usuario_prueba.get("/pagos/listar_admin")
    assert res_admin.status_code == 200

    res_api = sesion_usuario_prueba.get(f"/pagos/obtener_deudas/{cedula}")
    assert res_api.status_code == 200
    assert isinstance(res_api.get_json(), list)


def test_humo_pagos_vista_registrar_admin_y_cliente(client, usuario_prueba_bd):
    """Humo: Verifica renderizado real de /pagos/registrar_pago como admin (rol 1) y cliente (rol 4)."""
    # Vista Admin
    with client.session_transaction() as sess:
        sess["usuario_nombre"] = usuario_prueba_bd["nombre"]
        sess["cedula_usuario"] = usuario_prueba_bd["cedula_usuario"]
        sess["cod_rol"] = 1
        sess["rol"] = 1
    assert client.get("/pagos/registrar_pago").status_code == 200

    # Vista Cliente
    with client.session_transaction() as sess:
        sess["cod_rol"] = 4
        sess["rol"] = 4
    assert client.get("/pagos/registrar_pago").status_code == 200


# ==============================================================================
# 2. CAMINO FELIZ TRANSACCIONAL: PROCESAR ABONO + ANULAR EN AUTOMALL_TEST
# ==============================================================================

def test_humo_pagos_procesar_y_anular_flujo_real(sesion_usuario_prueba, cuenta_pendiente_temporal):
    """
    Humo End-to-End: Procesa un abono real en automall_test, verifica la reducción de saldo,
    luego lo anula y valida la restauración de la deuda y bloqueo de doble anulación.
    """
    cod_cuentas = cuenta_pendiente_temporal["cod_cuentas"]
    cod_moneda = cuenta_pendiente_temporal["cod_moneda"]
    cedula = cuenta_pendiente_temporal["cedula"]

    # 1. PROCESAR ABONO (Efectivo USD, $100 sobre deuda de $500)
    payload = {
        "cedula_cliente": cedula,
        "cod_cuentas": cod_cuentas,
        "monto_pago": 100.00,
        "cod_moneda": cod_moneda,
        "cod_metodo": "2",
        "descripcion": "Abono smoke test",
        "referencia": ""
    }
    res_procesar = sesion_usuario_prueba.post("/pagos/procesar", json=payload)

    assert res_procesar.status_code == 200
    json_proc = res_procesar.get_json()
    assert json_proc["success"] is True
    cod_pagos = json_proc["cod_pagos"]
    assert cod_pagos is not None

    # Verificar en automall_test que la deuda bajó a 400.00
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT deuda, estado FROM cuentas_por_cobrar WHERE cod_cuentas = %s", (cod_cuentas,))
        cxc = cur.fetchone()
        cur.close()
    finally:
        con.close()
    assert float(cxc["deuda"]) == 400.00

    # 2. ANULAR EL PAGO CREADO
    res_anular = sesion_usuario_prueba.post(
        "/pagos/anular",
        data={"cod_pagos": str(cod_pagos), "motivo": "Prueba de humo anulación"},
        follow_redirects=False
    )
    assert res_anular.status_code == 302

    # Verificar en automall_test que el pago quedó Anulado y la deuda restaurada a 500.00
    con = ConexionBD.obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT estado FROM pago_cuentas WHERE cod_pagos = %s", (cod_pagos,))
        pago_row = cur.fetchone()
        cur.execute("SELECT deuda, estado FROM cuentas_por_cobrar WHERE cod_cuentas = %s", (cod_cuentas,))
        cxc_anulada = cur.fetchone()
        cur.close()
    finally:
        con.close()

    assert pago_row["estado"] == "Anulado"
    assert float(cxc_anulada["deuda"]) == 500.00

    # 3. RECHAZO DE DOBLE ANULACIÓN
    res_doble = sesion_usuario_prueba.post(
        "/pagos/anular",
        data={"cod_pagos": str(cod_pagos), "motivo": "Intento doble"},
        follow_redirects=False
    )
    assert res_doble.status_code == 302
    with sesion_usuario_prueba.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert any(cat == "danger" for cat, _ in flashes)


# ==============================================================================
# 3. VALIDACIONES Y CAMINO TRISTE (MONTO 0, SOBREABONO, IDS INEXISTENTES)
# ==============================================================================

def test_humo_pagos_procesar_rechaza_json_vacio_y_cuenta_inexistente(sesion_usuario_prueba):
    """Humo (Camino triste): JSON vacío o cod_cuentas 999999 devuelven HTTP 400 controlado."""
    res_vacio = sesion_usuario_prueba.post("/pagos/procesar", json={})
    assert res_vacio.status_code == 400
    assert res_vacio.get_json()["success"] is False

    res_inexistente = sesion_usuario_prueba.post(
        "/pagos/procesar",
        json={"cod_cuentas": 999999, "monto_pago": 50, "cod_metodo": "2"}
    )
    assert res_inexistente.status_code == 400
    assert res_inexistente.get_json()["success"] is False
    assert "no existe" in res_inexistente.get_json()["error"].lower()


def test_humo_pagos_procesar_rechaza_monto_cero_y_sobreabono(sesion_usuario_prueba, cuenta_pendiente_temporal):
    """Humo (Valores límite): Rechaza abono de $0 o mayor a la deuda ($9999 > $500) con HTTP 400."""
    cod_cuentas = cuenta_pendiente_temporal["cod_cuentas"]
    cod_moneda = cuenta_pendiente_temporal["cod_moneda"]
    cedula = cuenta_pendiente_temporal["cedula"]

    res_cero = sesion_usuario_prueba.post(
        "/pagos/procesar",
        json={
            "cedula_cliente": cedula, "cod_cuentas": cod_cuentas,
            "monto_pago": 0, "cod_moneda": cod_moneda, "cod_metodo": "2"
        }
    )
    assert res_cero.status_code == 400
    assert res_cero.get_json()["success"] is False

    res_exceso = sesion_usuario_prueba.post(
        "/pagos/procesar",
        json={
            "cedula_cliente": cedula, "cod_cuentas": cod_cuentas,
            "monto_pago": 9999, "cod_moneda": cod_moneda, "cod_metodo": "2"
        }
    )
    assert res_exceso.status_code == 400
    assert res_exceso.get_json()["success"] is False


def test_humo_pagos_anular_sin_codigo_y_id_inexistente(sesion_usuario_prueba):
    """Humo (IDs inexistentes): Anular sin código o con cod_pagos=999999 no da 500 y muestra alerta."""
    res_sin_cod = sesion_usuario_prueba.post("/pagos/anular", data={"motivo": "Sin código"})
    assert res_sin_cod.status_code == 302

    res_999 = sesion_usuario_prueba.post("/pagos/anular", data={"cod_pagos": "999999", "motivo": "Inexistente"})
    assert res_999.status_code == 302
    with sesion_usuario_prueba.session_transaction() as sess:
        flashes = sess.get("_flashes", [])
        assert any(cat == "danger" for cat, _ in flashes)


# ==============================================================================
# 4. SEGURIDAD Y CONTROL DE ACCESO (SIN SESIÓN Y ROL SIN PRIVILEGIOS)
# ==============================================================================

def test_humo_pagos_sin_sesion_bloquea_todas_las_rutas(client):
    """Humo Seguridad: Peticiones sin iniciar sesión bloquean las 6 rutas del módulo Pagos."""
    assert client.get("/pagos/listar_pagos").status_code in (302, 401, 403)
    assert client.get("/pagos/listar_admin").status_code in (302, 401, 403)
    assert client.get("/pagos/obtener_deudas/12345678").status_code in (302, 401, 403)
    assert client.get("/pagos/registrar_pago").status_code in (302, 401, 403)
    assert client.post("/pagos/procesar", json={"cod_cuentas": 1, "monto_pago": 10}).status_code in (302, 401, 403)
    assert client.post("/pagos/anular", data={"cod_pagos": "1"}).status_code in (302, 401, 403)


def test_humo_pagos_rol_sin_privilegios_bloquea_rutas_protegidas(client):
    """Humo Seguridad: Un rol sin permisos en 'Pagos' en seguridad_test no puede consultar ni operar."""
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
                  WHERE rp.cod_rol = r.cod_rol AND m.nombre_modulo IN ('Pagos', 'Pagosadmin')
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

    assert client.get("/pagos/listar_pagos").status_code in (302, 401, 403)
    assert client.get("/pagos/listar_admin").status_code in (302, 401, 403)
    assert client.get("/pagos/obtener_deudas/12345678").status_code in (302, 401, 403)
    assert client.post("/pagos/procesar", json={"cod_cuentas": 1, "monto_pago": 10}).status_code in (302, 401, 403)
    assert client.post("/pagos/anular", data={"cod_pagos": "1"}).status_code in (302, 401, 403)