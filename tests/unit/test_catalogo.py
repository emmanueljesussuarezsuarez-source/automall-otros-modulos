from decimal import Decimal
from unittest.mock import MagicMock
from models.catalogo import Catalogo


# ==============================================================================
#   BLOQUE A: PRUEBAS UNITARIAS DEL MODELO (models/catalogo.py)
# ==============================================================================

def test_cp_cat_01_obtener_disponibles_exitoso(mock_bd):
    """CP-CAT-01: Consultar catálogo disponible invocando sp_obtener_catalogo_detallado."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        {
            "placa": "ABC123",
            "nombre_marca": "Toyota",
            "nombre_modelo": "Corolla",
            "precio": Decimal("22500.75"),
            "imagen_url": "uploads/auto1.jpg",
        }
    ]
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    disponibles = Catalogo.obtener_disponibles()

    # Assert
    mock_conexion.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.callproc.assert_called_once_with("sp_obtener_catalogo_detallado", (None, True))
    assert len(disponibles) == 1
    assert isinstance(disponibles[0]["precio"], float)
    assert disponibles[0]["precio"] == 22500.75
    assert disponibles[0]["imagenes_lista"] == ["uploads/auto1.jpg"]
    assert disponibles[0]["imagen_url"] == "uploads/auto1.jpg"
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_cat_02_obtener_disponibles_agrupa_imagenes_y_evita_duplicados(mock_bd):
    """CP-CAT-02: Agrupar múltiples fotos por placa (soportando 'imagen_url' y 'URL') sin duplicar."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        {"placa": "ABC123", "precio": Decimal("18000.00"), "imagen_url": "uploads/f1.jpg"},
        {"placa": "ABC123", "precio": Decimal("18000.00"), "URL": "uploads/f2.jpg"},
        {"placa": "ABC123", "precio": Decimal("18000.00"), "imagen_url": "uploads/f1.jpg"},
    ]
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    disponibles = Catalogo.obtener_disponibles()

    # Assert
    assert len(disponibles) == 1
    assert disponibles[0]["imagenes_lista"] == ["uploads/f1.jpg", "uploads/f2.jpg"]
    assert disponibles[0]["imagen_url"] == "uploads/f1.jpg"
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_cat_03_obtener_disponibles_precio_none_y_sin_imagen(mock_bd):
    """CP-CAT-03: Asignar precio 0.0 y portada None cuando el registro viene sin precio ni foto."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        {"placa": "XYZ999", "precio": None, "imagen_url": None, "URL": None}
    ]
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    disponibles = Catalogo.obtener_disponibles()

    # Assert
    assert len(disponibles) == 1
    assert disponibles[0]["precio"] == 0.0
    assert disponibles[0]["imagenes_lista"] == []
    assert disponibles[0]["imagen_url"] is None


def test_cp_cat_04_obtener_disponibles_sin_resultados(mock_bd):
    """CP-CAT-04: Retornar lista vacía cuando el procedimiento almacenado no devuelve filas."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    disponibles = Catalogo.obtener_disponibles()

    # Assert
    assert disponibles == []
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_cat_05_obtener_por_placa_existente(mock_bd):
    """CP-CAT-05: Consultar un vehículo específico en catálogo por placa retornando un único dict."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        {"placa": "ABC123", "precio": Decimal("19500.00"), "imagen_url": "uploads/front.jpg"}
    ]
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    vehiculo = Catalogo.obtener_por_placa("ABC123")

    # Assert
    mock_cursor.callproc.assert_called_once_with("sp_obtener_catalogo_detallado", ("ABC123", False))
    assert isinstance(vehiculo, dict)
    assert vehiculo["placa"] == "ABC123"
    assert vehiculo["precio"] == 19500.0
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_cat_06_obtener_por_placa_inexistente_retorna_none(mock_bd):
    """CP-CAT-06: Retornar None cuando la placa buscada en catálogo no existe."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_cursor.stored_results.return_value = [mock_result]

    # Act
    vehiculo = Catalogo.obtener_por_placa("NOEXISTE")

    # Assert
    assert vehiculo is None
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_cat_07_consultar_catalogo_error_bd_retorna_lista_vacia(mock_bd):
    """CP-CAT-07: Capturar excepción durante callproc, retornar [] y cerrar conexión."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.callproc.side_effect = Exception("Error en procedimiento almacenado")

    # Act
    disponibles = Catalogo.obtener_disponibles()

    # Assert
    assert disponibles == []
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
#   BLOQUE B: PRUEBAS UNITARIAS DEL CONTROLADOR (controllers/catalogo_controller.py)
# ==============================================================================

def test_cp_cat_08_ctrl_listar_catalogo_renderiza_vista_con_vehiculos(client_catalogo, monkeypatch):
    """CP-CAT-08: Endpoint GET /catalogo-ventas consulta disponibles y renderiza la plantilla."""
    # Arrange
    vehiculos_mock = [
        {"placa": "ABC123", "precio": 22500.0, "imagen_url": "uploads/auto1.jpg"}
    ]
    monkeypatch.setattr("controllers.catalogo_controller.Catalogo.obtener_disponibles", lambda: vehiculos_mock)
    mock_render = MagicMock(return_value="<html>Catalogo</html>")
    monkeypatch.setattr("controllers.catalogo_controller.render_template", mock_render)

    # Act
    respuesta = client_catalogo.get("/catalogo-ventas")

    # Assert
    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("vehiculos/catalogo_lista.html", vehiculos=vehiculos_mock)


def test_cp_cat_09_ctrl_listar_catalogo_vacio(client_catalogo, monkeypatch):
    """CP-CAT-09: Endpoint GET /catalogo-ventas renderiza correctamente cuando no hay vehículos disponibles."""
    # Arrange
    monkeypatch.setattr("controllers.catalogo_controller.Catalogo.obtener_disponibles", lambda: [])
    mock_render = MagicMock(return_value="<html>Catalogo Vacio</html>")
    monkeypatch.setattr("controllers.catalogo_controller.render_template", mock_render)

    # Act
    respuesta = client_catalogo.get("/catalogo-ventas")

    # Assert
    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("vehiculos/catalogo_lista.html", vehiculos=[])


def test_cp_cat_10_ctrl_catalogo_es_accesible_sin_sesion(client_catalogo, monkeypatch):
    """CP-CAT-10: Verificar que /catalogo-ventas permite acceso público sin requerir inicio de sesión."""
    # Arrange (sin variables en session)
    monkeypatch.setattr("controllers.catalogo_controller.Catalogo.obtener_disponibles", lambda: [])
    monkeypatch.setattr("controllers.catalogo_controller.render_template", MagicMock(return_value="<html>OK</html>"))

    # Act
    respuesta = client_catalogo.get("/catalogo-ventas")

    # Assert
    assert respuesta.status_code == 200