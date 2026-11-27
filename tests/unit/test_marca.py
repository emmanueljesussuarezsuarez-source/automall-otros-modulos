import pytest
from unittest.mock import MagicMock
from mysql.connector import Error
from models.marca import Marca


# ==============================================================================
#   BLOQUE A: PRUEBAS UNITARIAS DEL MODELO (models/marca.py)
# ==============================================================================

def test_cp_mar_01_guardar_marca_exitoso(mock_bd, monkeypatch):
    """CP-MAR-01: Guardar una marca con datos válidos y registrar en bitácora."""
    # Arrange (Preparar)
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.marca.Bitacora.registrar", mock_bitacora)

    # Act (Actuar)
    resultado = Marca.guardar("  Toyota  ", "Activo", id_usuario_sesion="12345678")

    # Assert (Verificar)
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO marca (nombre_marca, estado) VALUES (%s, %s)",
        ("Toyota", "Activo")
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=1, cod_modulo=6)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mar_02_guardar_marca_nombre_vacio(monkeypatch):
    """CP-MAR-02: Rechazar guardado si el nombre está vacío o tiene solo espacios."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.marca.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Marca.guardar("   ", "Activo", id_usuario_sesion="12345678")

    assert "Validación: El nombre de la marca debe tener al menos 2 caracteres." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mar_03_guardar_marca_nombre_menor_dos_caracteres(monkeypatch):
    """CP-MAR-03: Rechazar guardado si el nombre tiene menos de 2 caracteres (valor límite = 1)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.marca.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Marca.guardar("A", "Activo", id_usuario_sesion="12345678")

    assert "Validación: El nombre de la marca debe tener al menos 2 caracteres." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mar_04_guardar_marca_nombre_excede_50_caracteres(monkeypatch):
    """CP-MAR-04: Rechazar guardado si el nombre supera 50 caracteres (valor límite = 51)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.marca.ConexionBD.obtener_conexion", mock_conn)
    nombre_largo = "M" * 51

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Marca.guardar(nombre_largo, "Activo", id_usuario_sesion="12345678")

    assert "Validación: El nombre de la marca es demasiado largo." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mar_05_guardar_marca_duplicada_error_1062(mock_bd, monkeypatch):
    """CP-MAR-05: Capturar error MySQL 1062 cuando la marca ya existe."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry 'Toyota'", errno=1062)
    monkeypatch.setattr("models.marca.Bitacora.registrar", MagicMock())

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Marca.guardar("Toyota", "Activo", id_usuario_sesion="12345678")

    assert "La marca 'Toyota' ya está registrada." in str(exc_info.value)
    mock_conexion.commit.assert_not_called()
    mock_conexion.close.assert_called_once()


def test_cp_mar_06_actualizar_marca_exitoso(mock_bd, monkeypatch):
    """CP-MAR-06: Actualizar nombre y estado de una marca existente."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.marca.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Marca.actualizar(1, "  Honda  ", "Activo", id_usuario_sesion="12345678")

    # Assert
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE marca SET nombre_marca=%s, estado=%s WHERE cod_marca=%s",
        ("Honda", "Activo", 1)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=3, cod_modulo=6)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mar_07_actualizar_marca_nombre_invalido(monkeypatch):
    """CP-MAR-07: Rechazar actualización cuando el nombre no cumple longitud mínima."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.marca.ConexionBD.obtener_conexion", mock_conn)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Marca.actualizar(1, "X", "Activo", id_usuario_sesion="12345678")

    assert "Validación: El nombre de la marca debe tener al menos 2 caracteres." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_mar_08_eliminar_marca_logico_exitoso(mock_bd, monkeypatch):
    """CP-MAR-08: Realizar eliminado lógico cambiando el estado de la marca a 'Inactivo'."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.marca.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Marca.eliminar(5, id_usuario_sesion="12345678")

    # Assert
    assert resultado is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE marca SET estado = 'Inactivo' WHERE cod_marca = %s",
        (5,)
    )
    mock_bitacora.assert_called_once_with("12345678", cod_accion=4, cod_modulo=6)
    mock_conexion.commit.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_mar_09_eliminar_marca_error_bd_retorna_false(mock_bd):
    """CP-MAR-09: Retornar False si ocurre una excepción de MySQL durante la eliminación."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Error de conexión", errno=2013)

    # Act
    resultado = Marca.eliminar(5, id_usuario_sesion="12345678")

    # Assert
    assert resultado is False
    mock_conexion.close.assert_called_once()


def test_cp_mar_10_obtener_todas_las_marcas(mock_bd):
    """CP-MAR-10: Consultar todas las marcas cuyo estado sea distinto a 'Inactivo'."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    datos_esperados = [
        {"cod_marca": 1, "nombre_marca": "Ford", "estado": "Activo"},
        {"cod_marca": 2, "nombre_marca": "Toyota", "estado": "Activo"},
    ]
    mock_cursor.fetchall.return_value = datos_esperados

    # Act
    marcas = Marca.obtener_todas()

    # Assert
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM marca WHERE estado != 'Inactivo' ORDER BY nombre_marca ASC"
    )
    assert marcas == datos_esperados
    mock_conexion.close.assert_called_once()


def test_cp_mar_11_obtener_marcas_activas(mock_bd):
    """CP-MAR-11: Consultar únicamente las marcas con estado 'Activo'."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    datos_esperados = [{"cod_marca": 2, "nombre_marca": "Toyota", "estado": "Activo"}]
    mock_cursor.fetchall.return_value = datos_esperados

    # Act
    marcas = Marca.obtener_activas()

    # Assert
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM marca WHERE estado = 'Activo' ORDER BY nombre_marca ASC"
    )
    assert marcas == datos_esperados
    mock_conexion.close.assert_called_once()


# ==============================================================================
#   BLOQUE B: PRUEBAS UNITARIAS DEL CONTROLADOR (controllers/marca_controller.py)
# ==============================================================================

def test_cp_mar_12_ctrl_registro_marca_post_exitoso(client_marca, monkeypatch):
    """CP-MAR-12: Endpoint POST /marcas/registro retorna JSON 200 al crear marca válida."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.marca_controller.Marca.guardar", MagicMock(return_value=True))
    monkeypatch.setattr(
        "controllers.marca_controller.Marca.obtener_todas",
        lambda: [{"cod_marca": 10, "nombre_marca": "Mazda", "estado": "Activo"}]
    )
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.marca_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_marca.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_marca.post("/marcas/registro", data={"nombre_marca": "Mazda", "estado": "Activo"})
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    assert datos["cod_marca"] == 10
    assert datos["nombre_marca"] == "Mazda"
    mock_notif.assert_called_once()


def test_cp_mar_13_ctrl_registro_marca_post_error_devuelve_400(client_marca, monkeypatch):
    """CP-MAR-13: Endpoint POST /marcas/registro retorna JSON 400 cuando falla la validación."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr(
        "controllers.marca_controller.Marca.guardar",
        MagicMock(side_effect=Exception("Validación: El nombre de la marca debe tener al menos 2 caracteres."))
    )

    with client_marca.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_marca.post("/marcas/registro", data={"nombre_marca": "A"})
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 400
    assert datos["status"] == "error"
    assert "al menos 2 caracteres" in datos["message"]


def test_cp_mar_14_ctrl_editar_marca_post_exitoso(client_marca, monkeypatch):
    """CP-MAR-14: Endpoint POST /marcas/editar/<id> actualiza la marca y retorna JSON 200."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    mock_actualizar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.marca_controller.Marca.actualizar", mock_actualizar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.marca_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_marca.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_marca.post("/marcas/editar/3", data={"nombre_marca": "Chevrolet", "estado": "Activo"})
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    mock_actualizar.assert_called_once_with(3, "Chevrolet", "Activo", "12345678")
    mock_notif.assert_called_once()


def test_cp_mar_15_ctrl_eliminar_marca_post_exitoso(client_marca, monkeypatch):
    """CP-MAR-15: Endpoint POST /marcas/eliminar/<id> inactiva la marca y retorna JSON 200."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    mock_eliminar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.marca_controller.Marca.eliminar", mock_eliminar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.marca_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_marca.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "12345678"

    # Act
    respuesta = client_marca.post("/marcas/eliminar/3")
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    mock_eliminar.assert_called_once_with(3, "12345678")
    mock_notif.assert_called_once()


def test_cp_mar_16_ctrl_sin_sesion_redirige_a_login(client_marca):
    """CP-MAR-16: Acceso a /marcas/registro sin sesión activa redirige al login (302)."""
    # Arrange (sesión vacía)

    # Act
    respuesta = client_marca.get("/marcas/registro")

    # Assert
    assert respuesta.status_code == 302
    assert "/login" in respuesta.location