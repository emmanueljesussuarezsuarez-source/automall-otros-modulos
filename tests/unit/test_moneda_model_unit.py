import pytest
from mysql.connector import Error
from models.monedas import Moneda
from models.db import ConexionBD
from models.bitacora import Bitacora


# ==============================================================================
# PRUEBAS UNITARIAS: VALIDACIONES Y VALORES LÍMITE (MONEDA Y DIGITAL)
# ==============================================================================

@pytest.mark.parametrize("nombre_invalido", ["", None, "   ", "D", " D "])
def test_unit_moneda_validar_nombre_corto_falla_sin_abrir_bd(mocker, nombre_invalido):
    """Unitaria: Rechaza nombre vacío, None o < 2 chars sin abrir conexión a BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El nombre de la moneda debe tener al menos 2 caracteres."):
        Moneda.guardar(nombre_invalido, "$", "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_moneda_validar_nombre_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 50): Falla si el nombre supera 50 caracteres."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El nombre de la moneda no puede superar los 50 caracteres."):
        Moneda.guardar("M" * 51, "$", "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_moneda_validar_simbolo_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 10): Falla si el símbolo supera 10 caracteres."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El símbolo de la moneda no puede superar los 10 caracteres."):
        Moneda.guardar("Dólar", "S" * 11, "Activo", "12345678")

    espia_bd.assert_not_called()


@pytest.mark.parametrize("estado_invalido", ["Desconocido", "", None, 1])
def test_unit_moneda_validar_estado_invalido_falla_sin_abrir_bd(mocker, estado_invalido):
    """Unitaria: Rechaza estados distintos a 'Activo' o 'Inactivo' sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El estado de la moneda no es válido."):
        Moneda.guardar("Dólar", "$", estado_invalido, "12345678")

    espia_bd.assert_not_called()


def test_unit_moneda_actualizar_validacion_falla_sin_abrir_bd(mocker):
    """Unitaria: Verifica que actualizar valide datos antes de abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El estado de la moneda no es válido."):
        Moneda.actualizar(1, "Euro", "€", "Suspendido", "12345678")

    espia_bd.assert_not_called()


@pytest.mark.parametrize("nombre_invalido", ["", None, "   ", "B", " B "])
def test_unit_moneda_digital_validar_nombre_corto_falla_sin_abrir_bd(mocker, nombre_invalido):
    """Unitaria: Rechaza nombre digital vacío, None o < 2 chars sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El nombre de la moneda digital debe tener al menos 2 caracteres."):
        Moneda.guardar_digital(nombre_invalido, "BTC", 1, "12345678")

    espia_bd.assert_not_called()


def test_unit_moneda_digital_validar_nombre_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 50): Falla si el nombre digital supera 50 caracteres."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El nombre de la moneda digital no puede superar los 50 caracteres."):
        Moneda.guardar_digital("B" * 51, "BTC", 1, "12345678")

    espia_bd.assert_not_called()


def test_unit_moneda_digital_validar_simbolo_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 30): Falla si el símbolo digital supera 30 caracteres."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(ValueError, match="El símbolo digital no puede superar los 30 caracteres."):
        Moneda.actualizar_digital(1, "Bitcoin", "S" * 31, 1, "12345678")

    espia_bd.assert_not_called()


# ==============================================================================
# PRUEBAS UNITARIAS: CRUD DE MONEDA TRADICIONAL
# ==============================================================================

def test_unit_moneda_guardar_exitoso(mocker):
    """Unitaria: Verifica cálculo de correlativo, normalización .strip(), bitácora y commit."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (4,)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.guardar("  Euro  ", "  €  ", "Activo", "12345678")

    assert resultado is True
    assert mock_cursor.execute.call_count == 2
    primera_sql = mock_cursor.execute.call_args_list[0][0][0]
    assert "SELECT COALESCE(MAX(cod_moneda), 0) + 1" in primera_sql
    segunda_sql, parametros = mock_cursor.execute.call_args_list[1][0]
    assert "INSERT INTO moneda" in segunda_sql
    assert parametros == (4, "Euro", "€", "Activo")
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_guardar_valores_limite_y_simbolo_vacio(mocker):
    """Unitaria (Valores límite válidos): Acepta 50 chars, simbolo None/'' -> guarda None."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.guardar("M" * 50, "", "Inactivo", "12345678")

    assert resultado is True
    _, parametros = mock_cursor.execute.call_args_list[1][0]
    assert parametros == (1, "M" * 50, None, "Inactivo")
    mock_conexion.commit.assert_called_once()


def test_unit_moneda_guardar_duplicado_mysql_1062(mocker):
    """Unitaria: Captura error 1062 al guardar, ejecuta rollback() y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = [None, Error(msg="Duplicate entry", errno=1062)]
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="La moneda 'Dólar' ya se encuentra registrada."):
        Moneda.guardar("Dólar", "$", "Activo", "12345678")

    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_guardar_error_bd_general(mocker):
    """Unitaria: Captura error SQL distinto de 1062 al guardar y ejecuta rollback()."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Connection lost", errno=2013)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    with pytest.raises(Exception, match="Error en la base de datos:"):
        Moneda.guardar("Euro", "€", "Activo", "12345678")

    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_actualizar_exitoso(mocker):
    """Unitaria: Verifica actualización correcta, .strip(), bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.rowcount = 1
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.actualizar(1, "  Peso  ", "  $  ", "Activo", "12345678")

    assert resultado is True
    sql, params = mock_cursor.execute.call_args[0]
    assert "UPDATE moneda" in sql
    assert params == ("Peso", "$", "Activo", 1)
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_actualizar_no_existente_rowcount_cero(mocker):
    """Unitaria: Si rowcount == 0, lanza excepción, hace rollback() y no registra bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.rowcount = 0
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="La moneda indicada no existe."):
        Moneda.actualizar(999, "Peso", "$", "Activo", "12345678")

    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_actualizar_duplicado_1062_y_error_general(mocker):
    """Unitaria: Verifica manejo de error 1062 y error SQL genérico al actualizar moneda."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    mock_cursor.execute.side_effect = Error(msg="Dup", errno=1062)
    with pytest.raises(Exception, match="La moneda 'Euro' ya existe."):
        Moneda.actualizar(1, "Euro", "€", "Activo", "12345678")
    mock_conexion.rollback.assert_called_once()

    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="SQL fail", errno=1054)
    with pytest.raises(Exception, match="Error al actualizar la moneda:"):
        Moneda.actualizar(1, "Euro", "€", "Activo", "12345678")
    mock_conexion.rollback.assert_called_once()


def test_unit_moneda_eliminar_logico_exitoso(mocker):
    """Unitaria: Verifica desactivación lógica de moneda, bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.rowcount = 1
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.eliminar(2, "12345678")

    assert resultado is True
    sql, params = mock_cursor.execute.call_args[0]
    assert " ".join(sql.split()) == "UPDATE moneda SET estado = 'Inactivo' WHERE cod_moneda = %s"
    assert params == (2,)
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_eliminar_no_existente_y_error_bd(mocker):
    """Unitaria: Verifica rollback ante rowcount == 0 y ante Error MySQL al eliminar."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    # Caso 1: no existe
    mock_cursor.rowcount = 0
    with pytest.raises(Exception, match="La moneda indicada no existe."):
        Moneda.eliminar(99, "12345678")
    mock_conexion.rollback.assert_called_once()
    mock_bitacora.assert_not_called()

    # Caso 2: error MySQL
    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="FK constraint", errno=1451)
    with pytest.raises(Exception, match="Error al desactivar la moneda:"):
        Moneda.eliminar(2, "12345678")
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_obtener_todos_exitoso(mocker):
    """Unitaria: Verifica lista de monedas, cursor dictionary=True y cierre en finally."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    lista_ficticia = [{"cod_moneda": 1, "nombre_moneda": "Dólar", "simbolo": "$", "estado": "Activo"}]
    mock_cursor.fetchall.return_value = lista_ficticia
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Moneda.obtener_todos()

    assert resultado == lista_ficticia
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: CRUD DE MONEDA DIGITAL
# ==============================================================================

def test_unit_moneda_digital_guardar_exitoso(mocker):
    """Unitaria: Verifica cálculo de correlativo, inserción de moneda digital y bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.guardar_digital("  Bitcoin  ", "  BTC  ", 1, "12345678")

    assert resultado is True
    _, params = mock_cursor.execute.call_args_list[1][0]
    assert params == (1, "Bitcoin", "BTC", 1)
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_guardar_duplicado_1062_y_error_general(mocker):
    """Unitaria: Verifica rollback ante error 1062 y error general al guardar moneda digital."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    mock_cursor.execute.side_effect = [None, Error(msg="Dup", errno=1062)]
    with pytest.raises(Exception, match="La moneda digital 'Zelle' ya se encuentra registrada."):
        Moneda.guardar_digital("Zelle", None, 1, "12345678")
    mock_conexion.rollback.assert_called_once()

    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="DB down", errno=2003)
    with pytest.raises(Exception, match="Error en la base de datos:"):
        Moneda.guardar_digital("Zelle", "ZLL", 1, "12345678")
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_actualizar_exitoso(mocker):
    """Unitaria: Verifica actualización de moneda digital, bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.rowcount = 1
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.actualizar_digital(1, "  Tether  ", "  USDT  ", 1, "12345678")

    assert resultado is True
    sql, params = mock_cursor.execute.call_args[0]
    assert "UPDATE moneda_digital" in sql
    assert params == ("Tether", "USDT", 1, 1)
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_actualizar_no_existente_y_errores_bd(mocker):
    """Unitaria: Verifica rollback ante rowcount == 0, error 1062 y error SQL genérico."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    # rowcount == 0
    mock_cursor.rowcount = 0
    with pytest.raises(Exception, match="La moneda digital indicada no existe."):
        Moneda.actualizar_digital(99, "Tether", "USDT", 1, "12345678")
    mock_conexion.rollback.assert_called_once()

    # 1062
    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="Dup", errno=1062)
    with pytest.raises(Exception, match="La moneda digital 'Tether' ya existe."):
        Moneda.actualizar_digital(1, "Tether", "USDT", 1, "12345678")
    mock_conexion.rollback.assert_called_once()

    # Error genérico
    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="Timeout", errno=2013)
    with pytest.raises(Exception, match="Error al actualizar la moneda digital:"):
        Moneda.actualizar_digital(1, "Tether", "USDT", 1, "12345678")
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_eliminar_exitoso(mocker):
    """Unitaria: Verifica desactivación lógica (estado=0) de moneda digital y bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.rowcount = 1
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Moneda.eliminar_digital(3, "12345678")

    assert resultado is True
    sql, params = mock_cursor.execute.call_args[0]
    assert " ".join(sql.split()) == "UPDATE moneda_digital SET estado = 0 WHERE cod_mon_digital = %s"
    assert params == (3,)
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=31)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_eliminar_no_existente_y_error_bd(mocker):
    """Unitaria: Verifica rollback ante rowcount == 0 y error MySQL en eliminar_digital."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    mock_cursor.rowcount = 0
    with pytest.raises(Exception, match="La moneda digital indicada no existe."):
        Moneda.eliminar_digital(88, "12345678")
    mock_conexion.rollback.assert_called_once()

    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Error(msg="FK fail", errno=1451)
    with pytest.raises(Exception, match="Error al desactivar la moneda digital:"):
        Moneda.eliminar_digital(3, "12345678")
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_moneda_digital_obtener_todas_exitoso(mocker):
    """Unitaria: Verifica consulta de todas las monedas digitales y cierre en finally."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    digitales = [{"cod_mon_digital": 1, "nombre_digital": "Zelle", "simbolo_digital": "ZLL", "estado": 1}]
    mock_cursor.fetchall.return_value = digitales
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Moneda.obtener_todas_digitales()

    assert resultado == digitales
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()