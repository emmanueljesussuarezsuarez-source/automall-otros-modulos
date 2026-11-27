"""
Módulo de Pruebas Unitarias para el Módulo Taller
Archivo: tests/unit/test_taller.py
Metodología: Caja blanca, partición de equivalencia, análisis de valores límite y mocks.
Aislamiento: Base de datos MySQL simulada (sin llamadas reales a BD).
"""

from unittest.mock import MagicMock, Mock, patch
import pytest

from app import app
from models.taller import Taller
from utils.validaciones_taller import ValidacionTaller



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
    """Verifica que los imports, la aplicación Flask y los fixtures inicien correctamente."""
    conexion, cursor = conexion_mock
    assert conexion is not None
    assert cursor is not None
    assert app_client is not None
    assert cliente_autenticado is not None

    


# BLOQUE 2: PRUEBAS DE VALIDACIONES (CP-TAL-01 AL CP-TAL-12)


def test_cp_tal_01_nombre_valido():
    """CP-TAL-01: Validación exitosa de nombre de taller con caracteres válidos."""
    nombres_validos = [
        "Taller Auto-Express S.A.",
        "Mecánica José",
        "Taller 123",
        "Taller Los Andes - Central."
    ]
    for nombre in nombres_validos:
        resultado = ValidacionTaller.validar_nombre_taller(nombre)
        assert resultado is None, f"Se esperaba None para '{nombre}' pero retornó '{resultado}'"


@pytest.mark.parametrize("nombre_invalido", ["", None, "   "])
def test_cp_tal_02_nombre_vacio_o_espacios(nombre_invalido):
    """CP-TAL-02: Rechazo de nombre vacío, nulo o de solo espacios."""
    resultado = ValidacionTaller.validar_nombre_taller(nombre_invalido)
    assert resultado == "El nombre del taller es obligatorio."


@pytest.mark.parametrize("nombre_corto", ["A", "AB", "  X  ", " 1 "])
def test_cp_tal_03_nombre_menor_tres_caracteres(nombre_corto):
    """CP-TAL-03: Rechazo de nombre por valor límite inferior (< 3 caracteres)."""
    resultado = ValidacionTaller.validar_nombre_taller(nombre_corto)
    assert resultado == "El nombre del taller debe tener al menos 3 caracteres."


def test_cp_tal_04_nombre_limite_100_y_excede_101():
    """CP-TAL-04: Límite superior exacto (100) y rechazo por exceder límite (101 caracteres)."""
    nombre_limite_100 = "A" * 100
    assert ValidacionTaller.validar_nombre_taller(nombre_limite_100) is None

    nombre_excede_101 = "A" * 101
    assert ValidacionTaller.validar_nombre_taller(nombre_excede_101) == (
        "El nombre del taller no puede superar 100 caracteres."
    )


@pytest.mark.parametrize("nombre_caracteres_raros", [
    "Taller@Central",
    "Taller#1",
    "Taller/Principal",
    "<script>alert(1)</script>",
    "Taller & Repuestos"
])
def test_cp_tal_05_nombre_caracteres_no_permitidos(nombre_caracteres_raros):
    """CP-TAL-05: Rechazo de nombre con caracteres especiales no permitidos por regex."""
    resultado = ValidacionTaller.validar_nombre_taller(nombre_caracteres_raros)
    assert resultado == "El nombre del taller contiene caracteres no permitidos."


def test_cp_tal_06_nombre_duplicado_existe_func():
    """CP-TAL-06: Detección de nombre duplicado mediante función existe_func."""
    mock_existe = Mock(return_value=True)
    resultado = ValidacionTaller.validar_nombre_taller(
        "Taller Central",
        existe_func=mock_existe
    )
    assert resultado == "Ya existe un taller con ese nombre."
    mock_existe.assert_called_once_with("Taller Central", None)

    # Verificamos que si no existe retorne None
    mock_no_existe = Mock(return_value=False)
    resultado_ok = ValidacionTaller.validar_nombre_taller(
        "Taller Central",
        excluir_cod_taller=5,
        existe_func=mock_no_existe
    )
    assert resultado_ok is None
    mock_no_existe.assert_called_once_with("Taller Central", 5)


def test_cp_tal_07_direccion_valida():
    """CP-TAL-07: Validación exitosa de dirección dentro del rango permitido (5 a 255 caracteres)."""
    assert ValidacionTaller.validar_direccion("12345") is None
    assert ValidacionTaller.validar_direccion("Avenida Libertador, Galpón 4") is None
    assert ValidacionTaller.validar_direccion("A" * 255) is None


@pytest.mark.parametrize("direccion_invalida", ["", None, "    "])
def test_cp_tal_08_direccion_vacia_o_espacios(direccion_invalida):
    """CP-TAL-08: Rechazo de dirección vacía o solo espacios."""
    resultado = ValidacionTaller.validar_direccion(direccion_invalida)
    assert resultado == "La dirección es obligatoria."


@pytest.mark.parametrize("direccion_corta", ["A", "ABCD", " Av "])
def test_cp_tal_09_direccion_menor_cinco_caracteres(direccion_corta):
    """CP-TAL-09: Rechazo de dirección por valor límite inferior (< 5 caracteres)."""
    resultado = ValidacionTaller.validar_direccion(direccion_corta)
    assert resultado == "La dirección debe tener al menos 5 caracteres."


def test_cp_tal_10_direccion_excede_255_caracteres():
    """CP-TAL-10: Rechazo de dirección por valor límite superior (> 255 caracteres)."""
    direccion_larga = "A" * 256
    resultado = ValidacionTaller.validar_direccion(direccion_larga)
    assert resultado == "La dirección no puede superar 255 caracteres."


def test_cp_tal_11_estado_valido_e_invalido():
    """CP-TAL-11: Validación del campo estado ('0' y '1' válidos, otros rechazados)."""
    # Estados válidos
    for est in ["0", "1", 0, 1, None, " 1 "]:
        assert ValidacionTaller.validar_estado(est) is None

    # Estados inválidos
    for est in ["2", "-1", "Activo", "Inactivo", True, "X"]:
        assert ValidacionTaller.validar_estado(est) == "El estado seleccionado no es válido."


def test_cp_tal_12_validar_taller_integral():
    """CP-TAL-12: Validación integral de taller retornando mapa de errores si aplica."""
    mock_no_existe = Mock(return_value=False)

    # Caso exitoso integral
    valido, errores = ValidacionTaller.validar_taller(
        nombre_taller="Taller Mecánico Central",
        direccion="Av. Principal Calle 10",
        estado="1",
        existe_func=mock_no_existe
    )
    assert valido is True
    assert errores == {}

    # Caso con múltiples campos inválidos
    valido_err, errores_err = ValidacionTaller.validar_taller(
        nombre_taller="",
        direccion="Av",
        estado="9"
    )
    assert valido_err is False
    assert "nombre_taller" in errores_err
    assert "direccion" in errores_err
    assert "estado" in errores_err


    

# BLOQUE 3: PRUEBAS DE GUARDAR (CP-TAL-13 AL CP-TAL-16)


def test_cp_tal_13_guardar_taller_exitoso_con_bitacora(conexion_mock):
    """CP-TAL-13: Registro exitoso de taller con datos válidos, commit y bitácora."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock:

        resultado = Taller.guardar(
            nombre_taller="  Taller Central  ",
            direccion="  Av. Principal #10  ",
            estado="1",
            cedula_usuario="12345678"
        )

    # Verificación de respuesta
    assert resultado["status"] is True
    assert resultado["mensaje"] == "Taller registrado correctamente."

    # Verificación de limpieza de espacios (strip) e inserción SQL
    assert cursor.execute.called
    sql_ejecutado = cursor.execute.call_args[0][0]
    parametros = cursor.execute.call_args[0][1]

    assert "INSERT INTO taller" in sql_ejecutado
    assert parametros == ("Taller Central", "Av. Principal #10", "1")

    # Verificación transaccional y bitácora
    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=1, cod_modulo=10)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_tal_14_guardar_taller_sin_usuario_omite_bitacora(conexion_mock):
    """CP-TAL-14: Registro exitoso de taller sin cédula de usuario omite llamada a bitácora."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock:

        resultado = Taller.guardar(
            nombre_taller="Taller Los Andes",
            direccion="Zona Industrial Calle 4",
            estado="1",
            cedula_usuario=None
        )

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Taller registrado correctamente."
    conexion.commit.assert_called_once()
    bitacora_mock.assert_not_called()


def test_cp_tal_15_guardar_rechaza_por_validacion_sin_abrir_bd(conexion_mock):
    """CP-TAL-15: Rechazo al guardar por error de validación sin abrir conexión a BD."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        # 1. Nombre inválido
        resultado_nombre = Taller.guardar("", "Av. Principal #10")
        assert resultado_nombre["status"] is False
        assert resultado_nombre["mensaje"] == "El nombre del taller es obligatorio."

    # 2. Dirección inválida (< 5 caracteres)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False):
        resultado_dir = Taller.guardar("Taller Central", "Av 1")
        assert resultado_dir["status"] is False
        assert resultado_dir["mensaje"] == "La dirección debe tener al menos 5 caracteres."

    # 3. Nombre duplicado detectado en validación
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=True):
        resultado_dup = Taller.guardar("Taller Existente", "Av. Principal #10")
        assert resultado_dup["status"] is False
        assert resultado_dup["mensaje"] == "Ya existe un taller con ese nombre."

    # Confirmar que en ningún caso inválido se ejecutó INSERT ni commit
    cursor.execute.assert_not_called()
    conexion.commit.assert_not_called()


def test_cp_tal_16_guardar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-TAL-16: Manejo de error de base de datos y ejecución de rollback() al guardar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Pérdida de conexión con servidor MySQL (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False):

        resultado = Taller.guardar(
            nombre_taller="Taller Central",
            direccion="Av. Principal #10",
            estado="1",
            cedula_usuario="12345678"
        )

    # Debe retornar status False sin levantar excepción no controlada
    assert resultado["status"] is False
    assert "Error al guardar el taller" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    # Verificación de rollback y cierre en bloque finally
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


    


# BLOQUE 4: PRUEBAS DE ACTUALIZAR (CP-TAL-17 AL CP-TAL-19)

def test_cp_tal_17_actualizar_taller_exitoso_con_bitacora(conexion_mock):
    """CP-TAL-17: Actualización exitosa de taller con datos válidos, commit y bitácora."""
    conexion, cursor = conexion_mock

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock:

        resultado = Taller.actualizar(
            cod_taller=3,
            nombre_taller="  Taller Los Andes  ",
            direccion="  Nueva Sede Industrial  ",
            estado="0",
            cedula_usuario="12345678"
        )

    # Verificación de respuesta
    assert resultado["status"] is True
    assert resultado["mensaje"] == "Taller actualizado correctamente."

    # Verificación de parámetros SQL y limpieza de espacios
    assert cursor.execute.called
    sql_ejecutado = cursor.execute.call_args[0][0]
    parametros = cursor.execute.call_args[0][1]

    assert "UPDATE taller" in sql_ejecutado
    assert "WHERE cod_taller = %s" in sql_ejecutado
    assert parametros == ("Taller Los Andes", "Nueva Sede Industrial", "0", 3)

    # Verificación transaccional y bitácora (cod_accion=3)
    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=3, cod_modulo=10)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_cp_tal_18_actualizar_rechaza_datos_invalidos_sin_ejecutar_update(conexion_mock):
    """CP-TAL-18: Rechazo de actualización por datos inválidos sin abrir conexión ni ejecutar SQL."""
    conexion, cursor = conexion_mock

    # 1. Nombre vacío
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        res_nombre = Taller.actualizar(3, "", "Av. Principal 123", "1")
        assert res_nombre["status"] is False
        assert res_nombre["mensaje"] == "El nombre del taller es obligatorio."

    # 2. Dirección menor a 5 caracteres
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False):
        res_dir = Taller.actualizar(3, "Taller Central", "Av", "1")
        assert res_dir["status"] is False
        assert res_dir["mensaje"] == "La dirección debe tener al menos 5 caracteres."

    # 3. Estado fuera de rango
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False):
        res_est = Taller.actualizar(3, "Taller Central", "Av. Principal 123", "9")
        assert res_est["status"] is False
        assert res_est["mensaje"] == "El estado seleccionado no es válido."

    # 4. Nombre duplicado en otro taller distinto
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=True):
        res_dup = Taller.actualizar(3, "Taller Existente", "Av. Principal 123", "1")
        assert res_dup["status"] is False
        assert res_dup["mensaje"] == "Ya existe un taller con ese nombre."

    # Confirmamos que nunca se abrió ni ejecutó UPDATE ni commit
    cursor.execute.assert_not_called()
    conexion.commit.assert_not_called()


def test_cp_tal_19_actualizar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-TAL-19: Manejo de error de base de datos y ejecución de rollback() al actualizar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo de comunicación en base de datos (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Taller.existe_nombre", return_value=False):

        resultado = Taller.actualizar(
            cod_taller=3,
            nombre_taller="Taller Los Andes",
            direccion="Nueva Sede Industrial",
            estado="1",
            cedula_usuario="12345678"
        )

    # Verificación de captura de excepción
    assert resultado["status"] is False
    assert "Error al actualizar el taller" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    # Verificación de rollback y cierre de recursos
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


    


# BLOQUE 5: PRUEBAS DE ELIMINAR / DESACTIVAR (CP-TAL-20 Y CP-TAL-21)


def test_cp_tal_20_eliminar_logico_exitoso_con_bitacora(conexion_mock):
    """CP-TAL-20: Desactivación lógica exitosa de taller (estado = '0'), commit y bitácora."""
    conexion, cursor = conexion_mock

    # Caso 1: Eliminación con cédula de usuario (registra auditoría en bitácora)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock:

        resultado = Taller.eliminar(cod_taller=5, cedula_usuario="12345678")

    assert resultado["status"] is True
    assert resultado["mensaje"] == "Taller desactivado correctamente."

    # Verificación de sentencia SQL para borrado lógico
    assert cursor.execute.called
    sql_ejecutado = cursor.execute.call_args[0][0]
    parametros = cursor.execute.call_args[0][1]

    assert "UPDATE taller" in sql_ejecutado
    assert "SET estado = '0'" in sql_ejecutado
    assert "WHERE cod_taller = %s" in sql_ejecutado
    assert parametros == (5,)

    conexion.commit.assert_called_once()
    bitacora_mock.assert_called_once_with("12345678", cod_accion=3, cod_modulo=10)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    # Caso 2: Eliminación sin usuario (omite bitácora)
    conexion.reset_mock()
    cursor.reset_mock()
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock_vacio:

        resultado_sin_usuario = Taller.eliminar(cod_taller=5, cedula_usuario=None)

    assert resultado_sin_usuario["status"] is True
    conexion.commit.assert_called_once()
    bitacora_mock_vacio.assert_not_called()


def test_cp_tal_21_eliminar_manejo_error_bd_y_rollback(conexion_mock):
    """CP-TAL-21: Manejo de error de base de datos y ejecución de rollback() al desactivar."""
    conexion, cursor = conexion_mock
    cursor.execute.side_effect = Exception("Fallo de conexión con MySQL (errno=2013)")

    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Taller.eliminar(cod_taller=5, cedula_usuario="12345678")

    # Verificación de captura de error y mensaje descriptivo
    assert resultado["status"] is False
    assert "Error al desactivar el taller" in resultado["mensaje"]
    assert "errno=2013" in resultado["mensaje"]

    # Verificación de rollback y cierre en finally
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    


# BLOQUE 6: PRUEBAS DE CONSULTAS (CP-TAL-22 AL CP-TAL-24)


def test_cp_tal_22_obtener_todos_talleres_activos_con_y_sin_bitacora(conexion_mock):
    """CP-TAL-22: Consulta de talleres activos (estado = '1'), orden descendente y bitácora condicional."""
    conexion, cursor = conexion_mock
    talleres_esperados = [
        {"cod_taller": 2, "nombre_taller": "Taller Norte", "direccion": "Av. 10", "estado": "1"},
        {"cod_taller": 1, "nombre_taller": "Taller Sur", "direccion": "Av. 5", "estado": "1"}
    ]
    cursor.fetchall.return_value = talleres_esperados

    # Caso 1: Consulta con cédula de usuario (registra cod_accion=2 en bitácora)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Bitacora.registrar") as bitacora_mock:

        resultado = Taller.obtener_todos(cedula_usuario="12345678")

    assert resultado == talleres_esperados
    conexion.cursor.assert_called_with(dictionary=True)
    sql_ejecutado = cursor.execute.call_args[0][0]
    assert "WHERE estado = '1'" in sql_ejecutado
    assert "ORDER BY cod_taller DESC" in sql_ejecutado

    bitacora_mock.assert_called_once_with("12345678", cod_accion=2, cod_modulo=10)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    # Caso 2: Consulta sin cédula de usuario (no registra en bitácora)
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion), \
         patch("models.taller.Bitacora.registrar") as bitacora_vacio:

        resultado_sin_usuario = Taller.obtener_todos(cedula_usuario=None)

    assert resultado_sin_usuario == talleres_esperados
    bitacora_vacio.assert_not_called()


def test_cp_tal_23_obtener_por_id_existente_e_inexistente(conexion_mock):
    """CP-TAL-23: Consulta de taller por ID individual existente e inexistente."""
    conexion, cursor = conexion_mock
    taller_esperado = {
        "cod_taller": 1,
        "nombre_taller": "Taller Central",
        "direccion": "Av. Principal",
        "estado": "1"
    }

    # Caso 1: ID existente
    cursor.fetchone.return_value = taller_esperado
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado = Taller.obtener_por_id(1)

    assert resultado == taller_esperado
    sql_ejecutado = cursor.execute.call_args[0][0]
    parametros = cursor.execute.call_args[0][1]
    assert "WHERE cod_taller = %s" in sql_ejecutado
    assert parametros == (1,)
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()

    # Caso 2: ID inexistente retorna None
    cursor.reset_mock()
    conexion.reset_mock()
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado_inexistente = Taller.obtener_por_id(999)

    assert resultado_inexistente is None
    assert cursor.execute.call_args[0][1] == (999,)


def test_cp_tal_24_existe_nombre_crear_y_editar(conexion_mock):
    """CP-TAL-24: Verificación de nombre existente al crear (sin excluir) y al editar (excluyendo ID)."""
    conexion, cursor = conexion_mock

    # Caso 1: Al crear, nombre ya existe
    cursor.fetchone.return_value = {"cod_taller": 1}
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        existe = Taller.existe_nombre("  Taller Central  ")

    assert existe is True
    sql_1 = cursor.execute.call_args[0][0]
    param_1 = cursor.execute.call_args[0][1]
    assert "LOWER(nombre_taller) = LOWER(%s)" in sql_1
    assert "cod_taller <> %s" not in sql_1
    assert param_1 == ("Taller Central",)

    # Caso 2: Al crear, nombre no existe
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        no_existe = Taller.existe_nombre("Taller Inexistente")
    assert no_existe is False

    # Caso 3: Al editar, excluye el código del taller actual
    cursor.fetchone.return_value = None
    with patch("models.db.ConexionBD.obtener_conexion", return_value=conexion):
        resultado_editar = Taller.existe_nombre("Taller Central", excluir_cod_taller=5)

    assert resultado_editar is False
    sql_3 = cursor.execute.call_args[0][0]
    param_3 = cursor.execute.call_args[0][1]
    assert "cod_taller <> %s" in sql_3
    assert param_3 == ("Taller Central", 5)


def test_taller_modelo_propiedades_y_setters():
    """Verifica la instanciación de la entidad Taller y sus métodos get/set."""
    taller = Taller(cod_taller=1, nombre_taller="Taller Original", direccion="Dir Original", estado="1")
    assert taller.cod_taller == 1
    assert taller.nombre_taller == "Taller Original"
    assert taller.direccion == "Dir Original"
    assert taller.estado == "1"

    taller.cod_taller = 2
    taller.nombre_taller = "Taller Modificado"
    taller.direccion = "Dir Modificada"
    taller.estado = "0"

    assert taller.cod_taller == 2
    assert taller.nombre_taller == "Taller Modificado"
    assert taller.direccion == "Dir Modificada"
    assert taller.estado == "0"


   
# BLOQUE 7: PRUEBAS DE CONTROLADOR / RUTAS Y PERMISOS (CP-TAL-25 AL CP-TAL-34)


def test_cp_tal_25_ctrl_listar_talleres_get_exitoso(cliente_autenticado):
    """CP-TAL-25: Controlador GET /taller exitoso renderiza plantilla taller/index.html."""
    talleres_mock = [
        {"cod_taller": 1, "nombre_taller": "Taller Central", "direccion": "Av 1", "estado": "1"}
    ]

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_todos", return_value=talleres_mock) as mock_obtener, \
         patch("controllers.tallercontroller.render_template", return_value="<html>Listado OK</html>") as mock_render:

        respuesta = cliente_autenticado.get("/taller")

    assert respuesta.status_code == 200
    mock_obtener.assert_called_once_with("12345678")
    mock_render.assert_called_once_with("taller/index.html", talleres=talleres_mock)


def test_cp_tal_26_ctrl_crear_taller_post_exitoso(cliente_autenticado):
    """CP-TAL-26: Controlador POST /taller/nuevo exitoso notifica a staff y redirige."""
    datos_form = {
        "nombre_taller": "  Taller Express  ",
        "direccion": "  Zona Industrial Galpón 5  ",
        "estado": "1"
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.guardar", return_value={"status": True, "mensaje": "Taller registrado correctamente."}) as mock_guardar, \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post("/taller/nuevo", data=datos_form)

    # Redirección HTTP 302 hacia /taller
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")

    # Verificación de parámetros recibidos con strip aplicado en el controlador
    mock_guardar.assert_called_once_with(
        "Taller Express",
        "Zona Industrial Galpón 5",
        "1",
        "12345678"
    )

    # Verificación de emisión de notificación a staff (roles [1, 2])
    mock_notif.assert_called_once()
    kwargs_notif = mock_notif.call_args[1]["notificacion_staff"]
    assert kwargs_notif["titulo"] == "Nuevo Taller Registrado"
    assert kwargs_notif["roles"] == [1, 2]
    assert kwargs_notif["modulo"] == "taller"


def test_cp_tal_27_ctrl_crear_taller_post_error_validacion(cliente_autenticado):
    """CP-TAL-27: Controlador POST /taller/nuevo con fallo de validación redirige con flash danger y sin notificación."""
    datos_invalidos = {"nombre_taller": "", "direccion": "Av. Principal", "estado": "1"}

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.guardar", return_value={"status": False, "mensaje": "El nombre del taller es obligatorio."}), \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post("/taller/nuevo", data=datos_invalidos)

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_notif.assert_not_called()


def test_cp_tal_28_ctrl_editar_taller_post_exitoso(cliente_autenticado):
    """CP-TAL-28: Controlador POST /taller/editar/<id> exitoso actualiza, notifica y redirige."""
    taller_existente = {"cod_taller": 2, "nombre_taller": "Taller Antiguo"}
    datos_edicion = {
        "nombre_taller": "Taller Renovado",
        "direccion": "Avenida 2 Calle 3",
        "estado": "1"
    }

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_por_id", return_value=taller_existente), \
         patch("controllers.tallercontroller.Taller.actualizar", return_value={"status": True, "mensaje": "Taller actualizado correctamente."}) as mock_actualizar, \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post("/taller/editar/2", data=datos_edicion)

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_actualizar.assert_called_once_with(
        2,
        "Taller Renovado",
        "Avenida 2 Calle 3",
        "1",
        "12345678"
    )

    mock_notif.assert_called_once()
    kwargs_notif = mock_notif.call_args[1]["notificacion_staff"]
    assert kwargs_notif["titulo"] == "Taller Actualizado"
    assert kwargs_notif["roles"] == [1, 2]


def test_cp_tal_29_ctrl_editar_taller_inexistente_redirige(cliente_autenticado):
    """CP-TAL-29: Controlador POST /taller/editar/<id> con taller inexistente redirige sin intentar actualizar."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_por_id", return_value=None), \
         patch("controllers.tallercontroller.Taller.actualizar") as mock_actualizar, \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post(
            "/taller/editar/999",
            data={"nombre_taller": "Taller Fantasma", "direccion": "Sin Dirección", "estado": "1"}
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_actualizar.assert_not_called()
    mock_notif.assert_not_called()


def test_cp_tal_30_ctrl_editar_taller_error_actualizacion(cliente_autenticado):
    """CP-TAL-30: Controlador POST /taller/editar/<id> con fallo en actualizar redirige sin notificar."""
    taller_existente = {"cod_taller": 2, "nombre_taller": "Taller Actual"}

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_por_id", return_value=taller_existente), \
         patch("controllers.tallercontroller.Taller.actualizar", return_value={"status": False, "mensaje": "La dirección debe tener al menos 5 caracteres."}), \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post(
            "/taller/editar/2",
            data={"nombre_taller": "Taller Actual", "direccion": "Av", "estado": "1"}
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_notif.assert_not_called()


def test_cp_tal_31_ctrl_eliminar_taller_post_exitoso(cliente_autenticado):
    """CP-TAL-31: Controlador POST /taller/eliminar/<id> exitoso desactiva, notifica al staff y redirige."""
    taller_existente = {"cod_taller": 5, "nombre_taller": "Taller Los Teques"}

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_por_id", return_value=taller_existente), \
         patch("controllers.tallercontroller.Taller.eliminar", return_value={"status": True, "mensaje": "Taller desactivado correctamente."}) as mock_eliminar, \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post("/taller/eliminar/5")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_eliminar.assert_called_once_with(5, "12345678")

    mock_notif.assert_called_once()
    kwargs_notif = mock_notif.call_args[1]["notificacion_staff"]
    assert kwargs_notif["titulo"] == "Taller Desactivado"
    assert "Taller Los Teques" in kwargs_notif["mensaje"]
    assert kwargs_notif["roles"] == [1, 2]


def test_cp_tal_32_ctrl_eliminar_taller_error_desactivacion(cliente_autenticado):
    """CP-TAL-32: Controlador POST /taller/eliminar/<id> con fallo de eliminación redirige sin notificar."""
    taller_existente = {"cod_taller": 5, "nombre_taller": "Taller Los Teques"}

    with patch("utils.permisos.Permiso.verificar_acceso", return_value=True), \
         patch("controllers.tallercontroller.Taller.obtener_por_id", return_value=taller_existente), \
         patch("controllers.tallercontroller.Taller.eliminar", return_value={"status": False, "mensaje": "Error al desactivar el taller"}), \
         patch("controllers.tallercontroller.NotificacionManager.crear_multiple") as mock_notif:

        respuesta = cliente_autenticado.post("/taller/eliminar/5")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/taller")
    mock_notif.assert_not_called()


def test_cp_tal_33_ctrl_acceso_sin_sesion_redirige_a_login(app_client):
    """CP-TAL-33: Bloqueo de acceso por ausencia de sesión activa en GET /taller y POST /taller/nuevo."""
    # Intento GET sin sesión
    resp_get = app_client.get("/taller")
    assert resp_get.status_code == 302
    assert resp_get.headers["Location"].endswith("/login")

    # Intento POST sin sesión
    resp_post = app_client.post("/taller/nuevo", data={})
    assert resp_post.status_code == 302
    assert resp_post.headers["Location"].endswith("/login")


def test_cp_tal_34_ctrl_acceso_sin_permiso_redirige_a_index(cliente_sin_permiso):
    """CP-TAL-34: Bloqueo de acceso por falta de permisos de rol redirige a la página principal (index)."""
    with patch("utils.permisos.Permiso.verificar_acceso", return_value=False):
        # Intento GET con rol sin permiso
        resp_get = cliente_sin_permiso.get("/taller")
        assert resp_get.status_code == 302
        assert resp_get.headers["Location"].endswith("/")

        # Intento POST con rol sin permiso
        resp_post = cliente_sin_permiso.post("/taller/nuevo", data={})
        assert resp_post.status_code == 302
        assert resp_post.headers["Location"].endswith("/")