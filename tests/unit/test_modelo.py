import pytest
from unittest.mock import MagicMock
from mysql.connector import Error
from models.modelo import Modelo


# ==============================================================================
#   BLOQUE A: PRUEBAS UNITARIAS DEL MODELO (models/modelo.py)
# ==============================================================================

def test_cp_mod_01_guardar_modelo_exitoso(mock_bd, monkeypatch):
    """CP-MOD-01: Guardar un modelo válido asociado a una marca y registrar en bitácora."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.modelo.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Modelo.guardar("  Corolla  ", "Activo", cod_marca=1, id_usuario_sesion="12345678")

    # Assert
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO modelo (nombre_modelo, estado, cod_marca) VALUES (%s, %s, %s)",
        ("Corolla", "Activo", 1)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=7)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mod_02_guardar_modelo_nombre_vacio(monkeypatch):
    """CP-MOD-02: Rechazar guardado cuando el nombre del modelo está vacío o en blanco."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.modelo.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.guardar("   ", "Activo", cod_marca=1, id_usuario_sesion="12345678")

    assert "Validación: El nombre del modelo no puede estar vacío." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mod_03_guardar_modelo_marca_invalida(monkeypatch):
    """CP-MOD-03: Rechazar guardado cuando cod_marca es inválido (0 o menor)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.modelo.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.guardar("Corolla", "Activo", cod_marca=0, id_usuario_sesion="12345678")

    assert "Validación: Debe seleccionar una marca válida." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mod_04_guardar_modelo_nombre_excede_50_caracteres(monkeypatch):
    """CP-MOD-04: Rechazar guardado cuando el nombre supera los 50 caracteres (límite = 51)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.modelo.ConexionBD.obtener_conexion", mock_conn)
    nombre_largo = "X" * 51

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.guardar(nombre_largo, "Activo", cod_marca=1, id_usuario_sesion="12345678")

    assert "Validación: El nombre del modelo es demasiado largo." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mod_05_guardar_modelo_duplicado_error_1062(mock_bd, monkeypatch):
    """CP-MOD-05: Capturar error MySQL 1062 cuando el modelo ya existe para esa marca."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry 'Corolla'", errno=1062)
    monkeypatch.setattr("models.modelo.Bitacora.registrar", MagicMock())

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.guardar("Corolla", "Activo", cod_marca=1, id_usuario_sesion="12345678")

    assert "El modelo 'Corolla' ya existe para esta marca." in str(exc_info.value)
    mock_conexion.commit.assert_not_called()
    mock_conexion.close.assert_called_once()


def test_cp_mod_06_guardar_modelo_error_bd_generico(mock_bd, monkeypatch):
    """CP-MOD-06: Capturar error genérico de MySQL al guardar y cerrar conexión."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Connection lost", errno=2013)
    monkeypatch.setattr("models.modelo.Bitacora.registrar", MagicMock())

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.guardar("Corolla", "Activo", cod_marca=1, id_usuario_sesion="12345678")

    assert "Error en la base de datos:" in str(exc_info.value)
    mock_conexion.commit.assert_not_called()
    mock_conexion.close.assert_called_once()


def test_cp_mod_07_actualizar_modelo_exitoso(mock_bd, monkeypatch):
    """CP-MOD-07: Actualizar nombre, estado y marca de un modelo existente."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.modelo.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Modelo.actualizar(2, "  Civic  ", "Activo", cod_marca=3, id_usuario_sesion="12345678")

    # Assert
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE modelo SET nombre_modelo=%s, estado=%s, cod_marca=%s WHERE cod_modelo=%s",
        ("Civic", "Activo", 3, 2)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=7)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mod_08_actualizar_modelo_marca_invalida(monkeypatch):
    """CP-MOD-08: Rechazar actualización si cod_marca es negativo o inválido."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.modelo.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Modelo.actualizar(2, "Civic", "Activo", cod_marca=-1, id_usuario_sesion="12345678")

    assert "Validación: Debe seleccionar una marca válida." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mod_09_eliminar_modelo_logico_exitoso(mock_bd, monkeypatch):
    """CP-MOD-09: Realizar eliminado lógico cambiando estado del modelo a 'Inactivo'."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.modelo.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Modelo.eliminar(4, id_usuario_sesion="12345678")

    # Assert
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE modelo SET estado = 'Inactivo' WHERE cod_modelo = %s",
        (4,)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=7)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mod_10_eliminar_modelo_error_bd_retorna_false(mock_bd):
    """CP-MOD-10: Retornar False si ocurre una excepción de MySQL al eliminar."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Error de conexión", errno=2013)

    # Act
    resultado = Modelo.eliminar(4, id_usuario_sesion="12345678")

    # Assert
    assert resultado is False
    mock_conexion.close.assert_called_once()


def test_cp_mod_11_obtener_todos_los_modelos(mock_bd):
    """CP-MOD-11: Consultar todos los modelos no inactivos con JOIN a la tabla marca."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    datos_esperados = [
        {"cod_modelo": 1, "nombre_modelo": "Corolla", "estado": "Activo", "cod_marca": 1, "nombre_marca": "Toyota"},
        {"cod_modelo": 2, "nombre_modelo": "Civic", "estado": "Activo", "cod_marca": 2, "nombre_marca": "Honda"},
    ]
    mock_cursor.fetchall.return_value = datos_esperados

    # Act
    modelos = Modelo.obtener_todas()

    # Assert
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once()
    sql_ejecutado = mock_cursor.execute.call_args[0][0]
    assert "INNER JOIN marca ma ON m.cod_marca = ma.cod_marca" in sql_ejecutado
    assert "WHERE m.estado != 'Inactivo'" in sql_ejecutado
    assert modelos == datos_esperados
    mock_conexion.close.assert_called_once()


def test_cp_mod_12_obtener_modelos_por_marca(mock_bd):
    """CP-MOD-12: Consultar modelos activos filtrados por cod_marca."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    datos_esperados = [{"cod_modelo": 1, "nombre_modelo": "Corolla", "estado": "Activo", "cod_marca": 1}]
    mock_cursor.fetchall.return_value = datos_esperados

    # Act
    modelos = Modelo.obtener_por_marca(1)

    # Assert
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM modelo WHERE cod_marca = %s AND estado = 'Activo' AND estado != 'Inactivo'",
        (1,)
    )
    assert modelos == datos_esperados
    mock_conexion.close.assert_called_once()


# ==============================================================================
#   BLOQUE B: PRUEBAS UNITARIAS DEL CONTROLADOR (controllers/modelo_controller.py)
# ==============================================================================

def test_cp_mod_13_ctrl_registro_modelo_post_exitoso(client_modelo, monkeypatch):
    """CP-MOD-13: Endpoint POST /modelos/registro retorna JSON 200 al registrar modelo válido."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.modelo_controller.Modelo.guardar", MagicMock(return_value=True))
    monkeypatch.setattr(
        "controllers.modelo_controller.Modelo.obtener_por_marca",
        lambda cod_marca: [{"cod_modelo": 15, "nombre_modelo": "Corolla", "cod_marca": 1}]
    )
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.modelo_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_modelo.post(
        "/modelos/registro",
        data={"nombre_modelo": "Corolla", "estado": "Activo", "cod_marca": "1"}
    )
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    assert datos["cod_modelo"] == 15
    assert datos["nombre_modelo"] == "Corolla"
    assert datos["cod_marca"] == "1"
    mock_notif.assert_called_once()


def test_cp_mod_14_ctrl_registro_modelo_post_error_400(client_modelo, monkeypatch):
    """CP-MOD-14: Endpoint POST /modelos/registro retorna JSON 400 ante fallo de validación."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr(
        "controllers.modelo_controller.Modelo.guardar",
        MagicMock(side_effect=Exception("Validación: Debe seleccionar una marca válida."))
    )

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_modelo.post(
        "/modelos/registro",
        data={"nombre_modelo": "Corolla", "cod_marca": "0"}
    )
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 400
    assert datos["status"] == "error"
    assert "marca válida" in datos["message"]


def test_cp_mod_15_ctrl_registro_modelo_get_renderiza_vista(client_modelo, monkeypatch):
    """CP-MOD-15: Endpoint GET /modelos/registro obtiene modelos y marcas activas y renderiza la vista."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    modelos_mock = [{"cod_modelo": 1, "nombre_modelo": "Corolla"}]
    marcas_mock = [{"cod_marca": 1, "nombre_marca": "Toyota"}]
    monkeypatch.setattr("controllers.modelo_controller.Modelo.obtener_todas", lambda: modelos_mock)
    monkeypatch.setattr("controllers.modelo_controller.Marca.obtener_activas", lambda: marcas_mock)
    mock_render = MagicMock(return_value="<html>Vista Modelos</html>")
    monkeypatch.setattr("controllers.modelo_controller.render_template", mock_render)

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 1

    # Act
    respuesta = client_modelo.get("/modelos/registro")

    # Assert
    assert respuesta.status_code == 200
    mock_render.assert_called_once_with(
        "vehiculos/modelo_registro.html",
        modelos=modelos_mock,
        marcas=marcas_mock
    )


def test_cp_mod_16_ctrl_editar_modelo_post_exitoso(client_modelo, monkeypatch):
    """CP-MOD-16: Endpoint POST /modelos/editar/<id> actualiza el modelo y retorna JSON 200."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    mock_actualizar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.modelo_controller.Modelo.actualizar", mock_actualizar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.modelo_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_modelo.post(
        "/modelos/editar/2",
        data={"nombre_modelo": "Yaris", "estado": "Activo", "cod_marca": "1"}
    )
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    mock_actualizar.assert_called_once_with(2, "Yaris", "Activo", "1", "12345678")
    mock_notif.assert_called_once()


def test_cp_mod_17_ctrl_eliminar_modelo_post_exitoso(client_modelo, monkeypatch):
    """CP-MOD-17: Endpoint POST /modelos/eliminar/<id> inactiva el modelo y retorna JSON 200."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    mock_eliminar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.modelo_controller.Modelo.eliminar", mock_eliminar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.modelo_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_modelo.post("/modelos/eliminar/2")
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    mock_eliminar.assert_called_once_with(2, "12345678")
    mock_notif.assert_called_once()


def test_cp_mod_18_ctrl_sin_permiso_redirige_a_index(client_modelo, monkeypatch):
    """CP-MOD-18: Usuario autenticado sin permiso 'p_crear' es redirigido al inicio (302)."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: False)

    with client_modelo.session_transaction() as sess:
        sess["cod_rol"] = 3

    # Act
    respuesta = client_modelo.get("/modelos/registro")

    # Assert
    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/")