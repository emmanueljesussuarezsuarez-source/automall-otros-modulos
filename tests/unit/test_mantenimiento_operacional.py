"""
Módulo de Pruebas Unitarias para el Módulo de Mantenimiento Operacional
Archivo: tests/unit/test_mantenimiento_operacional.py
Metodología: Caja blanca, partición de equivalencia, análisis de valores límite y mocks.
Aislamiento: Bases de datos MySQL simuladas (automall y seguridad sin llamadas reales).
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch
import pytest

from app import app
from models.mantenimiento_operacional import MantenimientoOperacional
from utils.validaciones_mantenimiento_operacional import ValidacionMantenimientoOperacional



# CONSTANTES DE FECHA PARA PRUEBAS TEMPORALES

HOY = date.today().strftime("%Y-%m-%d")
MANANA = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
PASADO_MANANA = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
AYER = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")



# FIXTURES Y CONFIGURACIÓN DE MOCKS DE AISLAMIENTO

@pytest.fixture
def conexion_mock():
    """
    Simula la conexión principal a MySQL (automall) y su cursor.
    Garantiza aislamiento total sin tocar la base de datos real.
    """
    conexion = MagicMock()
    cursor = MagicMock()

    conexion.cursor.return_value = cursor
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    cursor.lastrowid = 1

    return conexion, cursor


@pytest.fixture
def conexion_seguridad_mock():
    """
    Simula la conexión secundaria a MySQL (seguridad) para usuarios y roles.
    """
    conexion_sec = MagicMock()
    cursor_sec = MagicMock()

    conexion_sec.cursor.return_value = cursor_sec
    cursor_sec.fetchall.return_value = []
    cursor_sec.fetchone.return_value = None

    return conexion_sec, cursor_sec


@pytest.fixture
def app_client():
    """Cliente de pruebas HTTP de Flask configurado en modo TESTING."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion.clear()
        yield client


@pytest.fixture
def cliente_autenticado(app_client):
    """Cliente con sesión activa y rol Superusuario/Administrador (acceso total)."""
    with app_client.session_transaction() as sesion:
        sesion["cedula_usuario"] = "12345678"
        sesion["cod_rol"] = 1
    return app_client


@pytest.fixture
def cliente_sin_permiso(app_client):
    """Cliente con sesión activa pero sin permisos asignados para el módulo."""
    with app_client.session_transaction() as sesion:
        sesion["cedula_usuario"] = "87654321"
        sesion["cod_rol"] = 3
    return app_client



# VERIFICACIÓN DE CONFIGURACIÓN INICIAL


def test_configuracion_inicial_fixtures(conexion_mock, conexion_seguridad_mock, app_client, cliente_autenticado):
    """Verifica que los imports, helpers de fechas y todos los fixtures inicien correctamente."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    assert conexion is not None
    assert cursor is not None
    assert con_sec is not None
    assert cur_sec is not None
    assert app_client is not None
    assert cliente_autenticado is not None
    assert HOY is not None
    assert MANANA > HOY
    assert AYER < HOY

  
# BLOQUE 2: PRUEBAS DE VALIDACIONES (CP-MOP-01 AL CP-MOP-08)


def test_cp_mop_01_descripcion_general_valida_e_invalida():
    """CP-MOP-01: Validación de descripción general (mínimo 10 caracteres tras strip)."""
    # Casos válidos
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("Mantenimiento preventivo general") is None
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("1234567890") is None  # Límite inferior exacto (10 chars)
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("  Revisión de frenos  ") is None

    # Casos inválidos (vacío, None, espacios, menor a 10 caracteres)
    msg_esperado = "La descripción general debe tener al menos 10 caracteres."
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("") == msg_esperado
    assert ValidacionMantenimientoOperacional.validar_descripcion_general(None) == msg_esperado
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("   ") == msg_esperado
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("Corto") == msg_esperado
    assert ValidacionMantenimientoOperacional.validar_descripcion_general("123456789") == msg_esperado  # Límite inferior - 1 (9 chars)


def test_cp_mop_02_quien_autoriza_valido_e_invalido():
    """CP-MOP-02: Validación del usuario autorizador (obligatorio y estrictamente numérico)."""
    # Válidos (cédula o ID numérico)
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("12345678") is None
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza(12345678) is None
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza(" 99887766 ") is None

    # Vacío o None
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("") == "Debe seleccionar quién autoriza."
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza(None) == "Debe seleccionar quién autoriza."
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("   ") == "Debe seleccionar quién autoriza."

    # No numérico
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("admin") == "El valor de autorización debe ser numérico."
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("V-12345678") == "El valor de autorización debe ser numérico."
    assert ValidacionMantenimientoOperacional.validar_quien_autoriza("1234A") == "El valor de autorización debe ser numérico."


def test_cp_mop_03_tipo_mantenimiento_valido_e_invalido():
    """CP-MOP-03: Validación del tipo de mantenimiento (obligatorio: 'Preventivo' o 'Correctivo')."""
    # Válidos
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("Preventivo") is None
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("Correctivo") is None

    # Vacíos
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("") == "Debe seleccionar el tipo de mantenimiento."
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento(None) == "Debe seleccionar el tipo de mantenimiento."
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("   ") == "Debe seleccionar el tipo de mantenimiento."

    # Valores no permitidos
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("Emergencia") == "El tipo de mantenimiento no es válido."
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("preventivo") == "El tipo de mantenimiento no es válido."
    assert ValidacionMantenimientoOperacional.validar_tipo_mantenimiento("General") == "El tipo de mantenimiento no es válido."


def test_cp_mop_04_fecha_solicitud_valida_e_invalida():
    """CP-MOP-04: Validación de fecha de solicitud (formato YYYY-MM-DD y restricción de no ser pasada)."""
    # Fechas válidas (hoy o futuras)
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada(HOY, "Fecha de solicitud") is None
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada(MANANA, "Fecha de solicitud") is None
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada(PASADO_MANANA, "Fecha de solicitud") is None

    # Vacío o None
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada("", "Fecha de solicitud") == "Fecha de solicitud es obligatoria."
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada(None, "Fecha de solicitud") == "Fecha de solicitud es obligatoria."

    # Formato inválido
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada("2026/11/20", "Fecha de solicitud") == "El formato de fecha de solicitud no es válido. Use YYYY-MM-DD."
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada("20-11-2026", "Fecha de solicitud") == "El formato de fecha de solicitud no es válido. Use YYYY-MM-DD."
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada("invalido", "Fecha de solicitud") == "El formato de fecha de solicitud no es válido. Use YYYY-MM-DD."

    # Fecha anterior a hoy (pasada)
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada(AYER, "Fecha de solicitud") == "Fecha de solicitud no puede ser anterior a hoy."
    assert ValidacionMantenimientoOperacional.validar_fecha_no_pasada("2020-01-01", "Fecha de solicitud") == "Fecha de solicitud no puede ser anterior a hoy."


def test_cp_mop_05_fecha_completada_valida_e_invalida():
    """CP-MOP-05: Validación de fecha completada (opcional, formato YYYY-MM-DD y >= fecha_solicitud)."""
    # Casos válidos: opcional vacía o fechas iguales / posteriores
    assert ValidacionMantenimientoOperacional.validar_fecha_completada("", HOY) is None
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(None, HOY) is None
    assert ValidacionMantenimientoOperacional.validar_fecha_completada("   ", HOY) is None
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(HOY, HOY) is None
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(MANANA, HOY) is None
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(PASADO_MANANA, MANANA) is None

    # Formato inválido en fecha completada
    assert ValidacionMantenimientoOperacional.validar_fecha_completada("2026/12/01", HOY) == "El formato de fecha completada no es válido. Use YYYY-MM-DD."

    # Fecha de solicitud con formato inválido
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(MANANA, "formato_invalido") == "La fecha de solicitud no es válida."

    # Inconsistencia temporal: fecha completada anterior a la fecha de solicitud
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(HOY, MANANA) == "La fecha completada no puede ser anterior a la fecha de solicitud."
    assert ValidacionMantenimientoOperacional.validar_fecha_completada(AYER, HOY) == "La fecha completada no puede ser anterior a la fecha de solicitud."


def test_cp_mop_06_placa_valida_e_invalida():
    """CP-MOP-06: Validación de placa vehicular (obligatoria, longitud entre 5 y 7 caracteres)."""
    # Válidos (5, 6 y 7 caracteres)
    assert ValidacionMantenimientoOperacional.validar_placa("A1B2C") is None       # 5 caracteres
    assert ValidacionMantenimientoOperacional.validar_placa("ABC123") is None     # 6 caracteres
    assert ValidacionMantenimientoOperacional.validar_placa("AB123CD") is None    # 7 caracteres
    assert ValidacionMantenimientoOperacional.validar_placa("  XYZ789  ") is None # Limpieza de espacios

    # Vacío o None
    assert ValidacionMantenimientoOperacional.validar_placa("") == "Debe seleccionar una placa."
    assert ValidacionMantenimientoOperacional.validar_placa(None) == "Debe seleccionar una placa."
    assert ValidacionMantenimientoOperacional.validar_placa("   ") == "Debe seleccionar una placa."

    # Fuera de rango de longitud (< 5 o > 7)
    assert ValidacionMantenimientoOperacional.validar_placa("A") == "La placa debe tener entre 5 y 7 caracteres."
    assert ValidacionMantenimientoOperacional.validar_placa("AB12") == "La placa debe tener entre 5 y 7 caracteres."      # 4 caracteres (límite inferior - 1)
    assert ValidacionMantenimientoOperacional.validar_placa("ABC12345") == "La placa debe tener entre 5 y 7 caracteres."  # 8 caracteres (límite superior + 1)


def test_cp_mop_07_cod_taller_valido_e_invalido():
    """CP-MOP-07: Validación del código de taller (obligatorio y estrictamente numérico)."""
    # Válidos
    assert ValidacionMantenimientoOperacional.validar_cod_taller("1") is None
    assert ValidacionMantenimientoOperacional.validar_cod_taller("25") is None
    assert ValidacionMantenimientoOperacional.validar_cod_taller(10) is None
    assert ValidacionMantenimientoOperacional.validar_cod_taller("  5  ") is None

    # Vacío o None
    assert ValidacionMantenimientoOperacional.validar_cod_taller("") == "Debe seleccionar un taller."
    assert ValidacionMantenimientoOperacional.validar_cod_taller(None) == "Debe seleccionar un taller."
    assert ValidacionMantenimientoOperacional.validar_cod_taller("   ") == "Debe seleccionar un taller."

    # No numérico
    assert ValidacionMantenimientoOperacional.validar_cod_taller("abc") == "El código del taller debe ser numérico."
    assert ValidacionMantenimientoOperacional.validar_cod_taller("T-01") == "El código del taller debe ser numérico."
    assert ValidacionMantenimientoOperacional.validar_cod_taller("-1") == "El código del taller debe ser numérico."


def test_cp_mop_08_validar_mantenimiento_integral():
    """CP-MOP-08: Validación integral del conjunto completo de campos de mantenimiento."""
    datos_validos = {
        "descripcion_general": "Mantenimiento preventivo general de frenos y fluidos",
        "quien_autoriza": "12345678",
        "tipo": "Preventivo",
        "fecha_solicitud": HOY,
        "fecha_completada": MANANA,
        "placa": "ABC123",
        "cod_taller": "1"
    }

    # 1. Conjunto totalmente válido
    es_valido, errores = ValidacionMantenimientoOperacional.validar_mantenimiento(datos_validos)
    assert es_valido is True
    assert len(errores) == 0

    # 2. Conjunto con fecha completada omitida (opcional válida)
    datos_sin_completada = datos_validos.copy()
    datos_sin_completada["fecha_completada"] = None
    es_valido, errores = ValidacionMantenimientoOperacional.validar_mantenimiento(datos_sin_completada)
    assert es_valido is True
    assert len(errores) == 0

    # 3. Conjunto con múltiples fallas concurrentes
    datos_invalidos = {
        "descripcion_general": "Corta",          # < 10 caracteres
        "quien_autoriza": "invalido",            # No numérico
        "tipo": "Invalido",                      # No es Preventivo ni Correctivo
        "fecha_solicitud": AYER,                 # Anterior a hoy
        "fecha_completada": "2020-01-01",        # Anterior a fecha_solicitud
        "placa": "AB",                           # < 5 caracteres
        "cod_taller": "no_num"                   # No numérico
    }
    es_valido, errores = ValidacionMantenimientoOperacional.validar_mantenimiento(datos_invalidos)
    assert es_valido is False
    assert len(errores) == 7
    assert "descripcion_general" in errores
    assert "quien_autoriza" in errores
    assert "tipo" in errores
    assert "fecha_solicitud" in errores
    assert "fecha_completada" in errores
    assert "placa" in errores
    assert "cod_taller" in errores

# BLOQUE 3: PRUEBAS DE GUARDAR Y EXISTENCIAS (CP-MOP-09 AL CP-MOP-18)


def test_cp_mop_09_validar_existencias_exitoso(conexion_mock, conexion_seguridad_mock):
    """CP-MOP-09: Verificación exitosa de existencias (vehículo, taller activo y usuario autorizador existen)."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    # Simular que vehiculo existe en automall y taller existe y activo
    cursor.fetchone.side_effect = [{"placa": "ABC123"}, {"cod_taller": 1}]
    # Simular que el usuario autorizador existe en seguridad
    cur_sec.fetchone.return_value = {"cedula_usuario": "12345678"}

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        res = MantenimientoOperacional.validar_existencias("ABC123", "1", "12345678")

    assert res["status"] is True


def test_cp_mop_10_validar_existencias_placa_inexistente(conexion_mock, conexion_seguridad_mock):
    """CP-MOP-10: Rechazo en validar existencias cuando la placa no existe en la tabla vehiculo."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    cursor.fetchone.return_value = None  # No existe vehiculo

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        res = MantenimientoOperacional.validar_existencias("ZZZ999", "1", "12345678")

    assert res["status"] is False
    assert res["mensaje"] == "La placa seleccionada no existe en la tabla vehiculo."


def test_cp_mop_11_validar_existencias_taller_inexistente(conexion_mock, conexion_seguridad_mock):
    """CP-MOP-11: Rechazo en validar existencias cuando el taller no existe o está inactivo."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    cursor.fetchone.side_effect = [{"placa": "ABC123"}, None]  # Vehículo existe, pero taller no

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        res = MantenimientoOperacional.validar_existencias("ABC123", "99", "12345678")

    assert res["status"] is False
    assert res["mensaje"] == "El taller seleccionado no existe o no está activo."


def test_cp_mop_12_validar_existencias_autorizador_inexistente(conexion_mock, conexion_seguridad_mock):
    """CP-MOP-12: Rechazo en validar existencias cuando el autorizador no existe en t_usuario."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    cursor.fetchone.side_effect = [{"placa": "ABC123"}, {"cod_taller": 1}]
    cur_sec.fetchone.return_value = None  # Usuario autorizador no existe en seguridad

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        res = MantenimientoOperacional.validar_existencias("ABC123", "1", "99999999")

    assert res["status"] is False
    assert res["mensaje"] == "La persona que autoriza no existe en la tabla t_usuario."


def test_cp_mop_13_validar_existencias_excepcion_bd(conexion_mock, conexion_seguridad_mock):
    """CP-MOP-13: Control de excepción inesperada durante la consulta de existencias en BD."""
    conexion, cursor = conexion_mock
    con_sec, cur_sec = conexion_seguridad_mock

    cursor.execute.side_effect = Exception("Fallo de socket en BD")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        res = MantenimientoOperacional.validar_existencias("ABC123", "1", "12345678")

    assert res["status"] is False
    assert "Error validando existencias: Fallo de socket en BD" in res["mensaje"]


def test_cp_mop_14_guardar_exitoso_con_detalles_y_bitacora(conexion_mock):
    """CP-MOP-14: Registro exitoso completo con items de detalle, estado Mantenimiento, bitácora y commit."""
    conexion, cursor = conexion_mock
    cursor.lastrowid = 15

    detalles = [
        {"descripcion_detalle": "Cambio de aceite 20W50", "cantidad": 4},
        {"descripcion_detalle": "Filtro de aire", "cantidad": 1}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.guardar(
            descripcion_general="Mantenimiento preventivo general de 50000 km",
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=MANANA,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678",
            costo_base=150.0,
            costo_final=None,
            detalles=detalles
        )

    assert res["status"] is True
    assert res["mensaje"] == "Mantenimiento registrado correctamente."
    # Debe ejecutar: 1 insert mantenimiento + 2 insert mantenimiento_cant + 1 insert det_mantenimiento + 1 update vehiculo
    assert cursor.execute.call_count == 5
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=3)


def test_cp_mop_15_guardar_exitoso_sin_detalles_ni_completada(conexion_mock):
    """CP-MOP-15: Registro exitoso sin lista de repuestos/detalles y sin fecha de finalización."""
    conexion, cursor = conexion_mock
    cursor.lastrowid = 20

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.guardar(
            descripcion_general="Revisión básica de fluidos y frenos",
            quien_autoriza="12345678",
            tipo="Correctivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678",
            costo_base=80.0,
            costo_final=None,
            detalles=None
        )

    assert res["status"] is True
    assert cursor.execute.call_count == 3  # 1 mantenimiento + 1 det_mantenimiento + 1 update vehiculo
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=3)


def test_cp_mop_16_guardar_rechazo_por_validacion_sin_abrir_bd():
    """CP-MOP-16: Rechazo inmediato al guardar con datos inválidos sin abrir conexión a BD."""
    with patch("models.db.ConexionBD.obtener_conexion") as mock_conn:
        res = MantenimientoOperacional.guardar(
            descripcion_general="Corta",  # Inválido (< 10 caracteres)
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert res["mensaje"] == "La descripción general debe tener al menos 10 caracteres."
    mock_conn.assert_not_called()


def test_cp_mop_17_guardar_rechazo_por_existencias_bd():
    """CP-MOP-17: Rechazo de guardado al fallar la comprobación de existencias vehiculares."""
    with patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias",
               return_value={"status": False, "mensaje": "La placa seleccionada no existe en la tabla vehiculo."}), \
         patch("models.db.ConexionBD.obtener_conexion") as mock_conn:

        res = MantenimientoOperacional.guardar(
            descripcion_general="Mantenimiento preventivo general de 50000 km",
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ZZZ999",
            cod_taller="1",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert res["mensaje"] == "La placa seleccionada no existe en la tabla vehiculo."
    mock_conn.assert_not_called()


def test_cp_mop_18_guardar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-MOP-18: Manejo de excepción SQL durante inserción ejecutando reversión transaccional (ROLLBACK)."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo de clave foránea o conexión caída")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.guardar(
            descripcion_general="Mantenimiento preventivo general de 50000 km",
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert "Error en la base de datos: Fallo de clave foránea o conexión caída" in res["mensaje"]
    conexion.rollback.assert_called_once()
    mock_bitacora.assert_not_called()


   
# BLOQUE 4: PRUEBAS DE ACTUALIZAR (CP-MOP-19 AL CP-MOP-23)


def test_cp_mop_19_actualizar_exitoso_con_detalles_y_bitacora(conexion_mock):
    """CP-MOP-19: Actualización completa con reemplazo de items de detalle, bitácora y commit."""
    conexion, cursor = conexion_mock

    detalles = [
        {"descripcion_detalle": "Pastillas de freno delanteras", "cantidad": 2},
        {"descripcion_detalle": "Líquido de frenos DOT4", "cantidad": 1}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.actualizar(
            cod_mantenimiento=5,
            descripcion_general="Actualización de mantenimiento general de frenos",
            quien_autoriza="12345678",
            tipo="Correctivo",
            fecha_solicitud=HOY,
            fecha_completada=MANANA,
            placa="ABC123",
            cod_taller="2",
            cedula_usuario="12345678",
            costo_base=200.0,
            costo_final=250.0,
            detalles=detalles
        )

    assert res["status"] is True
    assert res["mensaje"] == "Mantenimiento actualizado correctamente."
    # Debe ejecutar: 1 update mantenimiento + 1 delete mantenimiento_cant + 2 insert mantenimiento_cant + 1 update det_mantenimiento + 1 update vehiculo = 6
    assert cursor.execute.call_count == 6
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=3)


def test_cp_mop_20_actualizar_exitoso_sin_detalles(conexion_mock):
    """CP-MOP-20: Actualización exitosa sin lista de detalles adicionales y fecha_completada opcional omitida."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.actualizar(
            cod_mantenimiento=5,
            descripcion_general="Ajuste menor de suspensión sin repuestos",
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678",
            costo_base=120.0,
            costo_final=None,
            detalles=None
        )

    assert res["status"] is True
    # Debe ejecutar: 1 update mantenimiento + 1 delete mantenimiento_cant + 1 update det_mantenimiento + 1 update vehiculo = 4
    assert cursor.execute.call_count == 4
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=3)


def test_cp_mop_21_actualizar_rechazo_por_validacion_sin_abrir_bd():
    """CP-MOP-21: Rechazo inmediato en actualizar ante datos inválidos sin aperturar conexión a BD."""
    with patch("models.db.ConexionBD.obtener_conexion") as mock_conn:
        res = MantenimientoOperacional.actualizar(
            cod_mantenimiento=5,
            descripcion_general="Actualización válida con más de diez caracteres",
            quien_autoriza="no_numerico",  # Inválido
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert res["mensaje"] == "El valor de autorización debe ser numérico."
    mock_conn.assert_not_called()


def test_cp_mop_22_actualizar_rechazo_por_existencias_bd():
    """CP-MOP-22: Rechazo de actualización al detectar que el taller asociado no existe o está inactivo."""
    with patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias",
               return_value={"status": False, "mensaje": "El taller seleccionado no existe o no está activo."}), \
         patch("models.db.ConexionBD.obtener_conexion") as mock_conn:

        res = MantenimientoOperacional.actualizar(
            cod_mantenimiento=5,
            descripcion_general="Actualización de mantenimiento general de frenos",
            quien_autoriza="12345678",
            tipo="Preventivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="99",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert res["mensaje"] == "El taller seleccionado no existe o no está activo."
    mock_conn.assert_not_called()


def test_cp_mop_23_actualizar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-MOP-23: Manejo de excepción SQL durante la actualización ejecutando reversión transaccional (ROLLBACK)."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Deadlock detectado en MySQL")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.validar_existencias", return_value={"status": True}), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.actualizar(
            cod_mantenimiento=5,
            descripcion_general="Actualización de mantenimiento general de frenos",
            quien_autoriza="12345678",
            tipo="Correctivo",
            fecha_solicitud=HOY,
            fecha_completada=None,
            placa="ABC123",
            cod_taller="1",
            cedula_usuario="12345678"
        )

    assert res["status"] is False
    assert "Error en la base de datos: Deadlock detectado en MySQL" in res["mensaje"]
    conexion.rollback.assert_called_once()
    mock_bitacora.assert_not_called()

   
# BLOQUE 5: PRUEBAS DE INACTIVAR Y FINALIZAR (CP-MOP-24 AL CP-MOP-28)


def test_cp_mop_24_inactivar_exitoso_con_bitacora(conexion_mock):
    """CP-MOP-24: Inactivación lógica exitosa de mantenimiento (estado Inactivo), bitácora y commit."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.inactivar(cod_mantenimiento=10, cedula_usuario="12345678")

    assert res is True
    assert cursor.execute.call_count == 1
    # Verificar que el UPDATE contenga 'Inactivo'
    sql_ejecutado = cursor.execute.call_args[0][0]
    assert "estado = 'Inactivo'" in sql_ejecutado
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=3)


def test_cp_mop_25_inactivar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-MOP-25: Captura de fallo SQL en inactivación, ejecución de rollback y re-lanzamiento de excepción."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo de conexión durante inactivación")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        with pytest.raises(Exception, match="Fallo de conexión durante inactivación"):
            MantenimientoOperacional.inactivar(cod_mantenimiento=10, cedula_usuario="12345678")

    conexion.rollback.assert_called_once()
    mock_bitacora.assert_not_called()


def test_cp_mop_26_finalizar_exitoso_con_detalles_liberacion_vehiculo_y_bitacora(conexion_mock):
    """CP-MOP-26: Finalización exitosa con costo final, detalles, liberación de vehículo a 'Disponible' y bitácora."""
    conexion, cursor = conexion_mock

    detalles = [
        {"descripcion_detalle": "Mano de obra especializada", "cantidad": 1},
        {"descripcion_detalle": "Empacaduras de cárter", "cantidad": 2}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.finalizar(
            cod_mantenimiento=8,
            placa="ABC123",
            cedula_usuario="12345678",
            costo_final=320.50,
            detalles=detalles
        )

    assert res is True
    # 1 update mantenimiento (Finalizado) + 1 update det_mantenimiento (CURDATE) + 2 insert detalles + 1 update vehiculo (Disponible) = 5
    assert cursor.execute.call_count == 5

    # Validar que se actualice el vehículo a 'Disponible'
    llamadas_sql = [call[0][0] for call in cursor.execute.call_args_list]
    assert any("estado = 'Finalizado'" in sql for sql in llamadas_sql)
    assert any("estado = 'Disponible'" in sql for sql in llamadas_sql)

    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=3)


def test_cp_mop_27_finalizar_exitoso_sin_detalles(conexion_mock):
    """CP-MOP-27: Finalización exitosa sin agregar repuestos/detalles adicionales."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        res = MantenimientoOperacional.finalizar(
            cod_mantenimiento=8,
            placa="ABC123",
            cedula_usuario="12345678",
            costo_final=180.0,
            detalles=None
        )

    assert res is True
    # 1 update mantenimiento + 1 update det_mantenimiento + 1 update vehiculo = 3
    assert cursor.execute.call_count == 3
    conexion.commit.assert_called_once()
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=3)


def test_cp_mop_28_finalizar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-MOP-28: Manejo de excepción SQL durante la finalización, ejecutando rollback y re-lanzando error."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Error forzado de integridad en finalización")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        with pytest.raises(Exception, match="Error forzado de integridad en finalización"):
            MantenimientoOperacional.finalizar(
                cod_mantenimiento=8,
                placa="ABC123",
                cedula_usuario="12345678",
                costo_final=300.0
            )

    conexion.rollback.assert_called_once()
    mock_bitacora.assert_not_called()

   
# BLOQUE 6: CONSULTAS, REPORTES Y PROPIEDADES DEL MODELO (CP-MOP-29 AL CP-MOP-34)

def test_cp_mop_29_obtener_mantenimientos_con_y_sin_bitacora(conexion_mock):
    """CP-MOP-29: Consulta del listado de mantenimientos activos y finalizados con y sin auditoría en bitácora."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [
        {"cod_mantenimiento": 1, "descripcion_general": "Mant 1", "estado": "Activo"},
        {"cod_mantenimiento": 2, "descripcion_general": "Mant 2", "estado": "Finalizado"}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.mantenimiento_operacional.Bitacora.registrar") as mock_bitacora:

        # 1. Con usuario en sesión (debe registrar en bitácora)
        res_con_usuario = MantenimientoOperacional.obtener_mantenimientos(cedula_usuario="12345678")
        assert len(res_con_usuario) == 2
        mock_bitacora.assert_called_once_with("12345678", cod_accion=2, cod_modulo=3)

        # 2. Sin usuario en sesión (no debe registrar en bitácora)
        mock_bitacora.reset_mock()
        res_sin_usuario = MantenimientoOperacional.obtener_mantenimientos(cedula_usuario=None)
        assert len(res_sin_usuario) == 2
        mock_bitacora.assert_not_called()

        # Verificar cláusula WHERE de la consulta
        sql_ejecutado = cursor.execute.call_args[0][0]
        assert "WHERE m.estado IN ('Activo', 'Finalizado')" in sql_ejecutado


def test_cp_mop_30_obtener_talleres(conexion_mock):
    """CP-MOP-30: Consulta del catálogo de talleres mecánicos habilitados (estado = '1')."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [
        {"cod_taller": 1, "nombre_taller": "Taller Central"},
        {"cod_taller": 2, "nombre_taller": "Taller Express"}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        talleres = MantenimientoOperacional.obtener_talleres()

    assert len(talleres) == 2
    assert talleres[0]["nombre_taller"] == "Taller Central"
    sql = cursor.execute.call_args[0][0]
    assert "WHERE estado = '1'" in sql


def test_cp_mop_31_obtener_usuarios_autorizadores_exito_y_error(conexion_seguridad_mock):
    """CP-MOP-31: Consulta de usuarios autorizadores en seguridad y control de excepción retornando lista vacía."""
    con_sec, cur_sec = conexion_seguridad_mock
    cur_sec.fetchall.return_value = [
        {"cedula_usuario": "12345678", "nombre": "Carlos", "apellido": "Pérez", "nombre_rol": "Administrador"}
    ]

    with patch("models.db.ConexionBD.obtener_conexion_seguridad", return_value=con_sec):
        # 1. Caso exitoso
        usuarios = MantenimientoOperacional.obtener_usuarios_autorizadores()
        assert len(usuarios) == 1
        assert usuarios[0]["nombre_rol"] == "Administrador"

        # 2. Caso con error en BD (debe capturar excepción y retornar lista vacía [])
        cur_sec.execute.side_effect = Exception("Error de red en seguridad")
        usuarios_error = MantenimientoOperacional.obtener_usuarios_autorizadores()
        assert usuarios_error == []


def test_cp_mop_32_obtener_vehiculos_disponibles_y_en_mantenimiento(conexion_mock):
    """CP-MOP-32: Consulta de vehículos disponibles para mantenimiento y vehículos en catálogo."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [{"placa": "ABC123", "estado": "Disponible"}]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        # 1. Vehículos disponibles o en mantenimiento
        v_disp = MantenimientoOperacional.obtener_vehiculos_disponibles()
        assert len(v_disp) == 1
        sql1 = cursor.execute.call_args[0][0]
        assert "WHERE estado IN ('Disponible', 'Mantenimiento')" in sql1

        # 2. Vehículos estrictamente disponibles
        v_estricto = MantenimientoOperacional.obtener_vehiculos()
        assert len(v_estricto) == 1
        sql2 = cursor.execute.call_args[0][0]
        assert "WHERE estado IN ('Disponible')" in sql2


def test_cp_mop_33_obtener_detalle_por_mantenimiento(conexion_mock):
    """CP-MOP-33: Consulta de detalles y repuestos vinculados a un código de mantenimiento."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [
        {"descripcion_detalle": "Bujías", "cantidad": 4},
        {"descripcion_detalle": "Aceite", "cantidad": 1}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        detalles = MantenimientoOperacional.obtener_detalle_por_mantenimiento(cod_mantenimiento=7)

    assert len(detalles) == 2
    assert detalles[0]["descripcion_detalle"] == "Bujías"
    sql = cursor.execute.call_args[0][0]
    assert "FROM mantenimiento_cant" in sql
    assert "WHERE cod_mantenimiento = %s" in sql


def test_cp_mop_34_filtrar_reporte(conexion_mock):
    """CP-MOP-34: Filtrado dinámico de reportes cubriendo rango BETWEEN, fechas individuales y rangos de costo."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [{"cod_mantenimiento": 1, "placa": "ABC123"}]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        # 1. Consulta con todos los filtros activos (rango de fechas con BETWEEN)
        res = MantenimientoOperacional.filtrar_reporte(
            cod_mantenimiento=1,
            placa="ABC123",
            estado="Finalizado",
            cod_taller="2",
            fecha_inicio="2026-01-01",
            fecha_fin="2026-01-31",
            costo_base_desde="100.00",
            costo_base_hasta="500.00",
            costo_final_desde="150.00",
            costo_final_hasta="600.00"
        )
        assert len(res) == 1
        sql1 = cursor.execute.call_args[0][0]
        params1 = cursor.execute.call_args[0][1]
        assert "AND m.cod_mantenimiento = %s" in sql1
        assert "AND dm.placa = %s" in sql1
        assert "AND m.estado = %s" in sql1
        assert "AND dm.cod_taller = %s" in sql1
        assert "AND dm.fecha_solicitud BETWEEN %s AND %s" in sql1
        assert "AND m.costo_base >= %s" in sql1
        assert "AND m.costo_base <= %s" in sql1
        assert "AND m.costo_final >= %s" in sql1
        assert "AND m.costo_final <= %s" in sql1
        assert len(params1) == 10

        # 2. Rama: solo fecha_inicio
        MantenimientoOperacional.filtrar_reporte(fecha_inicio="2026-02-01")
        sql2 = cursor.execute.call_args[0][0]
        assert "AND dm.fecha_solicitud >= %s" in sql2

        # 3. Rama: solo fecha_fin
        MantenimientoOperacional.filtrar_reporte(fecha_fin="2026-02-28")
        sql3 = cursor.execute.call_args[0][0]
        assert "AND dm.fecha_solicitud <= %s" in sql3


def test_mantenimiento_operacional_propiedades_y_setters():
    """Verificación de cobertura integral para constructor, getters y setters de la clase MantenimientoOperacional."""
    m = MantenimientoOperacional(
        cod_mantenimiento=1,
        descripcion_general="Mantenimiento de prueba",
        quien_autoriza="12345678",
        estado="Activo",
        costo_base=100.0,
        costo_final=150.0
    )

    # Validar getters iniciales
    assert m.cod_mantenimiento == 1
    assert m.descripcion_general == "Mantenimiento de prueba"
    assert m.quien_autoriza == "12345678"
    assert m.estado == "Activo"
    assert m.costo_base == 100.0
    assert m.costo_final == 150.0

    # Modificar mediante setters
    m.cod_mantenimiento = 2
    m.descripcion_general = "Mantenimiento modificado"
    m.quien_autoriza = "87654321"
    m.estado = "Finalizado"
    m.costo_base = 200.0
    m.costo_final = 250.0

    # Validar nuevos valores
    assert m.cod_mantenimiento == 2
    assert m.descripcion_general == "Mantenimiento modificado"
    assert m.quien_autoriza == "87654321"
    assert m.estado == "Finalizado"
    assert m.costo_base == 200.0
    assert m.costo_final == 250.0


   
# BLOQUE 7: CONTROLADOR WEB, RUTAS Y PERMISOS (CP-MOP-35 AL CP-MOP-48)


def test_cp_mop_35_ctrl_listar_mantenimiento_get_exitoso(cliente_autenticado):
    """CP-MOP-35: Respuesta HTTP 200 al listar mantenimientos con sesión y permisos autorizados."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos_disponibles", return_value=[]):

        resp = cliente_autenticado.get("/mantenimiento-operacional")

    assert resp.status_code == 200


def test_cp_mop_36_ctrl_crear_mantenimiento_get_renderiza_form(cliente_autenticado):
    """CP-MOP-36: Respuesta HTTP 200 al renderizar el formulario de creación de mantenimiento."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]):

        resp = cliente_autenticado.get("/mantenimiento-operacional/crear")

    assert resp.status_code == 200


def test_cp_mop_37_ctrl_crear_mantenimiento_post_exitoso(cliente_autenticado):
    """CP-MOP-37: Procesamiento exitoso vía POST para crear mantenimiento, notificación a staff y redirección 302."""
    payload = {
        "descripcion_general": "Mantenimiento preventivo general de motor",
        "quien_autoriza": "12345678",
        "tipo": "Preventivo",
        "fecha_solicitud": HOY,
        "fecha_completada": MANANA,
        "placa": "ABC123",
        "cod_taller": "1",
        "costo_base": "120.00",
        "costo_final": "",
        "descripcion_detalle_0": "Filtro de gasolina",
        "cantidad_0": "1"
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.guardar", return_value={"status": True, "mensaje": "Mantenimiento registrado correctamente."}) as mock_guardar, \
         patch("utils.notificaciones_manager.NotificacionManager.crear_multiple") as mock_notif:

        resp = cliente_autenticado.post("/mantenimiento-operacional/crear", data=payload)

    assert resp.status_code == 302
    assert "/mantenimiento-operacional" in resp.headers["Location"]
    mock_guardar.assert_called_once()
    mock_notif.assert_called_once()


def test_cp_mop_38_ctrl_crear_mantenimiento_post_faltan_campos_y_error_guardar(cliente_autenticado):
    """CP-MOP-38: Manejo de errores en POST: campos obligatorios faltantes y error retornado por el modelo."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]):

        # 1. Campos obligatorios vacíos (descripcion_general vacía)
        resp_faltantes = cliente_autenticado.post("/mantenimiento-operacional/crear", data={
            "descripcion_general": "",
            "quien_autoriza": "12345678",
            "tipo": "Preventivo",
            "fecha_solicitud": HOY,
            "placa": "ABC123",
            "cod_taller": "1"
        })
        assert resp_faltantes.status_code == 200

        # 2. Guardar retorna status: False
        with patch("models.mantenimiento_operacional.MantenimientoOperacional.guardar",
                   return_value={"status": False, "mensaje": "La placa seleccionada no existe en vehiculo."}):
            resp_error = cliente_autenticado.post("/mantenimiento-operacional/crear", data={
                "descripcion_general": "Mantenimiento preventivo general de motor",
                "quien_autoriza": "12345678",
                "tipo": "Preventivo",
                "fecha_solicitud": HOY,
                "placa": "ZZZ999",
                "cod_taller": "1"
            })
            assert resp_error.status_code == 200


def test_cp_mop_39_ctrl_editar_mantenimiento_get_existente_e_inexistente(cliente_autenticado):
    """CP-MOP-39: Ruta GET de edición de mantenimiento: código existente retorna 200, inexistente redirige 302."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123", "descripcion_general": "Mant 5"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]):

        # 1. Mantenimiento existente
        resp_ok = cliente_autenticado.get("/mantenimiento-operacional/editar/5")
        assert resp_ok.status_code == 200

        # 2. Mantenimiento inexistente (código 999)
        resp_no = cliente_autenticado.get("/mantenimiento-operacional/editar/999")
        assert resp_no.status_code == 302
        assert "/mantenimiento-operacional" in resp_no.headers["Location"]


def test_cp_mop_40_ctrl_editar_mantenimiento_post_exitoso(cliente_autenticado):
    """CP-MOP-40: Actualización exitosa vía POST, emisión de notificación y redirección a listado."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123", "descripcion_general": "Mant 5"}]
    payload = {
        "descripcion_general": "Mantenimiento mayor actualizado de motor",
        "quien_autoriza": "12345678",
        "tipo": "Correctivo",
        "fecha_solicitud": HOY,
        "fecha_completada": MANANA,
        "cod_taller": "1",
        "costo_base": "200.00",
        "costo_final": "250.00",
        "descripcion_detalle_0": "Empacaduras",
        "cantidad_0": "2"
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.actualizar", return_value={"status": True, "mensaje": "Mantenimiento actualizado correctamente."}) as mock_act, \
         patch("utils.notificaciones_manager.NotificacionManager.crear_multiple") as mock_notif:

        resp = cliente_autenticado.post("/mantenimiento-operacional/editar/5", data=payload)

    assert resp.status_code == 302
    assert "/mantenimiento-operacional" in resp.headers["Location"]
    mock_act.assert_called_once()
    mock_notif.assert_called_once()


def test_cp_mop_41_ctrl_editar_mantenimiento_post_faltan_campos_y_error(cliente_autenticado):
    """CP-MOP-41: Fallos en POST de edición: campos obligatorios incompletos y error en actualización."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123", "descripcion_general": "Mant 5"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_usuarios_autorizadores", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]):

        # 1. Campos obligatorios vacíos
        resp_faltantes = cliente_autenticado.post("/mantenimiento-operacional/editar/5", data={
            "descripcion_general": "",
            "quien_autoriza": "12345678",
            "tipo": "Correctivo",
            "fecha_solicitud": HOY,
            "cod_taller": "1"
        })
        assert resp_faltantes.status_code == 200

        # 2. Error retornado por actualizar
        with patch("models.mantenimiento_operacional.MantenimientoOperacional.actualizar",
                   return_value={"status": False, "mensaje": "Error en actualización"}):
            resp_error = cliente_autenticado.post("/mantenimiento-operacional/editar/5", data={
                "descripcion_general": "Mantenimiento mayor actualizado",
                "quien_autoriza": "12345678",
                "tipo": "Correctivo",
                "fecha_solicitud": HOY,
                "cod_taller": "1"
            })
            assert resp_error.status_code == 200


def test_cp_mop_42_ctrl_inactivar_mantenimiento_post_exitoso_y_error(cliente_autenticado):
    """CP-MOP-42: Ruta POST de inactivación de mantenimiento: caso exitoso con notificación y captura de excepción."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True):
        # 1. Inactivación exitosa
        with patch("models.mantenimiento_operacional.MantenimientoOperacional.inactivar", return_value=True) as mock_inac, \
             patch("utils.notificaciones_manager.NotificacionManager.crear_multiple") as mock_notif:

            resp_ok = cliente_autenticado.post("/mantenimiento-operacional/inactivar/5")
            assert resp_ok.status_code == 302
            assert "/mantenimiento-operacional" in resp_ok.headers["Location"]
            mock_inac.assert_called_once_with(5, "12345678")
            mock_notif.assert_called_once()

        # 2. Excepción durante inactivación
        with patch("models.mantenimiento_operacional.MantenimientoOperacional.inactivar", side_effect=Exception("Fallo en BD")):
            resp_error = cliente_autenticado.post("/mantenimiento-operacional/inactivar/5")
            assert resp_error.status_code == 302
            assert "/mantenimiento-operacional" in resp_error.headers["Location"]


def test_cp_mop_43_ctrl_finalizar_mantenimiento_get_modal_e_inexistente(cliente_autenticado):
    """CP-MOP-43: Ruta GET de finalización: abre modal en index con código existente y redirige ante inexistente."""
    mant_simulado = [{
        "cod_mantenimiento": 5,
        "placa": "ABC123",
        "descripcion_general": "Mantenimiento preventivo de motor",
        "estado": "Activo",
        "costo_base": 150.00,
        "costo_final": None,
        "nombre_taller": "Taller Central",
        "tipo": "Preventivo",
        "fecha_solicitud": HOY,
        "fecha_completada": None
    }]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_talleres", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_vehiculos_disponibles", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]):

        # 1. Mantenimiento existente: renderiza index con mostrar_modal_finalizar=True
        resp_ok = cliente_autenticado.get("/mantenimiento-operacional/finalizar/5/ABC123")
        assert resp_ok.status_code == 200

        # 2. Mantenimiento inexistente: redirige con warning
        resp_no = cliente_autenticado.get("/mantenimiento-operacional/finalizar/999/ABC123")
        assert resp_no.status_code == 302


def test_cp_mop_44_ctrl_finalizar_mantenimiento_post_exitoso(cliente_autenticado):
    """CP-MOP-44: Finalización exitosa vía POST con repuestos adicionales, notificación y redirección 302."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123"}]
    payload = {
        "costo_final": "350.00",
        "descripcion_detalle_0": "Mano de obra final",
        "cantidad_0": "1"
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.finalizar", return_value=True) as mock_fin, \
         patch("utils.notificaciones_manager.NotificacionManager.crear_multiple") as mock_notif:

        resp = cliente_autenticado.post("/mantenimiento-operacional/finalizar/5/ABC123", data=payload)

    assert resp.status_code == 302
    assert "/mantenimiento-operacional" in resp.headers["Location"]
    mock_fin.assert_called_once()
    mock_notif.assert_called_once()


def test_cp_mop_45_ctrl_finalizar_mantenimiento_post_error(cliente_autenticado):
    """CP-MOP-45: Control de excepciones durante el POST de finalización asegurando redirección y mensaje flash."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.finalizar", side_effect=Exception("Fallo al finalizar en BD")):

        resp = cliente_autenticado.post("/mantenimiento-operacional/finalizar/5/ABC123", data={"costo_final": "350.00"})

    assert resp.status_code == 302
    assert "/mantenimiento-operacional" in resp.headers["Location"]


def test_cp_mop_46_ctrl_ver_recibo_existente_e_inexistente(cliente_autenticado):
    """CP-MOP-46: Ruta GET de recibo: código existente retorna 200 con recibo.html e inexistente redirige 302."""
    mant_simulado = [{"cod_mantenimiento": 5, "placa": "ABC123"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_mantenimientos", return_value=mant_simulado), \
         patch("models.mantenimiento_operacional.MantenimientoOperacional.obtener_detalle_por_mantenimiento", return_value=[]):

        # 1. Existente: código 200
        resp_ok = cliente_autenticado.get("/mantenimiento-operacional/ver-recibo/5")
        assert resp_ok.status_code == 200

        # 2. Inexistente: código 302
        resp_no = cliente_autenticado.get("/mantenimiento-operacional/ver-recibo/999")
        assert resp_no.status_code == 302
        assert "/mantenimiento-operacional" in resp_no.headers["Location"]


def test_cp_mop_47_ctrl_acceso_sin_sesion_redirige_a_login(app_client):
    """CP-MOP-47: Protección de seguridad: usuario no autenticado (sin sesión) es redirigido a /login."""
    resp = app_client.get("/mantenimiento-operacional")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_cp_mop_48_ctrl_acceso_sin_permiso_redirige_a_index(cliente_sin_permiso):
    """CP-MOP-48: Control de acceso RBAC: usuario autenticado sin permiso asignado es bloqueado y redirigido."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=False):
        resp = cliente_sin_permiso.get("/mantenimiento-operacional")

    assert resp.status_code == 302
    assert resp.headers["Location"] in ["/", "/index"]