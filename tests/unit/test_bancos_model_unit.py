import pytest
from mysql.connector import Error
from models.bancos import Banco
from models.db import ConexionBD
from models.bitacora import Bitacora


# ==============================================================================
# PRUEBAS UNITARIAS: VALIDACIONES Y VALORES LÍMITE (MODELO BANCO)
# ==============================================================================

@pytest.mark.parametrize("nombre_invalido", ["", None, "   ", "A", " A "])
def test_unit_banco_guardar_nombre_invalido_o_corto_falla_sin_abrir_bd(mocker, nombre_invalido):
    """Unitaria: Rechaza nombre vacío, None, espacios o < 2 chars sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(Exception, match="Validación: El nombre del banco debe tener al menos 2 caracteres."):
        Banco.guardar(nombre_invalido, "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_banco_guardar_nombre_demasiado_largo_falla_sin_abrir_bd(mocker):
    """Unitaria (Valor límite > 50): Falla si el nombre supera 50 caracteres sin abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")
    nombre_largo = "B" * 51

    with pytest.raises(Exception, match="Validación: El nombre del banco es demasiado largo"):
        Banco.guardar(nombre_largo, "Activo", "12345678")

    espia_bd.assert_not_called()


def test_unit_banco_actualizar_validacion_falla_sin_abrir_bd(mocker):
    """Unitaria: Verifica que actualizar también valide datos antes de abrir BD."""
    espia_bd = mocker.patch.object(ConexionBD, "obtener_conexion")

    with pytest.raises(Exception, match="Validación: El nombre del banco debe tener al menos 2 caracteres."):
        Banco.actualizar(1, "X", "Activo", "12345678")

    with pytest.raises(Exception, match="Validación: El nombre del banco es demasiado largo"):
        Banco.actualizar(1, "B" * 51, "Activo", "12345678")

    espia_bd.assert_not_called()


# ==============================================================================
# PRUEBAS UNITARIAS: ESCRITURA (GUARDAR, ACTUALIZAR, ELIMINAR)
# ==============================================================================

def test_unit_banco_guardar_exitoso_y_strip(mocker):
    """Unitaria: Verifica guardado con .strip(), bitácora, commit y cierre de recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Banco.guardar("  Banco Provincial  ", "Activo", "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO banco (nombre_banco, estado) VALUES (%s, %s)",
        ("Banco Provincial", "Activo")
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=30)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


@pytest.mark.parametrize("nombre_valido", ["BD", "B" * 50])
def test_unit_banco_guardar_valores_limite_validos(mocker, nombre_valido):
    """Unitaria (Valores límite válidos): Acepta exactamente 2 y 50 caracteres."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    resultado = Banco.guardar(nombre_valido, "Activo", "12345678")

    assert resultado is True
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_guardar_duplicado_1062_lanza_excepcion(mocker):
    """Unitaria: Captura error 1062, no hace commit ni bitácora, y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry", errno=1062)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="El banco 'Banesco' ya se encuentra registrado."):
        Banco.guardar("Banesco", "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_guardar_error_bd_general(mocker):
    """Unitaria: Captura error MySQL distinto a 1062 al guardar y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Lost connection", errno=2013)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="Error en la base de datos:"):
        Banco.guardar("Banco de Venezuela", "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_actualizar_exitoso(mocker):
    """Unitaria: Verifica actualización con .strip(), bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Banco.actualizar(1, "  Mercantil Modificado  ", "Inactivo", "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE banco SET nombre_banco=%s, estado=%s WHERE cod_banco=%s",
        ("Mercantil Modificado", "Inactivo", 1)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=30)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_actualizar_duplicado_1062(mocker):
    """Unitaria: Captura error 1062 al actualizar a un nombre de banco existente."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry", errno=1062)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="El banco 'Banesco' ya existe, intente con otro nombre."):
        Banco.actualizar(1, "Banesco", "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_actualizar_error_bd_general(mocker):
    """Unitaria: Captura error SQL distinto a 1062 al actualizar y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="SQL error", errno=1054)
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    with pytest.raises(Exception, match="Error al actualizar:"):
        Banco.actualizar(1, "BNC", "Activo", "12345678")

    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_eliminar_exitoso(mocker):
    """Unitaria: Verifica borrado lógico ('Inactivo'), bitácora, commit y cierre."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Banco.eliminar(1, "12345678")

    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE banco SET estado = 'Inactivo' WHERE cod_banco = %s",
        (1,)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=30)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_eliminar_falla_retorna_false(mocker):
    """Unitaria: Retorna False si falla BD, no hace commit ni bitácora, y cierra recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Error(msg="FK constraint", errno=1451)
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Banco.eliminar(1, "12345678")

    assert resultado is False
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: CONSULTAS (MODELO BANCO)
# ==============================================================================

def test_unit_banco_obtener_todos_retorna_lista_bancos(mocker):
    """Unitaria: Verifica consulta de bancos, cursor dictionary=True y cierre de recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()

    bancos_ficticios = [
        {"cod_banco": 1, "nombre_banco": "Banesco", "estado": "Activo"},
        {"cod_banco": 2, "nombre_banco": "Mercantil", "estado": "Activo"}
    ]
    mock_cursor.fetchall.return_value = bancos_ficticios
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Banco.obtener_todos()

    assert resultado == bancos_ficticios
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once_with("SELECT * FROM banco ORDER BY cod_banco ASC")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_banco_obtener_todos_vacio(mocker):
    """Unitaria: Verifica retorno de lista vacía cuando no hay bancos registrados."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Banco.obtener_todos()

    assert resultado == []
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()