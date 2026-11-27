"""
Pruebas de Integración para el Módulo Taller
Archivo: tests/integration/test_taller_integration.py
Base de datos: automall_test y seguridad_test (MySQL Real)
Casos: CP-TAL-INT-01 al CP-TAL-INT-14
"""

from unittest.mock import patch
from tests.integration.conftest import obtener_conexion_negocio_test, obtener_conexion_seguridad_test
from utils.notificaciones_manager import NotificacionManager


def test_00_verificar_conexion_real_automall_test():
    """Verifica que la conexión física a MySQL se establezca exitosamente contra automall_test."""
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE(), COUNT(*) FROM taller;")
    nombre_bd, total_filas = cursor.fetchone()
    cursor.close()
    conn.close()

    assert nombre_bd == "automall_test"
    assert total_filas == 0  # La tabla debe estar limpia tras el fixture



# BLOQUE 2: CASOS DE INTEGRACIÓN DE REGISTRO (CP-TAL-INT-01 AL CP-TAL-INT-06)


def test_cp_tal_int_01_registro_exitoso_persistencia_bd_y_bitacora(cliente_autenticado):
    """
    CP-TAL-INT-01: Registro exitoso de nuevo taller.
    Verifica integración completa:
    1. HTTP POST /taller/nuevo -> 200 tras redirección con mensaje flash
    2. Notificación emitida al staff con título y mensaje correcto
    3. Persistencia física en automall_test.taller (1 registro exacto)
    4. Registro de auditoría en seguridad_test.t_bitacora (cod_accion=1 CREAR, cod_modulo=10 TALLER)
       cumpliendo la llave foránea con t_usuario (cédula 7423045 - Ana Valencia).
    """
    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            "/taller/nuevo",
            data={
                "nombre_taller": "Taller Mecánico Central",
                "direccion": "Av. Las Industrias, Local 12",
                "estado": "1"
            },
            follow_redirects=True
        )

        # 1. Verificación HTTP y mensaje Flash
        assert response.status_code == 200
        assert "Taller registrado correctamente." in response.get_data(as_text=True)

        # 2. Verificación de integración con Notificaciones
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Taller Mecánico Central" in call_kwargs.get("notificacion_staff", {}).get("mensaje", "")

    # 3. Verificación de persistencia directa en MySQL automall_test
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT cod_taller, nombre_taller, direccion, estado FROM taller WHERE nombre_taller = %s;",
        ("Taller Mecánico Central",)
    )
    taller_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_db is not None
    assert taller_db["nombre_taller"] == "Taller Mecánico Central"
    assert taller_db["direccion"] == "Av. Las Industrias, Local 12"
    assert taller_db["estado"] == "1"

    # 4. Verificación de auditoría en MySQL seguridad_test (Buscamos la acción 1 = CREAR)
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute(
        "SELECT cedula_usuario, cod_accion, cod_modulo FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = 1;",
        ("7423045",)
    )
    bitacora_db = cur_sec.fetchone()
    cur_sec.close()
    conn_sec.close()

    assert bitacora_db is not None
    assert bitacora_db["cedula_usuario"] == "7423045"
    assert bitacora_db["cod_accion"] == 1   # 1 = CREAR
    assert bitacora_db["cod_modulo"] == 10  # 10 = TALLER


def test_cp_tal_int_02_registro_rechazado_nombre_vacio(cliente_autenticado):
    """
    CP-TAL-INT-02: Rechazo de registro por nombre obligatorio vacío.
    Verifica que no se guarde nada en automall_test y no se genere bitácora de creación.
    """
    response = cliente_autenticado.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "",
            "direccion": "Av. Principal 45",
            "estado": "1"
        },
        follow_redirects=True
    )

    # 1. Verificación de respuesta HTTP y mensaje de validación
    assert response.status_code == 200
    assert "El nombre del taller es obligatorio." in response.get_data(as_text=True)

    # 2. Verificación en BD automall_test: 0 filas guardadas
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()

    # 3. Verificación en BD seguridad_test: 0 registros de creación en bitácora
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 10;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()


def test_cp_tal_int_03_registro_rechazado_direccion_invalida_corta(cliente_autenticado):
    """
    CP-TAL-INT-03: Rechazo de registro por dirección demasiado corta (< 5 caracteres).
    Verifica integridad: ningún dato es persistido.
    """
    response = cliente_autenticado.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "Taller Los Robles",
            "direccion": "Av.",  # Menor a 5 caracteres
            "estado": "1"
        },
        follow_redirects=True
    )

    # 1. Verificación HTTP
    assert response.status_code == 200
    assert "La dirección debe tener al menos 5 caracteres." in response.get_data(as_text=True)

    # 2. Verificación en BD: 0 filas
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_tal_int_04_registro_rechazado_caracteres_invalidos_nombre(cliente_autenticado):
    """
    CP-TAL-INT-04: Rechazo de registro por caracteres no permitidos en el nombre (@, #, $, etc.).
    """
    response = cliente_autenticado.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "Taller AutoMall #1 @*$",
            "direccion": "Zona Industrial II",
            "estado": "1"
        },
        follow_redirects=True
    )

    # 1. Verificación HTTP
    assert response.status_code == 200
    assert "El nombre del taller contiene caracteres no permitidos." in response.get_data(as_text=True)

    # 2. Verificación en BD: 0 filas
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_tal_int_05_registro_rechazado_nombre_duplicado(cliente_autenticado):
    """
    CP-TAL-INT-05: Rechazo de registro por nombre duplicado (integridad con BD real).
    Precondición: Existe un taller 'Taller Los Pinos' en automall_test.
    Acción: Intentar registrar otro taller con el mismo nombre en minúsculas.
    Resultado: Rechazado, no se duplica en BD y no genera bitácora adicional de creación.
    """
    # Precondición: Insertar previamente un taller en automall_test
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);",
        ("Taller Los Pinos", "Carrera 21 con Calle 15", "1")
    )
    cursor.close()
    conn.close()

    # Acción: Enviar formulario con nombre duplicado en minúsculas
    response = cliente_autenticado.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "taller los pinos",
            "direccion": "Otra Dirección 789",
            "estado": "1"
        },
        follow_redirects=True
    )

    # 1. Verificación HTTP
    assert response.status_code == 200
    assert "Ya existe un taller con ese nombre." in response.get_data(as_text=True)

    # 2. Verificación en BD: solo existe el registro original (no 2)
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller WHERE LOWER(nombre_taller) = 'taller los pinos';")
    assert cursor.fetchone()[0] == 1
    cursor.close()
    conn.close()

    # 3. Verificación en bitácora: no se registró creación para este intento
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 10;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()


def test_cp_tal_int_06_registro_exitoso_limites_longitud_maxima(cliente_autenticado):
    """
    CP-TAL-INT-06: Registro exitoso con valores en longitud límite máxima.
    - Nombre del taller: exactamente 100 caracteres permitidos.
    - Dirección: exactamente 250 caracteres permitidos.
    Verifica que la base de datos guarde íntegramente las cadenas límite sin truncar.
    """
    nombre_100 = "Taller " + ("A" * 93)  # Longitud exacta: 100 caracteres
    dir_250 = "Av. " + ("D" * 246)        # Longitud exacta: 250 caracteres

    response = cliente_autenticado.post(
        "/taller/nuevo",
        data={
            "nombre_taller": nombre_100,
            "direccion": dir_250,
            "estado": "1"
        },
        follow_redirects=True
    )

    # 1. Verificación HTTP
    assert response.status_code == 200
    assert "Taller registrado correctamente." in response.get_data(as_text=True)

    # 2. Verificación de persistencia íntegra en BD real
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre_taller, direccion, estado FROM taller WHERE nombre_taller = %s;", (nombre_100,))
    taller_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_db is not None
    assert len(taller_db["nombre_taller"]) == 100
    assert taller_db["nombre_taller"] == nombre_100
    assert len(taller_db["direccion"]) == 250
    assert taller_db["direccion"] == dir_250

    # 3. Verificación de auditoría en bitácora (para la cédula 7423045 de Ana Valencia)
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute(
        "SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 10 AND cedula_usuario = %s;",
        ("7423045",)
    )
    assert cur_sec.fetchone()[0] == 1
    cur_sec.close()
    conn_sec.close()



# BLOQUE 3: CASOS DE EDICIÓN, ELIMINACIÓN Y CONSULTA (CP-TAL-INT-07 AL CP-TAL-INT-12)


def test_cp_tal_int_07_actualizacion_exitosa_bd_bitacora_notificacion(cliente_autenticado):
    """
    CP-TAL-INT-07: Actualización exitosa de taller en BD física, bitácora y notificación.
    Verifica que los cambios se reflejen en automall_test.taller y se audite en seguridad_test.t_bitacora (cod_accion=3).
    """
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);",
        ("Taller Original Express", "Calle Vieja 123", "1")
    )
    cod_taller = cursor.lastrowid
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            f"/taller/editar/{cod_taller}",
            data={
                "nombre_taller": "Taller Central Renovado",
                "direccion": "Nueva Av. Las Industrias 456",
                "estado": "1"
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Taller actualizado correctamente." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Taller Central Renovado" in call_kwargs.get("notificacion_staff", {}).get("mensaje", "")

    # Verificación en BD negocio: datos actualizados
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre_taller, direccion, estado FROM taller WHERE cod_taller = %s;", (cod_taller,))
    taller_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_db is not None
    assert taller_db["nombre_taller"] == "Taller Central Renovado"
    assert taller_db["direccion"] == "Nueva Av. Las Industrias 456"
    assert taller_db["estado"] == "1"

    # Verificación en bitácora: cod_accion = 3 (ACTUALIZAR)
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute(
        "SELECT cedula_usuario, cod_accion, cod_modulo FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = 3;",
        ("7423045",)
    )
    bitacora_db = cur_sec.fetchone()
    cur_sec.close()
    conn_sec.close()

    assert bitacora_db is not None
    assert bitacora_db["cod_accion"] == 3   # 3 = ACTUALIZAR
    assert bitacora_db["cod_modulo"] == 10  # 10 = TALLER


def test_cp_tal_int_08_actualizacion_rechazada_taller_inexistente(cliente_autenticado):
    """
    CP-TAL-INT-08: Rechazo de actualización de un taller inexistente.
    Verifica que al no existir el ID en automall_test, se muestre error y no se registre bitácora de actualización.
    """
    response = cliente_autenticado.post(
        "/taller/editar/99999",
        data={
            "nombre_taller": "Taller Fantasma",
            "direccion": "Calle Inexistente 000",
            "estado": "1"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "El taller no existe." in response.get_data(as_text=True)

    # Verificación en bitácora: 0 registros de actualización
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 3 AND cod_modulo = 10;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()


def test_cp_tal_int_09_actualizacion_rechazada_nombre_duplicado_otro_taller(cliente_autenticado):
    """
    CP-TAL-INT-09: Rechazo de actualización por colisión de nombre con otro taller existente.
    Precondición: Taller A ('Taller Alfa') y Taller B ('Taller Beta').
    Acción: Intentar cambiar el nombre de Taller B a 'Taller Alfa'.
    Resultado: Rechazado por validación de duplicidad, Taller B no cambia en BD.
    """
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);", ("Taller Alfa", "Zona Norte", "1"))
    cod_taller_a = cursor.lastrowid
    cursor.execute("INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);", ("Taller Beta", "Zona Sur", "1"))
    cod_taller_b = cursor.lastrowid
    cursor.close()
    conn.close()

    # Intentar renombrar Taller B al nombre de Taller A
    response = cliente_autenticado.post(
        f"/taller/editar/{cod_taller_b}",
        data={
            "nombre_taller": "taller alfa",  # En minúsculas para probar insensibilidad
            "direccion": "Zona Sur Modificada",
            "estado": "1"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Ya existe un taller con ese nombre." in response.get_data(as_text=True)

    # Verificar que Taller B no cambió en BD
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre_taller, direccion FROM taller WHERE cod_taller = %s;", (cod_taller_b,))
    taller_b_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_b_db["nombre_taller"] == "Taller Beta"
    assert taller_b_db["direccion"] == "Zona Sur"


def test_cp_tal_int_10_eliminacion_logica_exitosa_estado_inactivo(cliente_autenticado):
    """
    CP-TAL-INT-10: Eliminación lógica exitosa cambiando estado a '0'.
    Verifica que el registro no se borre físicamente (preservando integridad referencial)
    y que se emita la notificación de desactivación y la bitácora.
    """
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);",
        ("Taller Para Desactivar", "Zona Oeste 99", "1")
    )
    cod_taller = cursor.lastrowid
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            f"/taller/eliminar/{cod_taller}",
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Taller desactivado correctamente." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Taller Desactivado" in call_kwargs.get("notificacion_staff", {}).get("titulo", "")

    # Verificación en BD negocio: el taller aún existe pero con estado = '0'
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_taller, nombre_taller, estado FROM taller WHERE cod_taller = %s;", (cod_taller,))
    taller_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_db is not None
    assert taller_db["estado"] == "0"

    # Verificación en bitácora: se registra la desactivación (cod_accion = 3)
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute(
        "SELECT cedula_usuario, cod_accion, cod_modulo FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = 3;",
        ("7423045",)
    )
    bitacora_db = cur_sec.fetchone()
    cur_sec.close()
    conn_sec.close()

    assert bitacora_db is not None
    assert bitacora_db["cod_modulo"] == 10


def test_cp_tal_int_11_eliminacion_taller_inexistente_sin_efecto_bd(cliente_autenticado):
    """
    CP-TAL-INT-11: Eliminación sobre ID inexistente en BD.
    Precondición: Taller legítimo activo ('Taller Activo Permanente').
    Acción: Ejecutar POST /taller/eliminar/99999.
    Resultado: La fila existente en BD no se ve afectada ni alterada en su estado.
    """
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);",
        ("Taller Activo Permanente", "Av. Principal 100", "1")
    )
    cod_taller = cursor.lastrowid
    cursor.close()
    conn.close()

    response = cliente_autenticado.post("/taller/eliminar/99999", follow_redirects=True)
    assert response.status_code == 200

    # Verificar que el taller existente no fue alterado
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM taller WHERE cod_taller = %s;", (cod_taller,))
    taller_db = cursor.fetchone()
    cursor.close()
    conn.close()

    assert taller_db["estado"] == "1"


def test_cp_tal_int_12_consulta_talleres_activos_renderizado_y_bitacora_lectura(cliente_autenticado):
    """
    CP-TAL-INT-12: Consulta de talleres (GET /taller).
    Verifica:
    1. Renderizado HTML 200 con DataTables
    2. Filtrado: solo muestra talleres con estado='1', omite estado='0'
    3. Registro de auditoría de lectura en t_bitacora (cod_accion=2 LEER, cod_modulo=10 TALLER)
    """
    # Precondición: 2 talleres activos y 1 inactivo en automall_test
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);", ("Taller Activo Uno", "Dirección 1", "1"))
    cursor.execute("INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);", ("Taller Activo Dos", "Dirección 2", "1"))
    cursor.execute("INSERT INTO taller (nombre_taller, direccion, estado) VALUES (%s, %s, %s);", ("Taller Inactivo Tres", "Dirección 3", "0"))
    cursor.close()
    conn.close()

    # Acción: GET /taller
    response = cliente_autenticado.get("/taller")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verificación en HTML: talleres activos presentes, inactivo ausente
    assert "Taller Activo Uno" in html
    assert "Taller Activo Dos" in html
    assert "Taller Inactivo Tres" not in html

    # Verificación en bitácora: cod_accion = 2 (LEER)
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute(
        "SELECT cedula_usuario, cod_accion, cod_modulo FROM t_bitacora WHERE cedula_usuario = %s AND cod_accion = 2;",
        ("7423045",)
    )
    bitacora_db = cur_sec.fetchone()
    cur_sec.close()
    conn_sec.close()

    assert bitacora_db is not None
    assert bitacora_db["cod_accion"] == 2   # 2 = LEER
    assert bitacora_db["cod_modulo"] == 10  # 10 = TALLER



# BLOQUE 4: SEGURIDAD, AUTENTICACIÓN Y CONTROL DE ACCESO RBAC (CP-TAL-INT-13 Y 14)


def test_cp_tal_int_13_acceso_anonimo_sin_sesion_bloqueado(app_client):
    """
    CP-TAL-INT-13: Acceso anónimo sin sesión iniciada.
    Verifica que el decorador @requiere_permiso intercepte la solicitud anónima,
    la redirija con HTTP 302 a /login y no permita ninguna inserción en automall_test.
    """
    # 1. Intento de consulta sin sesión
    res_get = app_client.get("/taller", follow_redirects=False)
    assert res_get.status_code == 302
    assert res_get.headers["Location"].endswith("/login")

    # 2. Intento de registro sin sesión
    res_post = app_client.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "Taller Intruso",
            "direccion": "Dirección No Autorizada",
            "estado": "1"
        },
        follow_redirects=False
    )
    assert res_post.status_code == 302
    assert res_post.headers["Location"].endswith("/login")

    # 3. Verificación de integridad: la BD automall_test permanece con 0 registros
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_tal_int_14_acceso_rol_no_autorizado_bloqueado_por_rbac(cliente_sin_permiso):
    """
    CP-TAL-INT-14: Control de acceso RBAC contra base de datos real seguridad_test.
    Usuario: Jeymar Inciarte (Rol 3 = Vendedor).
    El decorador @requiere_permiso consulta físicamente en seguridad_test.t_rol_permiso.
    Al comprobar que el Rol 3 no tiene permisos sobre el módulo 10 ('Taller'),
    bloquea la acción con HTTP 302 hacia '/' y no altera automall_test.
    """
    # 1. Intento de consulta con Rol 3
    res_get = cliente_sin_permiso.get("/taller", follow_redirects=False)
    assert res_get.status_code == 302
    assert res_get.headers["Location"].endswith("/")

    # 2. Intento de creación con Rol 3
    res_post = cliente_sin_permiso.post(
        "/taller/nuevo",
        data={
            "nombre_taller": "Taller Vendedor No Permitido",
            "direccion": "Zona Prohibida",
            "estado": "1"
        },
        follow_redirects=False
    )
    assert res_post.status_code == 302
    assert res_post.headers["Location"].endswith("/")

    # 3. Verificación de integridad en automall_test: ninguna fila insertada
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM taller WHERE nombre_taller = 'Taller Vendedor No Permitido';")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()

    # 4. Verificación de bitácora en seguridad_test: no se registra auditoría de creación
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 10;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()