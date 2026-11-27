"""
Pruebas de Integración para el Módulo Servicios
Archivo: tests/integration/test_servicios_integration.py
Base de datos: automall_test y seguridad_test (MySQL Real)
Casos: CP-SER-INT-01 al CP-SER-INT-14
"""

from datetime import date
from unittest.mock import patch
from tests.integration.conftest import obtener_conexion_negocio_test, obtener_conexion_seguridad_test
from models.servicios import Servicios
from utils.notificaciones_manager import NotificacionManager


def test_00_verificar_conexion_real_automall_test_servicios():
    """Verifica conexión física a MySQL y estado limpio inicial de las tablas de servicios."""
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE(), COUNT(*) FROM servicios;")
    nombre_bd, total_servicios = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM det_servicios;")
    total_detalles = cursor.fetchone()[0]

    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    estado_vehiculo = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    assert nombre_bd == "automall_test"
    assert total_servicios == 0
    assert total_detalles == 0
    assert estado_vehiculo == "Disponible"


#
# BLOQUE 1: CASOS DE INTEGRACIÓN DE REGISTRO (CP-SER-INT-01 AL CP-SER-INT-06)


def test_cp_ser_int_01_registro_exitoso_persistencia_transaccional_y_bitacora(cliente_autenticado):
    """
    CP-SER-INT-01: Registro exitoso transaccional de servicio.
    Verifica integración completa:
    1. HTTP POST /servicios/nuevo -> 200 tras redirección con mensaje flash
    2. Notificación emitida al staff con título y placa
    3. Persistencia en automall_test.servicios (cabecera con estado 'Activo')
    4. Persistencia en automall_test.det_servicios (detalle vinculado por cod_servicios)
    5. Sincronización atómica en automall_test.vehiculo (placa GH567IJ pasa a 'Servicio')
    6. Auditoría en seguridad_test.t_bitacora (cod_accion=1 CREAR, cod_modulo=9 SERVICIOS)
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            "/servicios/nuevo",
            data={
                "nombre_servicio": "Alineacion y Balanceo",
                "costo_base": "120.00",
                "costo_final": "150.00",
                "descripcion_especifica": "Alineacion laser de cuatro ruedas y balanceo dinamico",
                "fecha_realizacion": fecha_hoy,
                "placa": "GH567IJ"
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Servicio registrado correctamente." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "GH567IJ" in call_kwargs.get("notificacion_staff", {}).get("mensaje", "")

    # Verificación en BD negocio: cabecera
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT cod_servicios, nombre_servicio, costo_base, estado FROM servicios WHERE nombre_servicio = %s;",
        ("Alineacion y Balanceo",)
    )
    servicio_db = cursor.fetchone()

    assert servicio_db is not None
    cod_servicios = servicio_db["cod_servicios"]
    assert servicio_db["nombre_servicio"] == "Alineacion y Balanceo"
    assert float(servicio_db["costo_base"]) == 120.00
    assert servicio_db["estado"] == "Activo"

    # Verificación en BD negocio: detalle
    cursor.execute(
        "SELECT costo_final, descripcion_especifica, fecha_realizacion, placa FROM det_servicios WHERE cod_servicios = %s;",
        (cod_servicios,)
    )
    detalle_db = cursor.fetchone()
    assert detalle_db is not None
    assert float(detalle_db["costo_final"]) == 150.00
    assert detalle_db["placa"] == "GH567IJ"

    # Verificación en vehículo: pasa a 'Servicio'
    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    vehiculo_estado = cursor.fetchone()["estado"]
    cursor.close()
    conn.close()
    assert vehiculo_estado == "Servicio"

    # Verificación en bitácora: cod_accion = 1 (CREAR), cod_modulo = 9 (SERVICIOS)
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
    assert bitacora_db["cod_accion"] == 1
    assert bitacora_db["cod_modulo"] == 9


def test_cp_ser_int_02_registro_rechazado_placa_inexistente(cliente_autenticado):
    """
    CP-SER-INT-02: Rechazo de registro por placa inexistente en tabla vehiculo.
    Verifica que no se inserte en servicios ni det_servicios, y no se registre bitácora.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    response = cliente_autenticado.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Cambio de Frenos",
            "costo_base": "80.00",
            "costo_final": "90.00",
            "descripcion_especifica": "Cambio de pastillas de frenos delanteras",
            "fecha_realizacion": fecha_hoy,
            "placa": "ZZ999ZZ"  # Placa inexistente
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La placa seleccionada no existe en la tabla vehiculo." in response.get_data(as_text=True)

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM det_servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()

    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 9;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()


def test_cp_ser_int_03_registro_rechazado_nombre_invalido_caracteres_o_vacio(cliente_autenticado):
    """
    CP-SER-INT-03: Rechazo de registro por caracteres no permitidos en nombre_servicio.
    Verifica la expresión regular que solo admite letras y espacios.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    response = cliente_autenticado.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Servicio #1 @*$",
            "costo_base": "50.00",
            "costo_final": "60.00",
            "descripcion_especifica": "Descripcion valida de prueba tecnica",
            "fecha_realizacion": fecha_hoy,
            "placa": "GH567IJ"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "El nombre del servicio solo puede contener letras y espacios." in response.get_data(as_text=True)

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_ser_int_04_registro_rechazado_costo_base_negativo(cliente_autenticado):
    """
    CP-SER-INT-04: Rechazo de registro por costo base negativo (< 0).
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    response = cliente_autenticado.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Mantenimiento General",
            "costo_base": "-50.00",
            "costo_final": "100.00",
            "descripcion_especifica": "Revision de fluidos y mantenimiento general",
            "fecha_realizacion": fecha_hoy,
            "placa": "GH567IJ"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "El costo base no puede ser negativo." in response.get_data(as_text=True)

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_ser_int_05_registro_rechazado_fecha_anterior_a_hoy(cliente_autenticado):
    """
    CP-SER-INT-05: Rechazo de registro por fecha de realización anterior a hoy (fecha pasada).
    """
    response = cliente_autenticado.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Cambio de Correa",
            "costo_base": "75.00",
            "costo_final": "85.00",
            "descripcion_especifica": "Sustitucion de correa de distribucion",
            "fecha_realizacion": "2020-01-01",
            "placa": "GH567IJ"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La fecha de realización no puede ser anterior a hoy." in response.get_data(as_text=True)

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_ser_int_06_registro_rechazado_descripcion_demasiado_corta(cliente_autenticado):
    """
    CP-SER-INT-06: Rechazo de registro por descripción específica menor a 10 caracteres.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    response = cliente_autenticado.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Revision Electrica",
            "costo_base": "40.00",
            "costo_final": "50.00",
            "descripcion_especifica": "Arreglo",  # Menor a 10 caracteres
            "fecha_realizacion": fecha_hoy,
            "placa": "GH567IJ"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "La descripción específica debe tener al menos 10 caracteres." in response.get_data(as_text=True)

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()



# BLOQUE 2: CASOS DE EDICIÓN, ESTADOS Y FINALIZACIÓN (CP-SER-INT-07 AL CP-SER-INT-11)


def test_cp_ser_int_07_actualizacion_exitosa_bd_bitacora_notificacion(cliente_autenticado):
    """
    CP-SER-INT-07: Actualización exitosa de servicio existente en ambas tablas.
    Verifica persistencia en servicios y det_servicios, bitácora (cod_accion=3) y notificación.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Inicial", 100.00, "Activo")
    )
    cod_servicios = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (120.00, "Detalle inicial de prueba", fecha_hoy, "GH567IJ", cod_servicios)
    )
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            f"/servicios/editar/{cod_servicios}",
            data={
                "nombre_servicio": "Mantenimiento Preventivo Total",
                "costo_base": "180.00",
                "costo_final": "200.00",
                "descripcion_especifica": "Cambio de aceite sintetico y filtros de aire",
                "fecha_realizacion": fecha_hoy
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Servicio actualizado correctamente." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Mantenimiento Preventivo Total" in call_kwargs.get("notificacion_staff", {}).get("mensaje", "")

    # Verificación en BD negocio: cabecera y detalle actualizados
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre_servicio, costo_base FROM servicios WHERE cod_servicios = %s;", (cod_servicios,))
    serv_db = cursor.fetchone()
    assert serv_db["nombre_servicio"] == "Mantenimiento Preventivo Total"
    assert float(serv_db["costo_base"]) == 180.00

    cursor.execute("SELECT costo_final, descripcion_especifica FROM det_servicios WHERE cod_servicios = %s;", (cod_servicios,))
    det_db = cursor.fetchone()
    assert float(det_db["costo_final"]) == 200.00
    assert det_db["descripcion_especifica"] == "Cambio de aceite sintetico y filtros de aire"
    cursor.close()
    conn.close()

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
    assert bitacora_db["cod_modulo"] == 9


def test_cp_ser_int_08_actualizacion_cambio_vehiculo_sincronizacion_estados(cliente_autenticado):
    """
    CP-SER-INT-08: Actualización con cambio de vehículo y sincronización atómica de estados.
    Verifica que al reasignar el servicio de GH567IJ a IJ678KL:
    1. El vehículo original (GH567IJ) retorne a 'Disponible'
    2. El nuevo vehículo (IJ678KL) pase a 'Servicio'
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("UPDATE vehiculo SET estado = 'Servicio' WHERE placa = 'GH567IJ';")
    cursor.execute("UPDATE vehiculo SET estado = 'Disponible' WHERE placa = 'IJ678KL';")
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Reasignable", 100.00, "Activo")
    )
    cod_servicios = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (110.00, "Reasignacion vehicular de prueba", fecha_hoy, "GH567IJ", cod_servicios)
    )
    cursor.close()
    conn.close()

    resultado = Servicios.actualizar(
        cod_servicios,
        "Servicio Reasignado Exitoso",
        150.00,
        180.00,
        "Reasignacion vehicular de prueba completada",
        fecha_hoy,
        "IJ678KL",
        cedula_usuario="7423045"
    )
    assert resultado["status"] is True

    # Verificación en BD: GH567IJ vuelve a 'Disponible' e IJ678KL pasa a 'Servicio'
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Disponible"
    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'IJ678KL';")
    assert cursor.fetchone()["estado"] == "Servicio"
    cursor.close()
    conn.close()


def test_cp_ser_int_09_inactivacion_logica_exitosa(cliente_autenticado):
    """
    CP-SER-INT-09: Desactivación lógica de servicio (estado = 'Inactivo').
    Verifica que el registro no se destruya físicamente y se audite la desactivación.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Por Inactivar", 80.00, "Activo")
    )
    cod_servicios = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (90.00, "Detalle de prueba para inactivar", fecha_hoy, "GH567IJ", cod_servicios)
    )
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            f"/servicios/inactivar/{cod_servicios}",
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Servicio inactivado correctamente." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Servicio Inactivado" in call_kwargs.get("notificacion_staff", {}).get("titulo", "")

    # Verificación en BD: estado cambia a 'Inactivo'
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM servicios WHERE cod_servicios = %s;", (cod_servicios,))
    assert cursor.fetchone()["estado"] == "Inactivo"
    cursor.close()
    conn.close()

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
    assert bitacora_db["cod_modulo"] == 9


def test_cp_ser_int_10_finalizacion_exitosa_servicio_y_reactivacion_vehiculo(cliente_autenticado):
    """
    CP-SER-INT-10: Finalización exitosa de servicio y reactivación del vehículo.
    Verifica que:
    1. servicios.estado pase a 'Finalizado'
    2. det_servicios.costo_final se actualice con el monto final
    3. vehiculo.estado se reactive de 'Servicio' a 'Disponible'
    4. Se registre bitácora y notificación al staff
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("UPDATE vehiculo SET estado = 'Servicio' WHERE placa = 'GH567IJ';")
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Para Finalizar", 90.00, "Activo")
    )
    cod_servicios = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (None, "Servicio en proceso de finalizacion", fecha_hoy, "GH567IJ", cod_servicios)
    )
    cursor.close()
    conn.close()

    with patch.object(NotificacionManager, 'crear_multiple', wraps=NotificacionManager.crear_multiple) as spy_notif:
        response = cliente_autenticado.post(
            f"/servicios/finalizar/{cod_servicios}/GH567IJ",
            data={"costo_final": "175.50"},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert "Servicio finalizado y vehículo reactivado." in response.get_data(as_text=True)
        assert spy_notif.called
        call_kwargs = spy_notif.call_args.kwargs
        assert "Servicio Finalizado" in call_kwargs.get("notificacion_staff", {}).get("titulo", "")

    # Verificación en BD: servicio 'Finalizado' y costo_final guardado
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM servicios WHERE cod_servicios = %s;", (cod_servicios,))
    assert cursor.fetchone()["estado"] == "Finalizado"

    cursor.execute("SELECT costo_final FROM det_servicios WHERE cod_servicios = %s;", (cod_servicios,))
    assert float(cursor.fetchone()["costo_final"]) == 175.50

    # Verificación en vehículo: reactivado a 'Disponible'
    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Disponible"
    cursor.close()
    conn.close()

    # Verificación en bitácora: cod_accion = 3
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
    assert bitacora_db["cod_modulo"] == 9


def test_cp_ser_int_11_rechazo_finalizacion_sin_costo_final(cliente_autenticado):
    """
    CP-SER-INT-11: Rechazo de finalización si no se suministra ni existe costo_final.
    Verifica que el servicio permanezca 'Activo' y el vehículo continúe en 'Servicio'.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("UPDATE vehiculo SET estado = 'Servicio' WHERE placa = 'GH567IJ';")
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Sin Costo", 90.00, "Activo")
    )
    cod_servicios = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (None, "Sin costo registrado todavia", fecha_hoy, "GH567IJ", cod_servicios)
    )
    cursor.close()
    conn.close()

    response = cliente_autenticado.post(
        f"/servicios/finalizar/{cod_servicios}/GH567IJ",
        data={"costo_final": ""},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Debe registrar el costo final antes de finalizar el servicio." in response.get_data(as_text=True)

    # Verificación en BD: servicios sigue Activo y vehículo sigue en Servicio
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT estado FROM servicios WHERE cod_servicios = %s;", (cod_servicios,))
    assert cursor.fetchone()["estado"] == "Activo"

    cursor.execute("SELECT estado FROM vehiculo WHERE placa = 'GH567IJ';")
    assert cursor.fetchone()["estado"] == "Servicio"
    cursor.close()
    conn.close()



# BLOQUE 3: CONSULTAS RELACIONALES, RECIBO Y CONTROL RBAC (CP-SER-INT-12 AL 14)


def test_cp_ser_int_12_consulta_servicios_relacional_y_bitacora_lectura(cliente_autenticado):
    """
    CP-SER-INT-12: Consulta de servicios (GET /servicios) con JOIN relacional.
    Verifica:
    1. Renderizado HTML 200 de plantilla index.html
    2. Filtrado: muestra servicios en estado 'Activo' o 'Finalizado', omitiendo 'Inactivo'
    3. Registro de auditoría de lectura en t_bitacora (cod_accion=2 LEER, cod_modulo=9 SERVICIOS)
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    # 1 Servicio Activo
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Activo Visible", 100.00, "Activo")
    )
    cod_s1 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (120.00, "Detalle servicio activo visible", fecha_hoy, "GH567IJ", cod_s1)
    )

    # 1 Servicio Inactivo (debe ser excluido de la consulta)
    cursor.execute(
        "INSERT INTO servicios (nombre_servicio, costo_base, estado) VALUES (%s, %s, %s);",
        ("Servicio Inactivo Oculto", 80.00, "Inactivo")
    )
    cod_s2 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO det_servicios (costo_final, descripcion_especifica, fecha_realizacion, placa, cod_servicios) VALUES (%s, %s, %s, %s, %s);",
        (90.00, "Detalle servicio inactivo", fecha_hoy, "GH567IJ", cod_s2)
    )
    cursor.close()
    conn.close()

    response = cliente_autenticado.get("/servicios")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verificación en HTML: activo presente, inactivo ausente
    assert "Servicio Activo Visible" in html
    assert "Servicio Inactivo Oculto" not in html

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
    assert bitacora_db["cod_accion"] == 2
    assert bitacora_db["cod_modulo"] == 9


def test_cp_ser_int_13_acceso_anonimo_sin_sesion_bloqueado(app_client):
    """
    CP-SER-INT-13: Acceso anónimo sin sesión iniciada.
    Verifica que el decorador @requiere_permiso intercepte solicitudes sin sesión
    y redirija con HTTP 302 a /login, protegiendo las tablas de negocio.
    """
    # 1. Consulta sin sesión
    res_get = app_client.get("/servicios", follow_redirects=False)
    assert res_get.status_code == 302
    assert res_get.headers["Location"].endswith("/login")

    # 2. Intento de creación sin sesión
    res_post = app_client.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Servicio Intruso",
            "costo_base": "100.00",
            "costo_final": "120.00",
            "descripcion_especifica": "Intento de registro sin sesion",
            "fecha_realizacion": date.today().strftime("%Y-%m-%d"),
            "placa": "GH567IJ"
        },
        follow_redirects=False
    )
    assert res_post.status_code == 302
    assert res_post.headers["Location"].endswith("/login")

    # 3. Verificación de integridad: 0 filas en BD negocio
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios;")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()


def test_cp_ser_int_14_acceso_rol_no_autorizado_bloqueado_por_rbac(cliente_sin_permiso):
    """
    CP-SER-INT-14: Control de acceso relacional RBAC contra seguridad_test.
    Usuario: Jeymar Inciarte (Rol 3 = Vendedor).
    En seguridad_test.t_rol_permiso el Rol 3 carece de permiso de creación (91) e inactivación (94).
    Verifica que las peticiones POST de escritura sean denegadas con HTTP 302 hacia '/'.
    """
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    # 1. Intento de creación con Rol 3
    res_post = cliente_sin_permiso.post(
        "/servicios/nuevo",
        data={
            "nombre_servicio": "Servicio Vendedor No Permitido",
            "costo_base": "100.00",
            "costo_final": "120.00",
            "descripcion_especifica": "Intento no autorizado de creacion",
            "fecha_realizacion": fecha_hoy,
            "placa": "GH567IJ"
        },
        follow_redirects=False
    )
    assert res_post.status_code == 302
    assert res_post.headers["Location"].endswith("/")

    # 2. Verificación de integridad: ninguna fila guardada en automall_test
    conn = obtener_conexion_negocio_test()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM servicios WHERE nombre_servicio = 'Servicio Vendedor No Permitido';")
    assert cursor.fetchone()[0] == 0
    cursor.close()
    conn.close()

    # 3. Verificación de bitácora: 0 registros de creación en seguridad_test
    conn_sec = obtener_conexion_seguridad_test()
    cur_sec = conn_sec.cursor()
    cur_sec.execute("SELECT COUNT(*) FROM t_bitacora WHERE cod_accion = 1 AND cod_modulo = 9;")
    assert cur_sec.fetchone()[0] == 0
    cur_sec.close()
    conn_sec.close()