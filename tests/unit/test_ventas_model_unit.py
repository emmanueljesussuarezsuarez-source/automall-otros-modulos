from decimal import Decimal
import pytest
from models.ventas import Ventas
from models.db import ConexionBD
from models.bitacora import Bitacora


# ==============================================================================
# PRUEBAS UNITARIAS: INICIALIZACIÓN Y GETTERS (MODELO VENTAS)
# ==============================================================================

def test_unit_ventas_inicializacion_y_getters():
    """Unitaria: Verifica que el constructor mapee y convierta correctamente los tipos de datos."""
    data = {
        'cedula_cliente': 'V-12345678',
        'placa': 'ABC123A',
        'tipo_venta': 'Contado',
        'poder': True,
        'traspaso_papel': False,
        'monto_recibido': '1500.50',
        'precio_vehiculo': '3000',
        'deuda_pendiente': '1499.50',
        'fecha_vencimiento': '2026-12-31',
        'cod_metodo': 1,
        'cod_moneda': 1,
        'cod_banco': 2,
        'cod_mon_digital': 3,
        'referencia': 'REF12345'
    }

    venta = Ventas(data)

    assert venta.cedula_cliente == 'V-12345678'
    assert venta.placa == 'ABC123A'
    assert venta.tipo_venta == 'Contado'
    assert venta.poder == 1
    assert venta.traspaso_papel == 0
    assert venta.monto_recibido == 1500.50
    assert venta.precio_total == 3000.0
    assert venta.deuda_pendiente == 1499.50
    assert venta.fecha_vencimiento == '2026-12-31'
    assert venta.cod_metodo == 1
    assert venta.cod_moneda == 1
    assert venta.cod_banco == 2
    assert venta.cod_mon_digital == 3
    assert venta.referencia == 'REF12345'


def test_unit_ventas_inicializacion_valores_por_defecto_y_typo_refencia():
    """Unitaria: Verifica valores por defecto y respaldo para la clave alternativa 'refencia'."""
    venta = Ventas({'refencia': 'REF-ALT-99'})

    assert venta.cedula_cliente is None
    assert venta.placa is None
    assert venta.poder == 0
    assert venta.traspaso_papel == 0
    assert venta.monto_recibido == 0.0
    assert venta.precio_total == 0.0
    assert venta.deuda_pendiente == 0.0
    assert venta.referencia == 'REF-ALT-99'


# ==============================================================================
# PRUEBAS UNITARIAS: CONSULTAS DE CATÁLOGOS Y BÚSQUEDAS (MODELO VENTAS)
# ==============================================================================

def test_unit_ventas_obtener_bancos(mocker):
    """Unitaria: Verifica la obtención del catálogo de bancos y cierre de recursos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    bancos_ficticios = [{"cod_banco": 1, "nombre_banco": "Banesco"}]

    mock_cursor.fetchall.return_value = bancos_ficticios
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.obtener_bancos()

    assert resultado == bancos_ficticios
    mock_cursor.execute.assert_called_once_with("SELECT * FROM banco")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_metodos_pago(mocker):
    """Unitaria: Verifica la obtención del catálogo de métodos de pago."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    metodos_ficticios = [{"cod_metodo": 2, "nombre": "Efectivo"}]

    mock_cursor.fetchall.return_value = metodos_ficticios
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.obtener_metodos_pago()

    assert resultado == metodos_ficticios
    mock_cursor.execute.assert_called_once_with("SELECT * FROM metodo_pago")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_monedas(mocker):
    """Unitaria: Verifica la obtención del catálogo de monedas."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    monedas_ficticias = [{"cod_moneda": 1, "nombre": "USD"}]

    mock_cursor.fetchall.return_value = monedas_ficticias
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.obtener_monedas()

    assert resultado == monedas_ficticias
    mock_cursor.execute.assert_called_once_with("SELECT * FROM moneda")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_moneda_digital(mocker):
    """Unitaria: Verifica la obtención del catálogo de monedas digitales."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    digitales_ficticias = [{"cod_mon_digital": 1, "nombre": "Zelle"}]

    mock_cursor.fetchall.return_value = digitales_ficticias
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.obtener_moneda_digital()

    assert resultado == digitales_ficticias
    mock_cursor.execute.assert_called_once_with("SELECT * FROM moneda_digital")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_clientes(mocker):
    """Unitaria: Verifica la obtención de clientes desde la base de seguridad."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    clientes_ficticios = [{"cedula_usuario": "V-1111", "nombre": "Ana"}]

    mock_cursor.fetchall.return_value = clientes_ficticios
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion)

    resultado = Ventas.obtener_clientes()

    assert resultado == clientes_ficticios
    mock_cursor.execute.assert_called_once_with("SELECT cedula_usuario, nombre, apellido FROM t_usuario")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_buscar_por_placa_encontrado_y_normalizado(mocker):
    """Unitaria: Verifica normalización de placa y conversión de precio Decimal a float."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    vehiculo_ficticio = {
        "placa": "XYZ987", "marca": "Toyota", "modelo": "Corolla",
        "anio": 2022, "color": "Rojo", "tipo": "Sedán", "precio": Decimal("18500.50"),
        "estado": "Disponible", "foto": "url_foto"
    }

    mock_cursor.fetchone.return_value = vehiculo_ficticio
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.buscar_por_placa("  xyz987  ")

    assert resultado["exito"] is True
    assert resultado["vehiculo"]["placa"] == "XYZ987"
    assert resultado["vehiculo"]["precio"] == 18500.5
    assert isinstance(resultado["vehiculo"]["precio"], float)
    args_sql, params_sql = mock_cursor.execute.call_args[0]
    assert params_sql == ("XYZ987",)
    mock_conexion.close.assert_called_once()


def test_unit_ventas_buscar_por_placa_no_encontrado(mocker):
    """Unitaria: Verifica que retorne None si el vehículo no existe o no está disponible."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.buscar_por_placa("NOEXISTE")

    assert resultado is None
    mock_conexion.close.assert_called_once()


def test_unit_ventas_buscar_cliente_por_termino(mocker):
    """Unitaria: Verifica la búsqueda de un cliente por término en base de seguridad."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    cliente_ficticio = {"cedula_usuario": "V-12345", "nombre": "Luis", "apellido": "Sivira"}

    mock_cursor.fetchone.return_value = cliente_ficticio
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion)

    resultado = Ventas.buscar_cliente("Luis")

    assert resultado == cliente_ficticio
    _, params_sql = mock_cursor.execute.call_args[0]
    assert params_sql == ("%Luis%", "%Luis%", "%Luis%", "%Luis%")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_buscar_cliente_no_encontrado(mocker):
    """Unitaria: Verifica que retorne None cuando no hay coincidencia de cliente."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion)

    resultado = Ventas.buscar_cliente("Inexistente")

    assert resultado is None
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: TRANSACCIÓN DE REGISTRO DE VENTA (CAMINOS DE ÉXITO Y ERROR)
# ==============================================================================

def test_unit_ventas_registrar_exitoso_efectivo(mocker):
    """Unitaria: Verifica el flujo transaccional completo con pago en efectivo (método 2)."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[10, 20, 30, 40])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {
        'cedula_cliente': 'V-12345678',
        'placa': 'ABC123A',
        'tipo_venta': 'Contado',
        'monto_recibido': 500,
        'precio_vehiculo': 500,
        'deuda_pendiente': 0,
        'fecha_vencimiento': '2026-12-31',
        'cod_metodo': '2',  # Efectivo
        'cod_moneda': 1
    }

    venta = Ventas(data)
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": True, "cod_venta": 10}
    sqls = [call.args[0] for call in mock_cursor.execute.call_args_list]
    assert not any("det_banco" in s or "det_nom_digital" in s for s in sqls)
    mock_cursor.execute.assert_any_call("UPDATE vehiculo SET estado = 'Vendido' WHERE placa = %s", ('ABC123A',))
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=1, cod_modulo=14)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_registrar_exitoso_metodo_bancario_credito(mocker):
    """Unitaria: Verifica inserción en det_banco y cuenta por cobrar en estado 'pendiente'."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[11, 21, 31, 41])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {
        'cedula_cliente': 'V-22222222',
        'placa': 'DEF456',
        'tipo_venta': 'Crédito',
        'monto_recibido': 1000,
        'precio_vehiculo': 5000,
        'deuda_pendiente': 4000,
        'fecha_vencimiento': '2027-01-30',
        'cod_metodo': '3',  # Bancario
        'cod_moneda': 2,
        'cod_banco': 5,
        'referencia': 'TRF-9988'
    }

    venta = Ventas(data)
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": True, "cod_venta": 11}
    # Verifica cuenta por cobrar en estado pendiente
    cxc_call = [c for c in mock_cursor.execute.call_args_list if "cuentas_por_cobrar" in c.args[0]][0]
    assert cxc_call.args[1][3] == 'pendiente'
    # Verifica detalle bancario con cod_det_pago = 41
    banco_call = [c for c in mock_cursor.execute.call_args_list if "det_banco" in c.args[0]][0]
    assert banco_call.args[1] == (1000.0, 'TRF-9988', 5, 41)
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=1, cod_modulo=14)
    mock_conexion.commit.assert_called_once()


def test_unit_ventas_registrar_exitoso_metodo_digital(mocker):
    """Unitaria: Verifica inserción en det_nom_digital y cod_moneda=None en det_pago."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[12, 22, 32, 42])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    data = {
        'cedula_cliente': 'V-33333333',
        'placa': 'GHI789',
        'tipo_venta': 'Contado',
        'monto_recibido': 2500,
        'precio_vehiculo': 2500,
        'deuda_pendiente': 0,
        'fecha_vencimiento': '2026-12-31',
        'cod_metodo': '4',  # Digital
        'cod_moneda': 1,    # Debe ignorarse (guardarse None en det_pago)
        'cod_mon_digital': 2,
        'referencia': 'ZELLE-01'
    }

    venta = Ventas(data)
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": True, "cod_venta": 12}
    det_pago_call = [c for c in mock_cursor.execute.call_args_list if "det_pago" in c.args[0]][0]
    assert det_pago_call.args[1][4] is None  # cod_moneda en None
    digital_call = [c for c in mock_cursor.execute.call_args_list if "det_nom_digital" in c.args[0]][0]
    assert digital_call.args[1] == (2500.0, 'ZELLE-01', 2, 42)
    mock_conexion.commit.assert_called_once()


def test_unit_ventas_registrar_sin_pago_inicial(mocker):
    """Unitaria: Verifica registro a crédito con monto_recibido=0 (omite tablas de pago)."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[15, 25])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    data = {
        'cedula_cliente': 'V-44444444',
        'placa': 'JKL000',
        'tipo_venta': 'Crédito',
        'monto_recibido': 0,
        'precio_vehiculo': 8000,
        'deuda_pendiente': 8000,
        'fecha_vencimiento': '2027-06-01',
    }

    venta = Ventas(data)
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": True, "cod_venta": 15}
    sqls = [call.args[0] for call in mock_cursor.execute.call_args_list]
    assert not any("pago_cuentas" in s or "det_pago" in s for s in sqls)
    mock_conexion.commit.assert_called_once()


def test_unit_ventas_registrar_falla_validacion(mocker):
    """Unitaria: Verifica que no abra conexión/transacción si la validación previa falla."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": False, "error": "Faltan datos"})
    mock_obtener = mocker.patch.object(ConexionBD, "obtener_conexion")

    venta = Ventas({})
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": False, "error": "Faltan datos"}
    mock_obtener.assert_not_called()


def test_unit_ventas_registrar_metodo_pago_no_reconocido_hace_rollback(mocker):
    """Unitaria: Verifica rollback() y cierre de recursos ante método de pago inválido."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.lastrowid = 1
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {
        'cedula_cliente': 'V-55555555',
        'placa': 'MNO111',
        'tipo_venta': 'Contado',
        'monto_recibido': 100,
        'precio_vehiculo': 100,
        'deuda_pendiente': 0,
        'cod_metodo': '99',  # Inexistente
    }

    venta = Ventas(data)
    resultado = venta.registrar("V-Admin")

    assert resultado["status"] is False
    assert "Método de pago no reconocido: 99" in resultado["error"]
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_registrar_error_sql_hace_rollback(mocker):
    """Unitaria: Verifica rollback() y cierre seguro cuando falla una consulta SQL."""
    mocker.patch("utils.validaciones_ventas.validar_registro_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Exception("Error de integridad BD")
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    venta = Ventas({'placa': 'ABC123', 'monto_recibido': 100, 'cod_metodo': '2'})
    resultado = venta.registrar("V-Admin")

    assert resultado == {"status": False, "error": "Error de integridad BD"}
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: OBTENER DATOS DE FACTURA / COMPROBANTE
# ==============================================================================

def test_unit_ventas_obtener_datos_factura_exitoso(mocker):
    """Unitaria: Verifica armado de factura, conversión Decimal->float y cierre de ambas BD."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion_seg = mocker.MagicMock()
    mock_cursor_seg = mocker.MagicMock()

    venta_row = {
        'cod_venta': 7,
        'cedula_cliente': 'V-9999',
        'precio': Decimal('15000.00'),
        'deuda_total': Decimal('15000.00'),
        'saldo_pendiente': Decimal('5000.00')
    }
    total_row = {'total_pagado': Decimal('10000.00')}
    pagos_rows = [{'cod_pagos': 1, 'monto_abonado': Decimal('10000.00')}]
    cliente_row = {'cedula_usuario': 'V-9999', 'nombre': 'Carlos', 'apellido': 'Pérez'}

    mock_cursor.fetchone.side_effect = [venta_row, total_row]
    mock_cursor.fetchall.return_value = pagos_rows
    mock_cursor_seg.fetchone.return_value = cliente_row

    mock_conexion.cursor.return_value = mock_cursor
    mock_conexion_seg.cursor.return_value = mock_cursor_seg
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion_seg)

    resultado = Ventas.obtener_datos_factura(7)

    assert resultado is not None
    assert resultado['venta']['precio'] == 15000.0
    assert isinstance(resultado['venta']['precio'], float)
    assert resultado['venta']['total_pagado'] == 10000.0
    assert resultado['pagos'][0]['monto_abonado'] == 10000.0
    assert isinstance(resultado['pagos'][0]['monto_abonado'], float)
    assert resultado['cliente'] == cliente_row

    mock_cursor_seg.close.assert_called_once()
    mock_conexion_seg.close.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_datos_factura_venta_no_existe(mocker):
    """Unitaria: Verifica que retorne None y no abra BD de seguridad si la venta no existe."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_seg = mocker.patch.object(ConexionBD, "obtener_conexion_seguridad")

    resultado = Ventas.obtener_datos_factura(999)

    assert resultado is None
    mock_seg.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_datos_factura_cliente_no_disponible(mocker):
    """Unitaria: Verifica el diccionario de respaldo si el cliente no existe en seguridad."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion_seg = mocker.MagicMock()
    mock_cursor_seg = mocker.MagicMock()

    mock_cursor.fetchone.side_effect = [
        {'cod_venta': 8, 'cedula_cliente': 'V-0000', 'precio': None, 'deuda_total': None, 'saldo_pendiente': None},
        None
    ]
    mock_cursor.fetchall.return_value = []
    mock_cursor_seg.fetchone.return_value = None

    mock_conexion.cursor.return_value = mock_cursor
    mock_conexion_seg.cursor.return_value = mock_cursor_seg
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion_seg)

    resultado = Ventas.obtener_datos_factura(8)

    assert resultado['cliente']['nombre'] == 'Cliente'
    assert resultado['cliente']['apellido'] == 'no disponible'
    assert resultado['venta']['precio'] == 0.0
    assert resultado['venta']['total_pagado'] == 0.0


def test_unit_ventas_obtener_datos_factura_error_bd(mocker):
    """Unitaria: Verifica manejo de excepción retornando None y cerrando recursos abiertos."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Exception("Fallo de consulta")
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    resultado = Ventas.obtener_datos_factura(1)

    assert resultado is None
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: LISTADO GENERAL (OBTENER TODAS)
# ==============================================================================

def test_unit_ventas_obtener_todas_exitoso(mocker):
    """Unitaria: Verifica listado de ventas y registro de consulta en bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    ventas_ficticias = [{"cod_venta": 1, "placa": "ABC123"}]
    mock_cursor.fetchall.return_value = ventas_ficticias
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Ventas.obtener_todas("V-Admin")

    assert resultado == ventas_ficticias
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=2, cod_modulo=14)
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_obtener_todas_error_bd_retorna_lista_vacia(mocker):
    """Unitaria: Verifica que ante error SQL retorne lista vacía sin registrar bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Exception("Timeout SQL")
    mock_conexion.cursor.return_value = mock_cursor

    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Ventas.obtener_todas("V-Admin")

    assert resultado == []
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: ELIMINACIÓN (ANULACIÓN) Y ACTUALIZACIÓN DE VENTA
# ==============================================================================

def test_unit_ventas_eliminar_anulacion_exitosa(mocker):
    """Unitaria: Verifica anulación de venta, liberación del vehículo y anulación de cxc."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {'placa': 'ABC123A'}
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Ventas.eliminar(5, "V-Admin")

    assert resultado is True
    mock_cursor.execute.assert_any_call("UPDATE vehiculo SET estado = 'Disponible' WHERE placa = %s", ('ABC123A',))
    mock_cursor.execute.assert_any_call("UPDATE ventas SET estado = 'Anulada' WHERE cod_venta = %s", (5,))
    mock_cursor.execute.assert_any_call("UPDATE cuentas_por_cobrar SET estado = 'anulada', deuda = 0 WHERE cod_venta = %s", (5,))
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=4, cod_modulo=14)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_eliminar_sin_detalle_placa(mocker):
    """Unitaria: Si no encuentra detalle de placa, omite liberar vehículo pero anula venta."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    resultado = Ventas.eliminar(99, "V-Admin")

    assert resultado is True
    sqls = [c.args[0] for c in mock_cursor.execute.call_args_list]
    assert not any("UPDATE vehiculo" in s for s in sqls)
    mock_conexion.commit.assert_called_once()


def test_unit_ventas_eliminar_error_hace_rollback_y_retorna_false(mocker):
    """Unitaria: Verifica rollback() y retorno False cuando falla la anulación."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Exception("Error SQL al anular")
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Ventas.eliminar(5, "V-Admin")

    assert resultado is False
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_actualizar_falla_validacion(mocker):
    """Unitaria: Verifica que actualizar no abra conexión si la validación falla."""
    mocker.patch("utils.validaciones_ventas.validar_actualizacion_venta", return_value={"status": False, "error": "Monto inválido"})
    mock_obtener = mocker.patch.object(ConexionBD, "obtener_conexion")

    resultado = Ventas.actualizar({'cod_venta': 3}, "V-Admin")

    assert resultado == {"status": False, "error": "Monto inválido"}
    mock_obtener.assert_not_called()


def test_unit_ventas_actualizar_exitoso_saldo_pendiente(mocker):
    """Unitaria: Verifica recálculo matemático de deuda pendiente y estado 'pendiente'."""
    mocker.patch("utils.validaciones_ventas.validar_actualizacion_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {'total_pagado': 100.0}
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {
        'cod_venta': 3,
        'deuda_total': 1000.0,
        'fecha_vencimiento': '2026-11-30'
    }

    resultado = Ventas.actualizar(data, "V-Admin")

    assert resultado == {"status": True}
    update_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE cuentas_por_cobrar" in c.args[0]][0]
    assert update_call.args[1] == (1000.0, 900.0, '2026-11-30', 'pendiente', 3)
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=3, cod_modulo=14)
    mock_conexion.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_ventas_actualizar_limite_sobrepago_marca_pagado(mocker):
    """Unitaria (Valor límite): Si lo pagado supera nueva deuda_total, deuda se ajusta a 0 y estado='pagado'."""
    mocker.patch("utils.validaciones_ventas.validar_actualizacion_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {'total_pagado': Decimal('700.00')}
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    data = {
        'cod_venta': 4,
        'deuda_total': 500.0,
        'fecha_vencimiento': '2026-12-01'
    }

    resultado = Ventas.actualizar(data, "V-Admin")

    assert resultado == {"status": True}
    update_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE cuentas_por_cobrar" in c.args[0]][0]
    assert update_call.args[1] == (500.0, 0, '2026-12-01', 'pagado', 4)
    mock_conexion.commit.assert_called_once()


def test_unit_ventas_actualizar_error_sql_hace_rollback(mocker):
    """Unitaria: Verifica rollback() y cierre de recursos si falla la actualización."""
    mocker.patch("utils.validaciones_ventas.validar_actualizacion_venta", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = Exception("Error al actualizar cxc")
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {'cod_venta': 3, 'deuda_total': 1000.0, 'fecha_vencimiento': '2026-11-30'}
    resultado = Ventas.actualizar(data, "V-Admin")

    assert resultado == {"status": False, "error": "Error al actualizar cxc"}
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()