import pytest
from mysql.connector import Error
from models.metodo import MetodoPago
from models.db import ConexionBD
from models.bitacora import Bitacora


# ==============================================================================
# PRUEBAS UNITARIAS: VALIDACIONES DE NEGOCIO Y VALORES LÍMITE (MODELO)
# ==============================================================================

@pytest.mark.parametrize("nombre_invalido", ["", None, "   ", "Z", " Z "])
def test_unit_metodo_guardar_nombre_invalido_o_corto_falla_sin_abrir_bd(mocker, nombre_invalido):
    """Unitaria: Rechaza nombre vacío, None, espacios o < 2 chars sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(Exception, match="Validación: El nombre del método debe tener al menos 2 caracteres."):
        MetodoPago.guardar(nombre_invalido, 1, "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_metodo_guardar_nombre_demasiado_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 50): Falla si el nombre supera 50 caracteres sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")
    nombre_largo = "M" * 51

    with pytest.raises(Exception, match="Validación: El nombre del método es demasiado largo"):
        MetodoPago.guardar(nombre_largo, 1, "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_metodo_actualizar_validacion_falla_sin_abrir_bd(mocker):
    """Unitaria: Verifica que actualizar también valide nombre corto o > 50 chars sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(Exception, match="Validación: El nombre del método debe tener al menos 2 caracteres."):
        MetodoPago.actualizar(2, "X", 1, "Activo", "12345678")

    with pytest.raises(Exception, match="Validación: El nombre del método es demasiado largo"):
        MetodoPago.actualizar(2, "M" * 51, 1, "Activo", "12345678")

    espia_bd.assert_not_called()


# ==============================================================================
# PRUEBAS UNITARIAS: OPERACIONES DE ESCRITURA (GUARDAR)
# ==============================================================================

def test_unit_metodo_guardar_exitoso_y_normalizacion_strip(mocker):
    """Unitaria: Verifica inserción con .strip(), bitácora, commit y cierre de recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = MetodoPago.guardar("  Transferencia Bancaria  ", 1, "Activo", "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO metodo_pago (nombre_metodo, requiere_referencia, estado) VALUES (%s, %s, %s)",
        ("Transferencia Bancaria", 1, "Activo")
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=29)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


@pytest.mark.parametrize("nombre_valido", ["PM", "M" * 50])
def test_unit_metodo_guardar_valores_limite_validos(mocker, nombre_valido):
    """Unitaria (Valores límite válidos): Acepta exactamente 2 y 50 caracteres."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    resultado = MetodoPago.guardar(nombre_valido, 0, "Activo", "12345678")

    assert resultado is True
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_guardar_duplicado_mysql_1062(mocker):
    """Unitaria: Captura error 1062, no hace commit ni bitácora, y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry", errno=1062)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="El método de pago 'Zelle' ya se encuentra registrado."):
        MetodoPago.guardar("Zelle", 1, "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_guardar_error_bd_general(mocker):
    """Unitaria: Captura error MySQL distinto a 1062 al guardar y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Connection lost", errno=2013)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="Error en la base de datos:"):
        MetodoPago.guardar("Binance Pay", 1, "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: ACTUALIZACIÓN Y ELIMINACIÓN (MODELO)
# ==============================================================================

def test_unit_metodo_actualizar_exitoso(mocker):
    """Unitaria: Verifica actualización con .strip(), bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = MetodoPago.actualizar(2, "  Pago Móvil Modificado  ", 1, "Activo", "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE metodo_pago SET nombre_metodo=%s, requiere_referencia=%s, estado=%s WHERE cod_metodo=%s",
        ("Pago Móvil Modificado", 1, "Activo", 2)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=29)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_actualizar_duplicado_mysql_1062(mocker):
    """Unitaria: Captura error 1062 al actualizar a un nombre ya existente."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry", errno=1062)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="El método 'Efectivo' ya existe, intente con otro nombre."):
        MetodoPago.actualizar(2, "Efectivo", 0, "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_actualizar_error_bd_general(mocker):
    """Unitaria: Captura error MySQL distinto a 1062 al actualizar y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="SQL error", errno=1054)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="Error al actualizar:"):
        MetodoPago.actualizar(2, "Tarjeta", 1, "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_eliminar_logico_exitoso(mocker):
    """Unitaria: Verifica borrado lógico ('Inactivo'), bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = MetodoPago.eliminar(2, "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE metodo_pago SET estado = 'Inactivo' WHERE cod_metodo = %s",
        (2,)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=29)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_eliminar_error_bd_retorna_false(mocker):
    """Unitaria: Verifica retorno False, sin commit ni bitácora, y cierre ante Error MySQL."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="FK constraint", errno=1451)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = MetodoPago.eliminar(2, "12345678")

    assert resultado is False
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: OPERACIONES DE CONSULTA (MODELO)
# ==============================================================================

def test_unit_metodo_obtener_todos_exitoso(mocker):
    """Unitaria: Verifica listado ordenado, cursor dictionary=True y cierre de recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()

    metodos_ficticios = [
        {"cod_metodo": 1, "nombre_metodo": "Efectivo", "requiere_referencia": 0, "estado": "Activo"},
        {"cod_metodo": 2, "nombre_metodo": "Zelle", "requiere_referencia": 1, "estado": "Activo"}
    ]
    mock_cursor.fetchall.return_value = metodos_ficticios
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = MetodoPago.obtener_todos()

    assert resultado == metodos_ficticios
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once_with("SELECT * FROM metodo_pago ORDER BY cod_metodo ASC")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_metodo_obtener_todos_vacio(mocker):
    """Unitaria: Verifica retorno de lista vacía cuando no existen métodos registrados."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = MetodoPago.obtener_todos()

    assert resultado == []
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()