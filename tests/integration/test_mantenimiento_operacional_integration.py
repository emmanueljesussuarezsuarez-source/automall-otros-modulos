"""
Pruebas de Integración para el Módulo Mantenimiento Operacional
Archivo: tests/integration/test_mantenimiento_operacional_integration.py
Base de datos: automall_test y seguridad_test (MySQL Real)
Casos: CP-MAN-INT-01 al CP-MAN-INT-14
"""

from datetime import date
from unittest.mock import patch
from tests.integration.conftest import obtener_conexion_negocio_test, obtener_conexion_seguridad_test
from models.mantenimiento_operacional import MantenimientoOperacional
from utils.notificaciones_manager import NotificacionManager


def test_00_verificar_conexion_real_automall_test_mantenimiento():
    """Verifica conexión física a MySQL y estado inicial limpio de las tablas de mantenimiento."""
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE(), COUNT(*) FROM mantenimiento;")
    nombre_bd, total_mantenimientos = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM det_mantenimiento;")
    total_detalles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mantenimiento_cant;")
    total_cant = cursor.fetchone()[0]

    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    estado_vehiculo = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    assert nombre_bd == "automall_test"
    assert total_mantenimientos == 0
    assert total_detalles == 0
    assert total_cant == 0
    assert estado_vehiculo == "Disponible"



# BLOQUE 1: CASOS DE INTEGRACIÓN DE REGISTRO (CP-MAN-INT-01 AL CP-MAN-INT-06)


def test_cp_man_int_01_registro_exitoso_persistencia_transaccional_y_bitacora(cliente_autenticado, taller_de_prueba):
    """
    CP-MAN-INT-01: Registro exitoso transaccional de mantenimiento operacional.
    Verifica integración completa:
    1. HTTP POST /mantenimiento-operacional/crear -> 200 tras redirección con flash success.
    2. Notificación emitida al staff con título y placa.
    3. Persistencia en automall_test.mantenimiento (cabecera con estado 'Activo').
    4. Persistencia en automall_test.det_mantenimiento (detalle vinculado con taller y placa).
    5. Persistencia en automall_test.mantenimiento_cant (repuestos o tareas específicas).
    6. Sincronización en automall_test.vehiculo (placa GH567IJ pasa a 'Mantenimiento').
    7. Auditoría en seguridad_test.t_bitacora (cod_accion=1 CREAR, cod_modulo=3).
    """
    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            "/mantenimiento-operacional/crear",
            data={
                "descripcion_general": "Mantenimiento preventivo general de motor y frenos",
                "quien_autoriza": "7423045",
                "tipo": "Preventivo",
                "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
                "fecha_completada": "",
                "placa": "GH567IJ",
                "cod_taller": str(taller_de_prueba),
                "costo_base": "150.00",
                "costo_final": "",
                "descripcion_detalle_0": "Filtro de aceite y bujías",
                "cantidad_0": "4",
            },
            follow_redirects=True
        )

    assert response.status_code == 200
    assert "Mantenimiento registrado correctamente." in response.data.decode("utf-8")
    assert spy_notif.called

    # 1. Comprobación física de cabecera en mantenimiento
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento, descripcion_general, quien_autoriza, estado, costo_base FROM mantenimiento;")
    registros_mant = cursor.fetchall()
    assert len(registros_mant) == 1
    cod_mantenimiento = registros_mant[0]["cod_mantenimiento"]
    assert registros_mant[0]["descripcion_general"] == "Mantenimiento preventivo general de motor y frenos"
    assert registros_mant[0]["quien_autoriza"] == "7423045"
    assert registros_mant[0]["estado"] == "Activo"
    assert float(registros_mant[0]["costo_base"]) == 150.00

    # 2. Comprobación física en det_mantenimiento
    cursor.execute("SELECT tipo, placa, cod_taller, cedula_usuario FROM det_mantenimiento WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    det_mant = cursor.fetchone()
    assert det_mant is not None
    assert det_mant["tipo"] == "Preventivo"
    assert det_mant["placa"] == "GH567IJ"
    assert det_mant["cod_taller"] == taller_de_prueba
    assert det_mant["cedula_usuario"] == "7423045"

    # 3. Comprobación física en mantenimiento_cant
    cursor.execute("SELECT descripcion_detalle, cantidad FROM mantenimiento_cant WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    cant_items = cursor.fetchall()
    assert len(cant_items) == 1
    assert cant_items[0]["descripcion_detalle"] == "Filtro de aceite y bujías"
    assert cant_items[0]["cantidad"] == 4

    # 4. Comprobación de cambio de estado en vehículo
    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Mantenimiento"
    cursor.close()
    conn.close()

    # 5. Comprobación física de auditoría en bitácora
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute("SELECT cod_accion, cod_modulo, cedula_usuario FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 3;")
    bitacora = cur_sec.fetchall()
    cur_sec.close()
    conn_sec.close()
    assert len(bitacora) == 1
    assert bitacora[0]["cedula_usuario"] == "7423045"


def test_cp_man_int_02_registro_rechazado_placa_inexistente(cliente_autenticado, taller_de_prueba):
    """
    CP-MAN-INT-02: Rechazo de registro por placa inexistente en la tabla vehiculo.
    Verifica que validar_existencias bloquee la inserción física.
    """
    response = cliente_autenticado.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Mantenimiento de prueba con placa inexistente",
            "quien_autoriza": "7423045",
            "tipo": "Correctivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "placa": "NOEXIST",
            "cod_taller": str(taller_de_prueba),
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La placa seleccionada no existe en la tabla vehiculo." in response.data.decode("utf-8")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_man_int_03_registro_rechazado_taller_inexistente(cliente_autenticado):
    """
    CP-MAN-INT-03: Rechazo de registro por taller inexistente o inactivo.
    """
    response = cliente_autenticado.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Mantenimiento con taller inexistente en base de datos",
            "quien_autoriza": "7423045",
            "tipo": "Correctivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "placa": "GH567IJ",
            "cod_taller": "9999",
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "El taller seleccionado no existe o no está activo." in response.data.decode("utf-8")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_man_int_04_registro_rechazado_autorizador_inexistente(cliente_autenticado, taller_de_prueba):
    """
    CP-MAN-INT-04: Rechazo de registro por persona que autoriza no registrada en seguridad.t_usuario.
    """
    response = cliente_autenticado.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Mantenimiento con autorizador inexistente",
            "quien_autoriza": "99999999",
            "tipo": "Preventivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "placa": "GH567IJ",
            "cod_taller": str(taller_de_prueba),
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La persona que autoriza no existe en la tabla t_usuario." in response.data.decode("utf-8")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_man_int_05_registro_rechazado_descripcion_general_demasiado_corta(cliente_autenticado, taller_de_prueba):
    """
    CP-MAN-INT-05: Rechazo de registro cuando la descripción general tiene menos de 10 caracteres.
    """
    response = cliente_autenticado.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Corta",
            "quien_autoriza": "7423045",
            "tipo": "Preventivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "placa": "GH567IJ",
            "cod_taller": str(taller_de_prueba),
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La descripción general debe tener al menos 10 caracteres." in response.data.decode("utf-8")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_man_int_06_registro_rechazado_fecha_solicitud_anterior_a_hoy(cliente_autenticado, taller_de_prueba):
    """
    CP-MAN-INT-06: Rechazo de registro cuando la fecha de solicitud es anterior al día de hoy.
    """
    response = cliente_autenticado.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Mantenimiento con fecha en el pasado",
            "quien_autoriza": "7423045",
            "tipo": "Preventivo",
            "fecha_solicitud": "2020-01-01",
            "placa": "GH567IJ",
            "cod_taller": str(taller_de_prueba),
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Fecha de solicitud no puede ser anterior a hoy." in response.data.decode("utf-8")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()



# BLOQUE 2: ACTUALIZACIÓN, INACTIVACIÓN Y FINALIZACIÓN (CP-MAN-INT-07 AL CP-MAN-INT-11)


def test_cp_man_int_07_actualizacion_exitosa_bd_bitacora_notificacion(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-07: Actualización exitosa de mantenimiento y reemplazo de detalles en BD.
    Verifica:
    1. Registro inicial de mantenimiento activo.
    2. HTTP POST /mantenimiento-operacional/editar/<id> -> 200 tras redirección con flash success.
    3. Notificación emitida al staff sobre la actualización.
    4. Persistencia de nuevos datos en automall_test.mantenimiento.
    5. Reemplazo atómico de repuestos en automall_test.mantenimiento_cant.
    6. Auditoría en seguridad_test.t_bitacora (cod_accion=3 ACTUALIZAR, cod_modulo=3).
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento preventivo inicial programado",
        quien_autoriza="7423045",
        tipo="Preventivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=120.00,
        detalles=[{"descripcion_detalle": "Filtro inicial", "cantidad": 1}]
    )
    assert res_crear["status"] is True

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento FROM mantenimiento LIMIT 1;")
    cod_mantenimiento = cursor.fetchone()["cod_mantenimiento"]
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_super_usuario.post(
            f"/mantenimiento-operacional/editar/{cod_mantenimiento}",
            data={
                "descripcion_general": "Mantenimiento general actualizado con sustitución de frenos",
                "quien_autoriza": "7423045",
                "tipo": "Correctivo",
                "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
                "fecha_completada": "",
                "cod_taller": str(taller_de_prueba),
                "costo_base": "280.00",
                "costo_final": "",
                "descripcion_detalle_0": "Pastillas de freno cerámicas",
                "cantidad_0": "2",
            },
            follow_redirects=True
        )

    assert response.status_code == 200
    assert "Mantenimiento actualizado correctamente." in response.data.decode("utf-8")
    assert spy_notif.called

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT descripcion_general, costo_base FROM mantenimiento WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    mant_actualizado = cursor.fetchone()
    assert mant_actualizado["descripcion_general"] == "Mantenimiento general actualizado con sustitución de frenos"
    assert float(mant_actualizado["costo_base"]) == 280.00

    cursor.execute("SELECT descripcion_detalle, cantidad FROM mantenimiento_cant WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    detalles_nuevos = cursor.fetchall()
    assert len(detalles_nuevos) == 1
    assert detalles_nuevos[0]["descripcion_detalle"] == "Pastillas de freno cerámicas"
    assert detalles_nuevos[0]["cantidad"] == 2
    cursor.close()
    conn.close()

    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute("SELECT cod_accion, cod_modulo, cedula_usuario FROM t_bitacora WHERE cod_accion = 3 AND cod_modulo = 3;")
    bitacora = cur_sec.fetchall()
    cur_sec.close()
    conn_sec.close()
    assert len(bitacora) >= 1
    assert bitacora[-1]["cedula_usuario"] == "14094670"


def test_cp_man_int_08_actualizacion_rechazada_fecha_completada_anterior_a_solicitud(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-08: Rechazo de actualización cuando fecha_completada es anterior a fecha_solicitud.
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento preventivo para prueba de fechas",
        quien_autoriza="7423045",
        tipo="Preventivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=100.00
    )
    assert res_crear["status"] is True

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento FROM mantenimiento LIMIT 1;")
    cod_mantenimiento = cursor.fetchone()["cod_mantenimiento"]
    cursor.close()
    conn.close()

    response = cliente_super_usuario.post(
        f"/mantenimiento-operacional/editar/{cod_mantenimiento}",
        data={
            "descripcion_general": "Intento de actualización con fecha completada inválida",
            "quien_autoriza": "7423045",
            "tipo": "Preventivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "fecha_completada": "2020-01-01",
            "cod_taller": str(taller_de_prueba),
            "costo_base": "100.00",
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La fecha completada no puede ser anterior a la fecha de solicitud." in response.data.decode("utf-8")


def test_cp_man_int_09_inactivacion_logica_exitosa(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-09: Inactivación lógica exitosa de mantenimiento y auditoría en bitácora.
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento a inactivar lógicamente en prueba",
        quien_autoriza="7423045",
        tipo="Preventivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=85.00
    )
    assert res_crear["status"] is True

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento FROM mantenimiento LIMIT 1;")
    cod_mantenimiento = cursor.fetchone()["cod_mantenimiento"]
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_super_usuario.post(
            f"/mantenimiento-operacional/inactivar/{cod_mantenimiento}",
            follow_redirects=True
        )

    assert response.status_code == 200
    assert "Mantenimiento inactivado correctamente." in response.data.decode("utf-8")
    assert spy_notif.called

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM mantenimiento WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    assert cursor.fetchone()["estado"] == "Inactivo"
    cursor.close()
    conn.close()

    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute("SELECT cod_accion, cod_modulo, cedula_usuario FROM t_bitacora WHERE cod_accion = 3 AND cod_modulo = 3;")
    bitacora = cur_sec.fetchall()
    cur_sec.close()
    conn_sec.close()
    assert len(bitacora) >= 1
    assert bitacora[-1]["cedula_usuario"] == "14094670"


def test_cp_man_int_10_finalizacion_exitosa_mantenimiento_y_reactivacion_vehiculo(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-10: Finalización exitosa de mantenimiento operacional.
    Verifica:
    1. HTTP POST /mantenimiento-operacional/finalizar/<id>/<placa> con costo final.
    2. Cambio de estado a 'Finalizado' y registro de costo_final en automall_test.mantenimiento.
    3. Registro automático de fecha_completada = CURDATE() en det_mantenimiento.
    4. Reactivación automática del vehículo en automall_test.vehiculo a estado 'Disponible'.
    5. Auditoría en bitácora (cod_accion=3, cod_modulo=3).
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento en curso a ser finalizado con éxito",
        quien_autoriza="7423045",
        tipo="Correctivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=150.00
    )
    assert res_crear["status"] is True

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento FROM mantenimiento LIMIT 1;")
    cod_mantenimiento = cursor.fetchone()["cod_mantenimiento"]

    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Mantenimiento"
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_super_usuario.post(
            f"/mantenimiento-operacional/finalizar/{cod_mantenimiento}/GH567IJ",
            data={
                "costo_final": "320.00"
            },
            follow_redirects=True
        )

    assert response.status_code == 200
    assert "Mantenimiento finalizado correctamente." in response.data.decode("utf-8")
    assert spy_notif.called

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado, costo_final FROM mantenimiento WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    mant_finalizado = cursor.fetchone()
    assert mant_finalizado["estado"] == "Finalizado"
    assert float(mant_finalizado["costo_final"]) == 320.00

    cursor.execute("SELECT fecha_completada FROM det_mantenimiento WHERE cod_mantenimiento = %s;", (cod_mantenimiento,))
    fecha_comp = cursor.fetchone()["fecha_completada"]
    assert str(fecha_comp) == date.today().strftime("%Y-%m-%d")

    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Disponible"
    cursor.close()
    conn.close()

    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute("SELECT cod_accion, cod_modulo, cedula_usuario FROM t_bitacora WHERE cod_accion = 3 AND cod_modulo = 3;")
    bitacora = cur_sec.fetchall()
    cur_sec.close()
    conn_sec.close()
    assert len(bitacora) >= 1
    assert bitacora[-1]["cedula_usuario"] == "14094670"


def test_cp_man_int_11_consulta_mantenimientos_relacional_y_bitacora_lectura(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-11: Consulta relacional de mantenimientos con joins a taller y registro de bitácora de lectura.
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento preventivo para consulta relacional",
        quien_autoriza="7423045",
        tipo="Preventivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=90.00
    )
    assert res_crear["status"] is True

    response = cliente_super_usuario.get("/mantenimiento-operacional")
    assert response.status_code == 200
    contenido = response.data.decode("utf-8")
    assert "Taller Mecánico Central" in contenido
    assert "GH567IJ" in contenido

    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor(dictionary=True)
    cur_sec.execute("SELECT cod_accion, cod_modulo, cedula_usuario FROM t_bitacora WHERE cod_accion = 2 AND cod_modulo = 3;")
    bitacora = cur_sec.fetchall()
    cur_sec.close()
    conn_sec.close()
    assert len(bitacora) >= 1
    assert bitacora[0]["cedula_usuario"] == "14094670"



# BLOQUE 3: RECIBOS, SEGURIDAD Y CONTROL DE ACCESO  (CP-MAN-INT-12 AL CP-MAN-INT-14)

def test_cp_man_int_12_consulta_recibo_mantenimiento_existente_y_rechazo_no_existente(cliente_super_usuario, taller_de_prueba):
    """
    CP-MAN-INT-12: Verificación de recibo de mantenimiento existente y rechazo de ID inexistente.
    """
    res_crear = MantenimientoOperacional.guardar(
        descripcion_general="Mantenimiento para visualización de recibo",
        quien_autoriza="7423045",
        tipo="Preventivo",
        fecha_solicitud=date.today().strftime("%Y-%m-%d"),
        fecha_completada=None,
        placa="GH567IJ",
        cod_taller=taller_de_prueba,
        cedula_usuario="14094670",
        costo_base=115.00,
        detalles=[{"descripcion_detalle": "Revisión técnica", "cantidad": 1}]
    )
    assert res_crear["status"] is True

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_mantenimiento FROM mantenimiento LIMIT 1;")
    cod_mantenimiento = cursor.fetchone()["cod_mantenimiento"]
    cursor.close()
    conn.close()

    # 1. Caso exitoso con ID existente
    response_ok = cliente_super_usuario.get(f"/mantenimiento-operacional/ver-recibo/{cod_mantenimiento}")
    assert response_ok.status_code == 200
    assert "GH567IJ" in response_ok.data.decode("utf-8")

    # 2. Caso rechazado con ID inexistente
    response_err = cliente_super_usuario.get("/mantenimiento-operacional/ver-recibo/99999", follow_redirects=True)
    assert response_err.status_code == 200
    assert "Mantenimiento no encontrado." in response_err.data.decode("utf-8")


def test_cp_man_int_13_acceso_anonimo_sin_sesion_bloqueado(app_client):
    """
    CP-MAN-INT-13: Bloqueo de acceso a usuarios anónimos sin sesión iniciada.
    Verifica que el decorador @requiere_permiso intercepte y redirija hacia /login.
    """
    # 1. Intento de acceso a listado
    resp_listar = app_client.get("/mantenimiento-operacional")
    assert resp_listar.status_code == 302
    assert "/login" in resp_listar.headers["Location"]

    # 2. Intento de acceso a formulario de creación
    resp_crear = app_client.get("/mantenimiento-operacional/crear")
    assert resp_crear.status_code == 302
    assert "/login" in resp_crear.headers["Location"]

    # 3. Intento de POST de inactivación
    resp_inactivar = app_client.post("/mantenimiento-operacional/inactivar/1")
    assert resp_inactivar.status_code == 302
    assert "/login" in resp_inactivar.headers["Location"]


def test_cp_man_int_14_acceso_rol_no_autorizado_bloqueado_por_rbac(cliente_sin_permiso, taller_de_prueba):
    """
    CP-MAN-INT-14: Bloqueo de acceso por control de rol RBAC (Vendedor sin permisos de creación).
    Verifica que Permiso.verificar_acceso bloquee la petición y redirija a '/', sin afectar la BD física.
    """
    response = cliente_sin_permiso.post(
        "/mantenimiento-operacional/crear",
        data={
            "descripcion_general": "Intento de registro sin permisos por parte de vendedor",
            "quien_autoriza": "7423045",
            "tipo": "Preventivo",
            "fecha_solicitud": date.today().strftime("%Y-%m-%d"),
            "placa": "GH567IJ",
            "cod_taller": str(taller_de_prueba),
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Acceso denegado: No tienes permisos para esta acción." in response.data.decode("utf-8")

    # Comprobar que no se insertó absolutamente nada en base de datos física
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mantenimiento;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()