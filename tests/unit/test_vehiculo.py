import pytest
from datetime import date
from unittest.mock import MagicMock, PropertyMock
from mysql.connector import Error
from models.vehiculo import Vehiculo


# ==============================================================================
#   DATOS BASE REUTILIZABLES PARA PRUEBAS DE VEHÍCULO
# ==============================================================================

def _datos_vehiculo_validos():
    v_data = {
        "placa": "  abc123  ",
        "color": "Negro",
        "anio": 2023,
        "kilometraje": 15000,
        "cod_tipo": 1,
        "estado": "Disponible",
        "modelo": 2,
        "cedula": "12345678",
    }
    d_data = {
        "original_totalPropiedad": 1,
        "experticia_transito": 1,
        "certificado_origen": 1,
        "carnet_circulacion": 1,
        "reserva_dominio": 0,
        "garantia_vehiculo": 0,
        "certificado_garantia": 0,
        "manual_vehiculoGarantia": 1,
        "finiquito": 0,
        "resguardo": 0,
        "seguro": 1,
        "factura_compra": 1,
        "fecha_ingreso": "2026-11-18",
        "otro_documento": "Ninguno",
    }
    a_data = {"copia_llaves": 1, "repuesto": 1, "triangulo": 1}
    c_data = {"estado": "Activo", "precio": 18500.00, "descripcion": "Excelente estado"}
    return v_data, d_data, a_data, c_data


# ==============================================================================
#   BLOQUE A: PRUEBAS UNITARIAS DEL MODELO (models/vehiculo.py)
# ==============================================================================

def test_cp_veh_01_guardar_vehiculo_con_documentos_exitoso(mock_bd, monkeypatch):
    """CP-VEH-01: Guardar vehículo completo (documentación, accesorios, catálogo, imágenes, historial y bitácora)."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    type(mock_cursor).lastrowid = PropertyMock(side_effect=[10, 20])
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.vehiculo.Bitacora.registrar", mock_bitacora)

    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    filenames = ["foto1.jpg", "foto2.jpg"]

    # Act
    resultado = Vehiculo.guardar_con_documentos(
        v_data, d_data, a_data, c_data, filenames, id_usuario_sesion="99887766"
    )

    # Assert
    assert resultado is True
    assert c_data["fecha_pub"] == "2026-11-18"
    # 1 doc + 1 acc + 1 veh + 1 historial + 1 catalogo + 2 imagenes = 7 executes
    assert mock_cursor.execute.call_count == 7
    # Verificar que la placa se normalizó a mayúsculas sin espacios en el INSERT de vehiculo
    params_vehiculo = mock_cursor.execute.call_args_list[2][0][1]
    assert params_vehiculo[0] == "ABC123"
    assert params_vehiculo[8] == 10  # cod_documento
    assert params_vehiculo[9] == 20  # cod_accesorio
    mock_bitacora.assert_called_once_with("99887766", cod_accion=1, cod_modulo=2)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_02_guardar_vehiculo_placa_menor_5_caracteres(monkeypatch):
    """CP-VEH-02: Rechazar guardado cuando la placa tiene menos de 5 caracteres."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["placa"] = "AB12"

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: La placa debe tener al menos 5 caracteres." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_03_guardar_vehiculo_anio_inferior_1900(monkeypatch):
    """CP-VEH-03: Rechazar guardado cuando el año es menor al límite inferior (1899)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["anio"] = 1899

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: El año es inválido" in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_04_guardar_vehiculo_anio_superior_limite(monkeypatch):
    """CP-VEH-04: Rechazar guardado cuando el año supera el límite (año actual + 1)."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["anio"] = date.today().year + 2

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: El año es inválido" in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_05_guardar_vehiculo_kilometraje_negativo(monkeypatch):
    """CP-VEH-05: Rechazar guardado cuando el kilometraje es negativo."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["kilometraje"] = -10

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: El kilometraje no puede ser un número negativo." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_06_guardar_vehiculo_precio_cero(monkeypatch):
    """CP-VEH-06: Rechazar guardado cuando el precio es menor o igual a cero."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    c_data["precio"] = 0

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: El precio debe ser un monto mayor a cero." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_07_guardar_vehiculo_sin_cedula_propietario(monkeypatch):
    """CP-VEH-07: Rechazar guardado si falta la cédula del propietario o el modelo."""
    # Arrange
    mock_conn = MagicMock()
    monkeypatch.setattr("models.vehiculo.ConexionBD.obtener_conexion", mock_conn)
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["cedula"] = ""

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "Validación: La cédula del propietario y el modelo son obligatorios." in str(exc_info.value)
    mock_conn.assert_not_called()


def test_cp_veh_08_guardar_vehiculo_placa_duplicada_error_1062(mock_bd, monkeypatch):
    """CP-VEH-08: Ejecutar rollback y capturar error MySQL 1062 cuando la placa ya existe."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Error(msg="Duplicate entry 'ABC123'", errno=1062)
    monkeypatch.setattr("models.vehiculo.Bitacora.registrar", MagicMock())
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        Vehiculo.guardar_con_documentos(v_data, d_data, a_data, c_data, [], "99887766")

    assert "ya se encuentra registrada." in str(exc_info.value)
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_09_actualizar_vehiculo_completo_exitoso(mock_bd, monkeypatch):
    """CP-VEH-09: Actualizar vehículo con cambio de placa, eliminación física de foto y nuevas imágenes."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.fetchone.return_value = {"cod_documento": 10, "cod_accesorio": 20}
    mock_bitacora = MagicMock()
    mock_remove = MagicMock()
    monkeypatch.setattr("models.vehiculo.Bitacora.registrar", mock_bitacora)
    monkeypatch.setattr("models.vehiculo.os.path.exists", lambda path: True)
    monkeypatch.setattr("models.vehiculo.os.remove", mock_remove)

    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()
    v_data["placa"] = "xyz789"

    # Act
    resultado = Vehiculo.actualizar(
        "ABC123", v_data, d_data, a_data, c_data,
        id_usuario_sesion="99887766",
        nuevas_imagenes=["nueva1.jpg"],
        imagenes_eliminar=["uploads/vieja.jpg"]
    )

    # Assert
    assert resultado is True
    mock_remove.assert_called_once()
    mock_bitacora.assert_called_once_with("99887766", cod_accion=3, cod_modulo=2)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_10_actualizar_vehiculo_inexistente_retorna_false(mock_bd):
    """CP-VEH-10: Retornar False si la placa original no existe al intentar actualizar."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.fetchone.return_value = None
    v_data, d_data, a_data, c_data = _datos_vehiculo_validos()

    # Act
    resultado = Vehiculo.actualizar("NOEXISTE", v_data, d_data, a_data, c_data, "99887766")

    # Assert
    assert resultado is False
    mock_conexion.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_11_eliminar_vehiculo_logico_exitoso(mock_bd, monkeypatch):
    """CP-VEH-11: Inactivar lógicamente el vehículo, registrar historial y bitácora."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_bitacora = MagicMock()
    monkeypatch.setattr("models.vehiculo.Bitacora.registrar", mock_bitacora)

    # Act
    resultado = Vehiculo.eliminar("ABC123", id_usuario_sesion="99887766")

    # Assert
    assert resultado is True
    assert mock_cursor.execute.call_count == 2  # UPDATE vehiculo + INSERT historia_estado_vehiculo
    mock_bitacora.assert_called_once_with("99887766", cod_accion=4, cod_modulo=2)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_12_eliminar_vehiculo_error_bd_retorna_false(mock_bd):
    """CP-VEH-12: Hacer rollback y retornar False si ocurre excepción durante eliminación."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.execute.side_effect = Exception("Fallo SQL")

    # Act
    resultado = Vehiculo.eliminar("ABC123", id_usuario_sesion="99887766")

    # Assert
    assert resultado is False
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_cp_veh_13_obtener_todos_agrupa_multiples_imagenes_por_placa(mock_bd):
    """CP-VEH-13: Agrupar filas repetidas por placa en una sola entrada con galería imagenes_lista."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.fetchall.return_value = [
        {"placa": "ABC123", "nombre_marca": "Toyota", "imagen_url": "uploads/f1.jpg"},
        {"placa": "ABC123", "nombre_marca": "Toyota", "imagen_url": "uploads/f2.jpg"},
        {"placa": "DEF456", "nombre_marca": "Ford", "imagen_url": None},
    ]

    # Act
    vehiculos = Vehiculo.obtener_todos()

    # Assert
    assert len(vehiculos) == 2
    assert vehiculos[0]["placa"] == "ABC123"
    assert vehiculos[0]["imagenes_lista"] == ["uploads/f1.jpg", "uploads/f2.jpg"]
    assert vehiculos[0]["imagen_url"] == "uploads/f1.jpg"
    assert vehiculos[1]["imagenes_lista"] == []
    assert vehiculos[1]["imagen_url"] is None
    mock_conexion.close.assert_called_once()


def test_cp_veh_14_obtener_por_placa_con_galeria(mock_bd):
    """CP-VEH-14: Consultar detalle de un vehículo por placa incluyendo su lista de imágenes."""
    # Arrange
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.fetchone.return_value = {"placa": "ABC123", "color": "Negro", "precio": 18500}
    mock_cursor.fetchall.return_value = [{"URL": "uploads/f1.jpg"}, {"URL": "uploads/f2.jpg"}]

    # Act
    vehiculo = Vehiculo.obtener_por_placa("ABC123")

    # Assert
    assert vehiculo is not None
    assert vehiculo["imagen_url"] == "uploads/f1.jpg"
    assert len(vehiculo["imagenes"]) == 2
    mock_conexion.close.assert_called_once()


def test_cp_veh_15_buscar_por_placa_disponible_convierte_precio_float(mock_bd):
    """CP-VEH-15: Buscar vehículo disponible por placa convirtiendo precio Decimal a float."""
    # Arrange
    from decimal import Decimal
    mock_conexion, mock_cursor = mock_bd
    mock_cursor.fetchone.return_value = {
        "placa": "ABC123", "marca": "Toyota", "modelo": "Corolla",
        "anio": 2023, "color": "Negro", "tipo": "Sedan",
        "precio": Decimal("18500.50"), "estado": "Activo"
    }

    # Act
    resultado = Vehiculo.buscar_por_placa("  abc123  ")

    # Assert
    assert resultado["exito"] is True
    assert isinstance(resultado["vehiculo"]["precio"], float)
    assert resultado["vehiculo"]["precio"] == 18500.50
    mock_cursor.execute.assert_called_once()
    assert mock_cursor.execute.call_args[0][1] == ("ABC123",)
    mock_conexion.close.assert_called_once()


# ==============================================================================
#   BLOQUE B: PRUEBAS UNITARIAS DEL CONTROLADOR (controllers/vehiculos_controller.py)
# ==============================================================================

def test_cp_veh_16_ctrl_lista_vehiculos_renderiza_vista(client_vehiculos, monkeypatch):
    """CP-VEH-16: Endpoint GET /vehiculos-lista renderiza la lista de vehículos."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    vehiculos_mock = [{"placa": "ABC123", "color": "Negro"}]
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.obtener_todos", lambda: vehiculos_mock)
    mock_render = MagicMock(return_value="<html>Lista Vehiculos</html>")
    monkeypatch.setattr("controllers.vehiculos_controller.render_template", mock_render)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1

    # Act
    respuesta = client_vehiculos.get("/vehiculos-lista")

    # Assert
    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("vehiculos/lista.html", vehiculos=vehiculos_mock)


def test_cp_veh_17_ctrl_registro_vehiculo_post_exitoso(client_vehiculos, monkeypatch):
    """CP-VEH-17: Endpoint POST /vehiculos-registrar registra vehículo y notifica al staff."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.vehiculos_controller.os.path.exists", lambda p: True)
    mock_guardar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.guardar_con_documentos", mock_guardar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.vehiculos_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "99887766"

    form_data = {
        "placa": "ABC123", "color": "Negro", "anio": "2023",
        "kilometraje": "15000", "tipo": "1", "estado": "Disponible",
        "modelo": "2", "cedula": "12345678", "precio": "18500",
        "descripcion_catalogo": "Impecable", "fecha_ingreso": "2026-11-18",
        "copia_llaves": "on", "original_totalPropiedad": "on"
    }

    # Act
    respuesta = client_vehiculos.post("/vehiculos-registrar", data=form_data)
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    mock_guardar.assert_called_once()
    kwargs_notif = mock_notif.call_args.kwargs["notificacion_staff"]
    assert kwargs_notif["roles"] == [1, 2, 3, 5]


def test_cp_veh_18_ctrl_registro_vehiculo_post_error_400(client_vehiculos, monkeypatch):
    """CP-VEH-18: Endpoint POST /vehiculos-registrar retorna HTTP 400 si falla validación."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.vehiculos_controller.os.path.exists", lambda p: True)
    monkeypatch.setattr(
        "controllers.vehiculos_controller.Vehiculo.guardar_con_documentos",
        MagicMock(side_effect=Exception("Validación: La placa debe tener al menos 5 caracteres."))
    )

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "99887766"

    form_data = {
        "placa": "AB1", "color": "Negro", "anio": "2023",
        "kilometraje": "15000", "tipo": "1", "estado": "Disponible",
        "modelo": "2", "cedula": "12345678", "precio": "18500",
        "descripcion_catalogo": "Impecable", "fecha_ingreso": "2026-11-18"
    }

    # Act
    respuesta = client_vehiculos.post("/vehiculos-registrar", data=form_data)
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 400
    assert datos["status"] == "error"
    assert "al menos 5 caracteres" in datos["message"]


def test_cp_veh_19_ctrl_editar_vehiculo_cambio_estado_notifica_staff(client_vehiculos, monkeypatch):
    """CP-VEH-19: Endpoint POST /vehiculos-editar/<placa> con cambio de estado notifica a roles [1, 2, 3, 5]."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.vehiculos_controller.os.path.exists", lambda p: True)
    monkeypatch.setattr(
        "controllers.vehiculos_controller.Vehiculo.obtener_por_placa",
        lambda placa: {"placa": placa, "estado": "Disponible"}
    )
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.actualizar", MagicMock(return_value=True))
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.vehiculos_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "99887766"

    form_data = {
        "placa": "ABC123", "color": "Negro", "anio": "2023",
        "kilometraje": "15000", "tipo": "1", "estado": "Reservado",
        "modelo": "2", "cedula": "12345678", "precio": "18500",
        "descripcion_catalogo": "Actualizado", "fecha_ingreso": "2026-11-18"
    }

    # Act
    respuesta = client_vehiculos.post("/vehiculos-editar/ABC123", data=form_data)
    datos = respuesta.get_json()

    # Assert
    assert respuesta.status_code == 200
    assert datos["status"] == "success"
    kwargs_notif = mock_notif.call_args.kwargs["notificacion_staff"]
    assert kwargs_notif["roles"] == [1, 2, 3, 5]
    assert kwargs_notif["titulo"] == "Cambio de Estado de Vehículo"


def test_cp_veh_20_ctrl_editar_vehiculo_sin_cambio_estado_notifica_admin(client_vehiculos, monkeypatch):
    """CP-VEH-20: Endpoint POST /vehiculos-editar/<placa> sin cambio de estado notifica solo a roles [1, 2]."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    monkeypatch.setattr("controllers.vehiculos_controller.os.path.exists", lambda p: True)
    monkeypatch.setattr(
        "controllers.vehiculos_controller.Vehiculo.obtener_por_placa",
        lambda placa: {"placa": placa, "estado": "Disponible"}
    )
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.actualizar", MagicMock(return_value=True))
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.vehiculos_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "99887766"

    form_data = {
        "placa": "ABC123", "color": "Azul", "anio": "2023",
        "kilometraje": "15500", "tipo": "1", "estado": "Disponible",
        "modelo": "2", "cedula": "12345678", "precio": "18000",
        "descripcion_catalogo": "Mismo estado", "fecha_ingreso": "2026-11-18"
    }

    # Act
    respuesta = client_vehiculos.post("/vehiculos-editar/ABC123", data=form_data)

    # Assert
    assert respuesta.status_code == 200
    kwargs_notif = mock_notif.call_args.kwargs["notificacion_staff"]
    assert kwargs_notif["roles"] == [1, 2]
    assert kwargs_notif["titulo"] == "Vehículo Actualizado"


def test_cp_veh_21_ctrl_eliminar_vehiculo_redirige_lista(client_vehiculos, monkeypatch):
    """CP-VEH-21: Endpoint POST /vehiculos-eliminar/<placa> inactiva y redirige a /vehiculos-lista."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    mock_eliminar = MagicMock(return_value=True)
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.eliminar", mock_eliminar)
    mock_notif = MagicMock()
    monkeypatch.setattr("controllers.vehiculos_controller.NotificacionManager.crear_multiple", mock_notif)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1
        sess["cedula_usuario"] = "99887766"

    # Act
    respuesta = client_vehiculos.post("/vehiculos-eliminar/ABC123")

    # Assert
    assert respuesta.status_code == 302
    assert "/vehiculos-lista" in respuesta.location
    mock_eliminar.assert_called_once_with("ABC123", "99887766")
    mock_notif.assert_called_once()


def test_cp_veh_22_ctrl_historial_vehiculos_renderiza_vista(client_vehiculos, monkeypatch):
    """CP-VEH-22: Endpoint GET /vehiculos-historial consulta logs y renderiza historial."""
    # Arrange
    monkeypatch.setattr("utils.permisos.Permiso.verificar_acceso", lambda *args: True)
    logs_mock = [{"placa": "ABC123", "estado": "Disponible"}]
    monkeypatch.setattr("controllers.vehiculos_controller.Vehiculo.obtener_historial_completo", lambda: logs_mock)
    mock_render = MagicMock(return_value="<html>Historial</html>")
    monkeypatch.setattr("controllers.vehiculos_controller.render_template", mock_render)

    with client_vehiculos.session_transaction() as sess:
        sess["cod_rol"] = 1

    # Act
    respuesta = client_vehiculos.get("/vehiculos-historial")

    # Assert
    assert respuesta.status_code == 200
    mock_render.assert_called_once_with("vehiculos/historial_lista.html", logs=logs_mock)