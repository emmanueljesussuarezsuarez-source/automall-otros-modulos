"""
Módulo de Pruebas Unitarias para el Módulo Servicios
Archivo: tests/unit/test_servicios.py
Metodología: Caja blanca, partición de equivalencia, análisis de valores límite y mocks.
Aislamiento: Base de datos MySQL simulada (sin llamadas reales a BD).
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch
import pytest

from app import app
from models.servicios import Servicios
from utils.validaciones_servicios import ValidacionServicios



# CONSTANTES DE FECHA PARA PRUEBAS TEMPORALES

MANANA = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
AYER = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")



# FIXTURES Y CONFIGURACIÓN DE MOCKS

@pytest.fixture
def conexion_mock():
    """
    Simula la conexión a MySQL y el cursor de base de datos.
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
    """Cliente con sesión activa y rol con permisos autorizados."""
    with app_client.session_transaction() as sesion:
        sesion["cedula_usuario"] = "12345678"
        sesion["cod_rol"] = 1  # Superusuario / Administrador con acceso
    return app_client


@pytest.fixture
def cliente_sin_permiso(app_client):
    """Cliente con sesión activa pero sin permisos asignados."""
    with app_client.session_transaction() as sesion:
        sesion["cedula_usuario"] = "87654321"
        sesion["cod_rol"] = 3  # Rol sin permisos
    return app_client



# VERIFICACIÓN DE CONFIGURACIÓN


def test_configuracion_inicial_fixtures(conexion_mock, app_client, cliente_autenticado):
    """Verifica que los imports, helpers de fechas y los fixtures inicien correctamente."""
    conexion, cursor = conexion_mock
    assert conexion is not None
    assert cursor is not None
    assert app_client is not None
    assert cliente_autenticado is not None
    assert HOY is not None
    assert MANANA > HOY
    assert AYER < HOY

    


# BLOQUE 2: PRUEBAS DE VALIDACIONES (CP-SER-01 AL CP-SER-11)


def test_cp_ser_01_nombre_valido():
    """CP-SER-01: Validación exitosa de nombre con letras, acentos y espacios."""
    nombres_validos = [
        "Alineación y Balanceo",
        "Cambio de Aceite",
        "Revisión Eléctrica General",
        "Mantenimiento Mayor"
    ]
    for nombre in nombres_validos:
        resultado = ValidacionServicios.validar_nombre_servicio(nombre)
        assert resultado is None, f"Se esperaba None para '{nombre}' pero retornó '{resultado}'"


@pytest.mark.parametrize("nombre_invalido", ["", None, "   "])
def test_cp_ser_02_nombre_vacio_o_espacios(nombre_invalido):
    """CP-SER-02: Rechazo de nombre de servicio vacío, nulo o solo espacios."""
    resultado = ValidacionServicios.validar_nombre_servicio(nombre_invalido)
    assert resultado == "El nombre del servicio es obligatorio."


@pytest.mark.parametrize("nombre_corto", ["A", "AB", "  X  "])
def test_cp_ser_03_nombre_menor_tres_caracteres(nombre_corto):
    """CP-SER-03: Rechazo de nombre por valor límite inferior (< 3 caracteres)."""
    resultado = ValidacionServicios.validar_nombre_servicio(nombre_corto)
    assert resultado == "El nombre del servicio debe tener al menos 3 caracteres."


def test_cp_ser_04_nombre_limite_100_y_excede_101():
    """CP-SER-04: Límite superior exacto (100) y rechazo por exceder límite (101 caracteres)."""
    assert ValidacionServicios.validar_nombre_servicio("A" * 100) is None
    assert ValidacionServicios.validar_nombre_servicio("A" * 101) == (
        "El nombre del servicio no puede superar 100 caracteres."
    )


@pytest.mark.parametrize("nombre_no_alfabetico", [
    "Lavado 1",
    "Mantenimiento #2",
    "Servicio-A",
    "Taller@Express",
    "Cambio 100%",
    "Frenos_Delanteros"
])
def test_cp_ser_05_nombre_caracteres_no_alfabeticos(nombre_no_alfabetico):
    """CP-SER-05: Rechazo de nombre con números, guiones o caracteres especiales no alfabéticos."""
    resultado = ValidacionServicios.validar_nombre_servicio(nombre_no_alfabetico)
    assert resultado == "El nombre del servicio solo puede contener letras y espacios."


def test_cp_ser_06_costo_base_valido_e_invalido():
    """CP-SER-06: Validación de costo base (opcional, decimal válido, rechazo de texto y negativo)."""
    # Casos válidos (es opcional si está vacío o nulo)
    for valido in [None, "", "   ", "50", "50.00", 0, 100.5]:
        assert ValidacionServicios.validar_costo_base(valido) is None

    # Caso no numérico
    assert ValidacionServicios.validar_costo_base("abc") == "El costo base debe ser un número válido."

    # Caso negativo
    for negativo in ["-10", -0.01, "-0.01"]:
        assert ValidacionServicios.validar_costo_base(negativo) == "El costo base no puede ser negativo."


def test_cp_ser_07_costo_final_opcional_vs_obligatorio():
    """CP-SER-07: Validación de costo final (opcional al crear, obligatorio al finalizar)."""
    # Válidos
    assert ValidacionServicios.validar_costo_final("120.50", obligatorio=False) is None
    assert ValidacionServicios.validar_costo_final("120.50", obligatorio=True) is None

    # Vacío opcional (al registrar)
    assert ValidacionServicios.validar_costo_final("", obligatorio=False) is None
    assert ValidacionServicios.validar_costo_final(None, obligatorio=False) is None

    # Vacío obligatorio (al finalizar servicio)
    assert ValidacionServicios.validar_costo_final("", obligatorio=True) == (
        "Debe registrar el costo final antes de finalizar el servicio."
    )
    assert ValidacionServicios.validar_costo_final(None, obligatorio=True) == (
        "Debe registrar el costo final antes de finalizar el servicio."
    )

    # Inválidos: no numérico y negativo
    assert ValidacionServicios.validar_costo_final("xyz") == "El costo final debe ser un número válido."
    assert ValidacionServicios.validar_costo_final("-5") == "El costo final no puede ser negativo."


def test_cp_ser_08_descripcion_especifica_valida_e_invalida():
    """CP-SER-08: Validación de descripción específica (obligatoria y mínimo 10 caracteres)."""
    # Válida
    assert ValidacionServicios.validar_descripcion_especifica(
        "Cambio de aceite sintético y filtro de aire"
    ) is None

    # Vacía o espacios
    for vacia in ["", None, "   "]:
        assert ValidacionServicios.validar_descripcion_especifica(vacia) == (
            "La descripción específica es obligatoria."
        )

    # Menor a 10 caracteres
    for corta in ["Corta", "123456789", "  Av 123  "]:
        assert ValidacionServicios.validar_descripcion_especifica(corta) == (
            "La descripción específica debe tener al menos 10 caracteres."
        )


def test_cp_ser_09_fecha_realizacion_valida_e_invalida():
    """CP-SER-09: Validación de fecha (obligatoria, formato YYYY-MM-DD y no anterior a hoy)."""
    # Fechas válidas: hoy o futuro
    assert ValidacionServicios.validar_fecha_realizacion(HOY) is None
    assert ValidacionServicios.validar_fecha_realizacion(MANANA) is None

    # Vacía o nula
    for vacia in ["", None, "   "]:
        assert ValidacionServicios.validar_fecha_realizacion(vacia) == (
            "La fecha de realización es obligatoria."
        )

    # Formato inválido
    for formato_malo in ["31/12/2026", "2026-13-40", "texto-fecha"]:
        assert ValidacionServicios.validar_fecha_realizacion(formato_malo) == (
            "El formato de fecha de realización no es válido. Use YYYY-MM-DD."
        )

    # Fecha anterior a hoy (rechazo temporal)
    assert ValidacionServicios.validar_fecha_realizacion(AYER) == (
        "La fecha de realización no puede ser anterior a hoy."
    )


def test_cp_ser_10_placa_valida_e_invalida():
    """CP-SER-10: Validación de placa (longitud entre 5 y 7 caracteres)."""
    # Placas válidas (5, 6 y 7 caracteres)
    for valida in ["AB123", "ABC123", "ABC1234", "  AB123  "]:
        assert ValidacionServicios.validar_placa(valida) is None

    # Placa vacía
    for vacia in ["", None, "   "]:
        assert ValidacionServicios.validar_placa(vacia) == "Debe seleccionar una placa."

    # Longitud menor a 5 o mayor a 7 caracteres
    for fuera_rango in ["A", "AB", "AB12", "ABC12345", "ABCDEFGHI"]:
        assert ValidacionServicios.validar_placa(fuera_rango) == (
            "La placa debe tener entre 5 y 7 caracteres."
        )


def test_cp_ser_11_validar_servicio_integral():
    """CP-SER-11: Validación integral de servicio con consolidación de errores."""
    # Caso exitoso completo
    valido, errores = ValidacionServicios.validar_servicio(
        nombre_servicio="Alineación General",
        costo_base="45.00",
        costo_final="50.00",
        descripcion_especifica="Alineación y balanceo computarizado de 4 ruedas",
        fecha_realizacion=HOY,
        placa="ABC123",
        costo_final_obligatorio=False
    )
    assert valido is True
    assert errores == {}

    # Caso con costo final obligatorio faltante
    valido_obl, errores_obl = ValidacionServicios.validar_servicio(
        nombre_servicio="Alineación General",
        costo_base="45.00",
        costo_final="",
        descripcion_especifica="Alineación y balanceo computarizado de 4 ruedas",
        fecha_realizacion=HOY,
        placa="ABC123",
        costo_final_obligatorio=True
    )
    assert valido_obl is False
    assert "costo_final" in errores_obl

    # Caso con múltiples campos inválidos
    valido_err, errores_err = ValidacionServicios.validar_servicio(
        nombre_servicio="",
        costo_base="-10",
        costo_final="-5",
        descripcion_especifica="Corta",
        fecha_realizacion=AYER,
        placa="A"
    )
    assert valido_err is False
    assert "nombre_servicio" in errores_err
    assert "costo_base" in errores_err
    assert "costo_final" in errores_err
    assert "descripcion_especifica" in errores_err
    assert "fecha_realizacion" in errores_err
    assert "placa" in errores_err

    


# BLOQUE 3: PRUEBAS DE GUARDAR (CP-SER-12 AL CP-SER-16)


def test_cp_ser_12_guardar_servicio_exitoso_con_bitacora(conexion_mock):
    """CP-SER-12: Registro transaccional exitoso de servicio, detalle, estado de vehículo y bitácora."""
    conexion, cursor = conexion_mock
    cursor.lastrowid = 10

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.guardar(
            nombre_servicio="Alineacion y Balanceo",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Alineación general computarizada de 4 ruedas",
            fecha_realizacion=HOY,
            placa="ABC123",
            cedula_usuario="12345678"
        )

    # Verificación de respuesta
    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio registrado correctamente."

    # Verificación de consultas transaccionales ejecutadas
    assert cursor.execute.call_count == 3
    sql_servicios = cursor.execute.call_args_list[0][0][0]
    param_servicios = cursor.execute.call_args_list[0][0][1]
    assert "INSERT INTO servicios" in sql_servicios
    assert param_servicios == ("Alineacion y Balanceo", "50.00", "Activo")

    sql_det = cursor.execute.call_args_list[1][0][0]
    param_det = cursor.execute.call_args_list[1][0][1]
    assert "INSERT INTO det_servicios" in sql_det
    assert param_det == (None, "Alineación general computarizada de 4 ruedas", HOY, "ABC123", 10)

    sql_vehiculo = cursor.execute.call_args_list[2][0][0]
    param_vehiculo = cursor.execute.call_args_list[2][0][1]
    assert "UPDATE vehiculo" in sql_vehiculo
    assert "SET estado = 'Servicio'" in sql_vehiculo
    assert param_vehiculo == ("ABC123",)

    # Verificación transaccional y bitácora (cod_accion=1, cod_modulo=9)
    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=1, cod_modulo=9)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_ser_13_guardar_servicio_sin_usuario_omite_bitacora(conexion_mock):
    """CP-SER-13: Registro de servicio sin usuario realiza commit y omite bitácora."""
    conexion, cursor = conexion_mock
    cursor.lastrowid = 11

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.guardar(
            nombre_servicio="Cambio de Filtros",
            costo_base="25.00",
            costo_final="30.00",
            descripcion_especifica="Reemplazo de filtro de combustible y aire",
            fecha_realizacion=HOY,
            placa="XYZ789",
            cedula_usuario=None
        )

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio registrado correctamente."
    conexion.commit.assert_called_once()
    bitacora_mock.assert_not_called()


def test_cp_ser_14_guardar_rechaza_por_placa_inexistente(conexion_mock):
    """CP-SER-14: Rechazo al guardar si la placa tiene formato válido pero no existe en tabla vehiculo."""
    conexion, cursor = conexion_mock
    # Usamos una placa de 6 caracteres ("ZZZ999") para que supere la validación de longitud (5 a 7)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=False):
        resultado = Servicios.guardar(
            nombre_servicio="Mantenimiento General",
            costo_base="100.00",
            costo_final=None,
            descripcion_especifica="Mantenimiento preventivo general",
            fecha_realizacion=HOY,
            placa="ZZZ999"
        )
    assert resultado["status"] is False
    assert resultado["mensaje"] == "La placa seleccionada no existe en la tabla vehiculo."
    cursor.execute.assert_not_called()
    conexion.commit.assert_not_called()


def test_cp_ser_15_guardar_rechaza_por_validacion_sin_abrir_bd(conexion_mock):
    """CP-SER-15: Rechazo al guardar por error de validación sin abrir conexión a BD."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Servicios.guardar(
            nombre_servicio="",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Descripción de prueba",
            fecha_realizacion=HOY,
            placa="ABC123"
        )

    assert resultado["status"] is False
    assert resultado["mensaje"] == "El nombre del servicio es obligatorio."
    cursor.execute.assert_not_called()
    conexion.commit.assert_not_called()


def test_cp_ser_16_guardar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-SER-16: Manejo de error de base de datos y ejecución de rollback() al guardar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo de comunicación en servidor MySQL (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True):

        resultado = Servicios.guardar(
            nombre_servicio="Alineacion",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Alineación general de ruedas",
            fecha_realizacion=HOY,
            placa="ABC123",
            cedula_usuario="12345678"
        )

    assert resultado["status"] is False
    assert "Error al guardar el servicio" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()



    


# BLOQUE 4: PRUEBAS DE ACTUALIZAR (CP-SER-17 AL CP-SER-20)


def test_cp_ser_17_actualizar_servicio_misma_placa_con_bitacora(conexion_mock):
    """CP-SER-17: Actualización exitosa manteniendo la misma placa, commit y bitácora."""
    conexion, cursor = conexion_mock
    # Simulamos que la placa anterior es la misma ("ABC123")
    cursor.fetchone.return_value = ("ABC123",)

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.actualizar(
            cod_servicios=5,
            nombre_servicio="Alineacion Actualizada",
            costo_base="60.00",
            costo_final="65.00",
            descripcion_especifica="Alineación y balanceo con rotación de cauchos",
            fecha_realizacion=HOY,
            placa="ABC123",
            cedula_usuario="12345678"
        )

    # Verificación de respuesta
    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio actualizado correctamente."

    # Comprobamos las sentencias de actualización ejecutadas
    assert cursor.execute.call_count == 3
    sql_servicios = cursor.execute.call_args_list[1][0][0]
    param_servicios = cursor.execute.call_args_list[1][0][1]
    assert "UPDATE servicios" in sql_servicios
    assert param_servicios == ("Alineacion Actualizada", "60.00", 5)

    sql_det = cursor.execute.call_args_list[2][0][0]
    param_det = cursor.execute.call_args_list[2][0][1]
    assert "UPDATE det_servicios" in sql_det
    assert param_det == ("65.00", "Alineación y balanceo con rotación de cauchos", HOY, "ABC123", 5)

    # Verificación transaccional y bitácora (cod_accion=3, cod_modulo=9)
    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=3, cod_modulo=9)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_ser_18_actualizar_servicio_cambio_de_placa(conexion_mock):
    """CP-SER-18: Actualización con cambio de placa (libera vehículo anterior y asigna nuevo)."""
    conexion, cursor = conexion_mock
    # Placa anterior era "VIEJA1" y ahora se cambia a "NUEVA2"
    cursor.fetchone.return_value = ("VIEJA1",)

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.actualizar(
            cod_servicios=5,
            nombre_servicio="Alineacion Nueva",
            costo_base="55.00",
            costo_final="60.00",
            descripcion_especifica="Alineación para nuevo vehículo asignado",
            fecha_realizacion=HOY,
            placa="NUEVA2",
            cedula_usuario="12345678"
        )

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio actualizado correctamente."

    # Se ejecutan 5 sentencias: SELECT placa anterior + UPDATE servicios + UPDATE det + 2 UPDATE vehiculo
    assert cursor.execute.call_count == 5
    sql_liberar = cursor.execute.call_args_list[3][0][0]
    param_liberar = cursor.execute.call_args_list[3][0][1]
    assert "UPDATE vehiculo SET estado = 'Disponible' WHERE placa = %s" in sql_liberar
    assert param_liberar == ("VIEJA1",)

    sql_asignar = cursor.execute.call_args_list[4][0][0]
    param_asignar = cursor.execute.call_args_list[4][0][1]
    assert "UPDATE vehiculo SET estado = 'Servicio' WHERE placa = %s" in sql_asignar
    assert param_asignar == ("NUEVA2",)

    conexion.commit.assert_called_once()


def test_cp_ser_19_actualizar_rechaza_datos_invalidos_y_placa_inexistente(conexion_mock):
    """CP-SER-19: Rechazo de actualización por datos inválidos o placa no encontrada sin ejecutar SQL."""
    conexion, cursor = conexion_mock

    # 1. Error de validación: Nombre de servicio vacío
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        res_val = Servicios.actualizar(
            cod_servicios=5,
            nombre_servicio="",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Descripción de prueba",
            fecha_realizacion=HOY,
            placa="ABC123"
        )
        assert res_val["status"] is False
        assert res_val["mensaje"] == "El nombre del servicio es obligatorio."

    # 2. Placa de formato válido pero inexistente en base de datos
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=False):
        res_placa = Servicios.actualizar(
            cod_servicios=5,
            nombre_servicio="Mantenimiento",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Mantenimiento preventivo",
            fecha_realizacion=HOY,
            placa="ZZZ999"
        )
        assert res_placa["status"] is False
        assert res_placa["mensaje"] == "La placa seleccionada no existe en la tabla vehiculo."

    cursor.execute.assert_not_called()
    conexion.commit.assert_not_called()


def test_cp_ser_20_actualizar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-SER-20: Manejo de error de base de datos y ejecución de rollback() al actualizar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo en ejecución de UPDATE MySQL (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Servicios.existe_vehiculo", return_value=True):

        resultado = Servicios.actualizar(
            cod_servicios=5,
            nombre_servicio="Alineacion",
            costo_base="50.00",
            costo_final=None,
            descripcion_especifica="Alineación general de ruedas",
            fecha_realizacion=HOY,
            placa="ABC123",
            cedula_usuario="12345678"
        )

    assert resultado["status"] is False
    assert "Error al actualizar el servicio" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


    


# BLOQUE 5: PRUEBAS DE INACTIVAR Y FINALIZAR (CP-SER-21 AL CP-SER-25)


def test_cp_ser_21_inactivar_servicio_exitoso_con_bitacora(conexion_mock):
    """CP-SER-21: Inactivación lógica exitosa de servicio (estado = 'Inactivo'), commit y bitácora."""
    conexion, cursor = conexion_mock

    # Caso 1: Inactivación con cédula de usuario
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.inactivar(cod_servicios=8, cedula_usuario="12345678")

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio inactivado correctamente."

    assert cursor.execute.called
    sql_ejecutado = cursor.execute.call_args[0][0]
    parametros = cursor.execute.call_args[0][1]
    assert "UPDATE servicios" in sql_ejecutado
    assert "SET estado = 'Inactivo'" in sql_ejecutado
    assert "WHERE cod_servicios = %s" in sql_ejecutado
    assert parametros == (8,)

    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=3, cod_modulo=9)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    # Caso 2: Inactivación sin usuario (omite bitácora)
    conexion.reset_mock()
    cursor.reset_mock()
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Bitacora.registrar") as bitacora_vacio:

        resultado_sin_usuario = Servicios.inactivar(cod_servicios=8, cedula_usuario=None)

    assert resultado_sin_usuario["status"] is True
    conexion.commit.assert_called_once()
    bitacora_vacio.assert_not_called()


def test_cp_ser_22_inactivar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-SER-22: Manejo de error de base de datos y ejecución de rollback() al inactivar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo en UPDATE inactivar MySQL (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Servicios.inactivar(cod_servicios=8, cedula_usuario="12345678")

    assert resultado["status"] is False
    assert "Error al inactivar el servicio" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_ser_23_finalizar_servicio_exitoso_con_costo_final_y_bitacora(conexion_mock):
    """CP-SER-23: Finalización exitosa de servicio, reactiva vehículo a 'Disponible' y registra bitácora."""
    conexion, cursor = conexion_mock
    # Simulamos que existe el costo final en det_servicios
    cursor.fetchone.return_value = (150.0,)

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.finalizar(
            cod_servicios=8,
            placa="ABC123",
            cedula_usuario="12345678",
            costo_final="150.00"
        )

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Servicio finalizado y vehículo reactivado."

    # Se ejecutan 4 sentencias: UPDATE det_servicios + SELECT costo_final + UPDATE servicios + UPDATE vehiculo
    assert cursor.execute.call_count == 4
    sql_serv = cursor.execute.call_args_list[2][0][0]
    param_serv = cursor.execute.call_args_list[2][0][1]
    assert "UPDATE servicios" in sql_serv
    assert "SET estado = 'Finalizado'" in sql_serv
    assert param_serv == (8,)

    sql_veh = cursor.execute.call_args_list[3][0][0]
    param_veh = cursor.execute.call_args_list[3][0][1]
    assert "UPDATE vehiculo" in sql_veh
    assert "SET estado = 'Disponible'" in sql_veh
    assert param_veh == ("ABC123",)

    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=3, cod_modulo=9)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_ser_24_finalizar_rechaza_si_no_hay_costo_final(conexion_mock):
    """CP-SER-24: Rechazo al finalizar servicio si no existe costo final registrado."""
    conexion, cursor = conexion_mock

    # Caso 1: La fila no existe (None)
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado_none = Servicios.finalizar(cod_servicios=8, placa="ABC123", costo_final=None)

    assert resultado_none["status"] is False
    assert resultado_none["mensaje"] == "Debe registrar el costo final antes de finalizar el servicio."
    conexion.commit.assert_not_called()

    # Caso 2: La fila existe pero el costo es NULL en BD y no se pasó parámetro
    cursor.reset_mock()
    conexion.reset_mock()
    cursor.fetchone.return_value = (None,)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado_null = Servicios.finalizar(cod_servicios=8, placa="ABC123", costo_final="")

    assert resultado_null["status"] is False
    assert resultado_null["mensaje"] == "Debe registrar el costo final antes de finalizar el servicio."
    conexion.commit.assert_not_called()


def test_cp_ser_25_finalizar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-SER-25: Manejo de error de base de datos y ejecución de rollback() al finalizar servicio."""
    conexion, cursor = conexion_mock
    cursor.fetchone.return_value = (150.0,)
    # Simulamos fallo en la tercera sentencia (al intentar actualizar a 'Finalizado')
    cursor.execute.side_effect = [None, None, Exception("Error en sentencia UPDATE finalizado (errno=2013)")]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Servicios.finalizar(
            cod_servicios=8,
            placa="ABC123",
            cedula_usuario="12345678",
            costo_final="150.00"
        )

    assert resultado["status"] is False
    assert "Error al finalizar el servicio" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


    


# BLOQUE 6: PRUEBAS DE CONSULTAS (CP-SER-26 AL CP-SER-31)


def test_cp_ser_26_obtener_servicios_con_y_sin_bitacora(conexion_mock):
    """CP-SER-26: Consulta relacional de servicios activos/finalizados y bitácora condicional."""
    conexion, cursor = conexion_mock
    servicios_mock = [
        {"cod_servicios": 1, "nombre_servicio": "Lavado General", "estado": "Activo"}
    ]
    cursor.fetchall.return_value = servicios_mock

    # Caso 1: Con usuario (registra cod_accion=2 en bitácora)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Bitacora.registrar") as bitacora_mock:

        resultado = Servicios.obtener_servicios(cedula_usuario="12345678")

    assert resultado == servicios_mock
    conexion.cursor.assert_called_with(dictionary=True)
    sql_ejecutado = cursor.execute.call_args[0][0]
    assert "LEFT JOIN det_servicios" in sql_ejecutado
    assert "LEFT JOIN vehiculo" in sql_ejecutado
    assert "WHERE s.estado IN ('Activo', 'Finalizado')" in sql_ejecutado
    assert "ORDER BY s.cod_servicios DESC" in sql_ejecutado

    bitacora_mock.assert_called_once_with("12345678", cod_accion=2, cod_modulo=9)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    # Caso 2: Sin usuario (omite bitácora)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.servicios.Bitacora.registrar") as bitacora_vacio:

        resultado_sin_usuario = Servicios.obtener_servicios(cedula_usuario=None)

    assert resultado_sin_usuario == servicios_mock
    bitacora_vacio.assert_not_called()


def test_cp_ser_27_obtener_vehiculos_disponibles_y_catalogo(conexion_mock):
    """CP-SER-27: Consulta de vehículos disponibles ('Disponible') y listado de todas las placas."""
    conexion, cursor = conexion_mock
    # 1. Vehículos disponibles
    cursor.fetchall.return_value = [{"placa": "ABC123", "estado": "Disponible"}]
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        disponibles = Servicios.obtener_vehiculos_disponibles()
    assert disponibles == [{"placa": "ABC123", "estado": "Disponible"}]
    sql_disp = cursor.execute.call_args[0][0]
    assert "WHERE estado IN ('Disponible')" in sql_disp
    assert "ORDER BY placa ASC" in sql_disp
    # 2. Catálogo general de vehículos
    cursor.fetchall.return_value = [{"placa": "ABC123"}, {"placa": "XYZ789"}]
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        todos_vehiculos = Servicios.obtener_vehiculos()
    assert len(todos_vehiculos) == 2
    sql_todos = cursor.execute.call_args[0][0]
    assert "FROM vehiculo" in sql_todos
    assert "ORDER BY placa ASC" in sql_todos


def test_cp_ser_28_existe_vehiculo(conexion_mock):
    """CP-SER-28: Verificación booleana de existencia física de una placa en BD."""
    conexion, cursor = conexion_mock

    # Placa existente
    cursor.fetchone.return_value = {"placa": "ABC123"}
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        assert Servicios.existe_vehiculo("ABC123") is True

    sql = cursor.execute.call_args[0][0]
    param = cursor.execute.call_args[0][1]
    assert "WHERE placa = %s" in sql
    assert param == ("ABC123",)

    # Placa inexistente
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        assert Servicios.existe_vehiculo("NOEXISTE") is False

def test_cp_ser_29_obtener_costo_final(conexion_mock):
    """CP-SER-29: Consulta individual de costo_final desde la tabla det_servicios."""
    conexion, cursor = conexion_mock
    # Caso existente
    cursor.fetchone.return_value = {"costo_final": 85.50}
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        assert Servicios.obtener_costo_final(5) == 85.50
    sql = cursor.execute.call_args[0][0]
    param = cursor.execute.call_args[0][1]
    assert "FROM det_servicios" in sql
    assert "WHERE cod_servicios = %s" in sql
    assert "LIMIT 1" in sql
    assert param == (5,)
    # Caso no encontrado
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        assert Servicios.obtener_costo_final(999) is None


def test_cp_ser_30_obtener_servicio_por_codigo(conexion_mock):
    """CP-SER-30: Consulta detallada de servicio por código primario."""
    conexion, cursor = conexion_mock
    servicio_esperado = {
        "cod_servicios": 1,
        "nombre_servicio": "Lavado General",
        "placa": "ABC123",
        "estado": "Activo"
    }
    cursor.fetchone.return_value = servicio_esperado

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Servicios.obtener_servicio_por_codigo(1)

    assert resultado == servicio_esperado
    sql = cursor.execute.call_args[0][0]
    param = cursor.execute.call_args[0][1]
    assert "WHERE s.cod_servicios = %s" in sql
    assert param == (1,)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_ser_31_filtrar_reporte(conexion_mock):
    """CP-SER-31: Filtrado parametrizado para reportes de servicios con múltiples criterios."""
    conexion, cursor = conexion_mock
    cursor.fetchall.return_value = [
        {"cod_servicios": 1, "nombre_servicio": "Alineacion", "estado": "Finalizado", "placa": "ABC123"}
    ]

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Servicios.filtrar_reporte(
            cod_servicio="1",
            nombre_servicio="Alineacion",
            estado="Finalizado",
            placa="ABC123"
        )

    assert len(resultado) == 1
    sql = cursor.execute.call_args[0][0]
    params = cursor.execute.call_args[0][1]

    assert "WHERE (%s = '' OR s.cod_servicios = %s)" in sql
    assert "(%s = '' OR s.nombre_servicio LIKE %s)" in sql
    assert params == (
        "1", "1",
        "Alineacion", "%Alineacion%",
        "Finalizado", "Finalizado",
        "ABC123", "ABC123"
    )
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_servicios_modelo_propiedades_y_setters():
    """Verifica instanciación de la entidad Servicios y métodos get/set."""
    servicio = Servicios(cod_servicios=1, nombre_servicio="Mantenimiento", estado="Activo")
    assert servicio.cod_servicios == 1
    assert servicio.nombre_servicio == "Mantenimiento"
    assert servicio.estado == "Activo"

    servicio.cod_servicios = 2
    servicio.nombre_servicio = "Mantenimiento Mayor"
    servicio.estado = "Finalizado"

    assert servicio.cod_servicios == 2
    assert servicio.nombre_servicio == "Mantenimiento Mayor"
    assert servicio.estado == "Finalizado"


    


# BLOQUE 7: PRUEBAS DE CONTROLADOR / RUTAS Y PERMISOS (CP-SER-32 AL CP-SER-43)


def test_cp_ser_32_ctrl_listar_servicios_get_exitoso(cliente_autenticado):
    """CP-SER-32: Controlador GET /servicios exitoso renderiza servicios/index.html con lista y vehículos."""
    servicios_mock = [{"cod_servicios": 1, "nombre_servicio": "Lavado", "estado": "Activo"}]
    vehiculos_mock = [{"placa": "ABC123"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicios", return_value=servicios_mock) as mock_obt, \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos", return_value=vehiculos_mock), \
         patch("controllers.servicios_controller.render_template", return_value="<html>Listado OK</html>") as mock_render:

        respuesta = cliente_autenticado.get("/servicios")

    assert respuesta.status_code == 200
    mock_obt.assert_called_once_with("12345678")
    mock_render.assert_called_once_with("servicios/index.html", servicios=servicios_mock, vehiculos=vehiculos_mock)


def test_cp_ser_33_ctrl_crear_servicio_get_renderiza_form(cliente_autenticado):
    """CP-SER-33: Controlador GET /servicios/nuevo renderiza formulario con vehículos disponibles."""
    disp_mock = [{"placa": "ABC123", "estado": "Disponible"}]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos_disponibles", return_value=disp_mock), \
         patch("controllers.servicios_controller.render_template", return_value="<html>Formulario OK</html>") as mock_render:

        respuesta = cliente_autenticado.get("/servicios/nuevo")

    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("servicios/form.html", vehiculos=disp_mock, servicio=None)


def test_cp_ser_34_ctrl_crear_servicio_post_exitoso(cliente_autenticado):
    """CP-SER-34: Controlador POST /servicios/nuevo exitoso notifica a staff y redirige."""
    datos_form = {
        "nombre_servicio": "Alineacion",
        "costo_base": "50.00",
        "costo_final": "",
        "descripcion_especifica": "Alineación general de 4 ruedas",
        "fecha_realizacion": HOY,
        "placa": "ABC123"
    }
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos_disponibles", return_value=[]), \
         patch("controllers.servicios_controller.Servicios.guardar", return_value={"status": True, "mensaje": "Servicio registrado correctamente."}) as mock_guardar, \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif:
        respuesta = cliente_autenticado.post("/servicios/nuevo", data=datos_form)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/servicios")
    mock_guardar.assert_called_once_with(
        "Alineacion",
        "50.00",
        None,
        "Alineación general de 4 ruedas",
        HOY,
        "ABC123",
        "12345678"
    )
    mock_notif.assert_called_once()
    kwargs_notif = mock_notif.call_args[1]["notificacion_staff"]
    assert kwargs_notif["titulo"] == "Nuevo Servicio Registrado"
    assert kwargs_notif["roles"] == [1, 2]
    assert kwargs_notif["modulo"] == "servicios"


def test_cp_ser_35_ctrl_crear_servicio_post_error_renderiza_form(cliente_autenticado):
    """CP-SER-35: Controlador POST /servicios/nuevo con error en modelo renderiza form con flash danger."""
    datos_form = {"nombre_servicio": "", "placa": "ABC123"}

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos_disponibles", return_value=[]), \
         patch("controllers.servicios_controller.Servicios.guardar", return_value={"status": False, "mensaje": "El nombre del servicio es obligatorio."}), \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif, \
         patch("controllers.servicios_controller.render_template", return_value="<html>Form Re-render</html>") as mock_render:

        respuesta = cliente_autenticado.post("/servicios/nuevo", data=datos_form)

    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("servicios/form.html", vehiculos=[], servicio=None)
    mock_notif.assert_not_called()


def test_cp_ser_36_ctrl_editar_servicio_get_existente_e_inexistente(cliente_autenticado):
    """CP-SER-36: Controlador GET /servicios/editar/<id> existente e inexistente."""
    # 1. Existente con costos vacíos (los normaliza a 0)
    servicio_mock = {
        "cod_servicios": 1,
        "nombre_servicio": "Lavado",
        "costo_base": None,
        "costo_final": "",
        "placa": "ABC123"
    }
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=servicio_mock), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos", return_value=[]), \
         patch("controllers.servicios_controller.render_template", return_value="<html>Edicion</html>") as mock_render:
        resp_ok = cliente_autenticado.get("/servicios/editar/1")
    assert resp_ok.status_code == 200
    assert servicio_mock["costo_base"] == 0
    assert servicio_mock["costo_final"] == 0
    mock_render.assert_called_once()
    # 2. Inexistente redirige a /servicios
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=None), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos", return_value=[]):
        resp_no = cliente_autenticado.get("/servicios/editar/999")
    assert resp_no.status_code == 302
    assert resp_no.headers["Location"].endswith("/servicios")

def test_cp_ser_37_ctrl_editar_servicio_post_exitoso(cliente_autenticado):
    """CP-SER-37: Controlador POST /servicios/editar/<id> exitoso actualiza, notifica y redirige."""
    servicio_actual = {"cod_servicios": 1, "placa": "ABC123"}
    datos_form = {
        "nombre_servicio": "Lavado Integral",
        "costo_base": "30.00",
        "costo_final": "35.00",
        "descripcion_especifica": "Lavado profundo de chasis y motor",
        "fecha_realizacion": HOY
    }
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=servicio_actual), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos", return_value=[]), \
         patch("controllers.servicios_controller.Servicios.actualizar", return_value={"status": True, "mensaje": "Servicio actualizado correctamente."}) as mock_act, \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif:
        respuesta = cliente_autenticado.post("/servicios/editar/1", data=datos_form)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/servicios")
    mock_act.assert_called_once_with(
        1,
        "Lavado Integral",
        "30.00",
        "35.00",
        "Lavado profundo de chasis y motor",
        HOY,
        "ABC123",
        "12345678"
    )
    mock_notif.assert_called_once()
    kwargs_notif = mock_notif.call_args[1]["notificacion_staff"]
    assert kwargs_notif["titulo"] == "Servicio Actualizado"
    assert kwargs_notif["roles"] == [1, 2]


def test_cp_ser_38_ctrl_editar_servicio_post_error_renderiza_form(cliente_autenticado):
    """CP-SER-38: Controlador POST /servicios/editar/<id> con fallo en modelo renderiza form sin notificar."""
    servicio_actual = {"cod_servicios": 1, "placa": "ABC123"}
    datos_form = {
        "nombre_servicio": "Lavado",
        "costo_base": "30.00",
        "costo_final": "",
        "descripcion_especifica": "Corta",
        "fecha_realizacion": HOY
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=servicio_actual), \
         patch("controllers.servicios_controller.Servicios.obtener_vehiculos", return_value=[]), \
         patch("controllers.servicios_controller.Servicios.actualizar", return_value={"status": False, "mensaje": "La descripción específica debe tener al menos 10 caracteres."}), \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif, \
         patch("controllers.servicios_controller.render_template", return_value="<html>Re-render Form</html>") as mock_render:

        respuesta = cliente_autenticado.post("/servicios/editar/1", data=datos_form)

    assert respuesta.status_code == 200
    mock_render.assert_called_once()
    mock_notif.assert_not_called()


def test_cp_ser_39_ctrl_inactivar_servicio_post_exitoso_y_error(cliente_autenticado):
    """CP-SER-39: Controlador POST /servicios/inactivar/<id> exitoso y con fallo."""
    # 1. Éxito
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.inactivar", return_value={"status": True, "mensaje": "Inactivado"}) as mock_inac, \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif:

        resp_ok = cliente_autenticado.post("/servicios/inactivar/1")

    assert resp_ok.status_code == 302
    assert resp_ok.headers["Location"].endswith("/servicios")
    mock_inac.assert_called_once_with(1, "12345678")
    mock_notif.assert_called_once()

    # 2. Error
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.inactivar", return_value={"status": False, "mensaje": "Error"}), \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif_err:

        resp_err = cliente_autenticado.post("/servicios/inactivar/1")

    assert resp_err.status_code == 302
    mock_notif_err.assert_not_called()


def test_cp_ser_40_ctrl_finalizar_servicio_post_exitoso_y_error(cliente_autenticado):
    """CP-SER-40: Controlador POST /servicios/finalizar/<id>/<placa> exitoso y con error."""
    # 1. Éxito
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.finalizar", return_value={"status": True, "mensaje": "Finalizado"}) as mock_fin, \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif:

        resp_ok = cliente_autenticado.post(
            "/servicios/finalizar/1/ABC123",
            data={"costo_final": "200.00"}
        )

    assert resp_ok.status_code == 302
    assert resp_ok.headers["Location"].endswith("/servicios")
    mock_fin.assert_called_once_with(1, "ABC123", "12345678", "200.00")
    mock_notif.assert_called_once()

    # 2. Error (costo no registrado)
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.finalizar", return_value={"status": False, "mensaje": "Falta costo final"}), \
         patch("controllers.servicios_controller.NotificacionManager.crear_multiple") as mock_notif_err:

        resp_err = cliente_autenticado.post(
            "/servicios/finalizar/1/ABC123",
            data={"costo_final": ""}
        )

    assert resp_err.status_code == 302
    mock_notif_err.assert_not_called()


def test_cp_ser_41_ctrl_ver_recibo_servicio_existente_e_inexistente(cliente_autenticado):
    """CP-SER-41: Controlador GET /servicios/recibo/<id> existente e inexistente."""
    # 1. Existente
    servicio_mock = {"cod_servicios": 1, "nombre_servicio": "Lavado"}
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=servicio_mock), \
         patch("controllers.servicios_controller.render_template", return_value="<html>Recibo</html>") as mock_render:

        resp_ok = cliente_autenticado.get("/servicios/recibo/1")

    assert resp_ok.status_code == 200
    mock_render.assert_called_once_with("servicios/recibo.html", servicio=servicio_mock)

    # 2. Inexistente redirige con flash danger
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.servicios_controller.Servicios.obtener_servicio_por_codigo", return_value=None):

        resp_no = cliente_autenticado.get("/servicios/recibo/999")

    assert resp_no.status_code == 302
    assert resp_no.headers["Location"].endswith("/servicios")


def test_cp_ser_42_ctrl_acceso_sin_sesion_redirige_a_login(app_client):
    """CP-SER-42: Bloqueo de acceso por ausencia de sesión activa en GET /servicios y POST /servicios/nuevo."""
    # Intento GET sin sesión
    resp_get = app_client.get("/servicios")
    assert resp_get.status_code == 302
    assert resp_get.headers["Location"].endswith("/login")

    # Intento POST sin sesión
    resp_post = app_client.post("/servicios/nuevo", data={})
    assert resp_post.status_code == 302
    assert resp_post.headers["Location"].endswith("/login")


def test_cp_ser_43_ctrl_acceso_sin_permiso_redirige_a_index(cliente_sin_permiso):
    """CP-SER-43: Bloqueo de acceso por falta de permisos de rol redirige a la raíz (index)."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=False):
        # Intento GET con rol no autorizado
        resp_get = cliente_sin_permiso.get("/servicios")
        assert resp_get.status_code == 302
        assert resp_get.headers["Location"].endswith("/")

        # Intento POST con rol no autorizado
        resp_post = cliente_sin_permiso.post("/servicios/nuevo", data={})
        assert resp_post.status_code == 302
        assert resp_post.headers["Location"].endswith("/")