from decimal import Decimal
import pytest
from models.pagos import Pagos
from models.db import ConexionBD
from models.bitacora import Bitacora


# ==============================================================================
# PRUEBAS UNITARIAS: CONSTRUCTOR Y GETTERS (MODELO PAGOS)
# ==============================================================================

def test_unit_pagos_inicializacion_completa_y_getters():
    """Unitaria: Verifica el mapeo completo de atributos privados y todos los getters."""
    data = {
        "cod_pagos": 10,
        "monto_pago": "250.75",
        "cod_cuentas": 5,
        "descripcion": "Abono parcial",
        "cod_moneda": 1,
        "cod_metodo": "3",
        "referencia": "REF-7788",
        "cod_banco": 2,
        "cod_mon_digital": None,
        "saldo_actual": "500.25",
    }

    pago = Pagos(data)

    assert pago.cod_pagos == 10
    assert pago.monto_pago == 250.75
    assert pago.cod_cuentas == 5
    assert pago.descripcion == "Abono parcial"
    assert pago.cod_moneda == 1
    assert pago.cod_metodo == "3"
    assert pago.referencia == "REF-7788"
    assert pago.cod_banco == 2
    assert pago.cod_mon_digital is None
    assert pago.saldo_actual == 500.25


def test_unit_pagos_inicializacion_por_defecto_y_fallback_monto_abonado():
    """Unitaria: Verifica valores por defecto y fallback de monto_pago a monto_abonado."""
    pago_vacio = Pagos()
    assert pago_vacio.monto_pago == 0.0
    assert pago_vacio.saldo_actual == 0.0
    assert pago_vacio.descripcion == ""
    assert pago_vacio.referencia == ""
    assert pago_vacio.cod_moneda is None

    pago_fallback = Pagos({"monto_pago": "", "monto_abonado": "120.50", "cod_banco": ""})
    assert pago_fallback.monto_pago == 120.50
    assert pago_fallback.cod_banco is None


# ==============================================================================
# PRUEBAS UNITARIAS: TASA DE CAMBIO Y CONVERSIÓN A USD
# ==============================================================================

def test_unit_pagos_obtener_tasa_exitoso_y_error(mocker):
    """Unitaria: Verifica obtención de última tasa y retorno None ante fallo de BD."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    tasa_ficticia = {"valor": Decimal("45.50"), "fecha": "2026-11-19"}
    mock_cursor.fetchone.return_value = tasa_ficticia
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    assert Pagos.obtener_tasa() == tasa_ficticia
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()

    # Caso de excepción
    mock_cursor.execute.side_effect = Exception("Error BD tasa")
    assert Pagos.obtener_tasa() is None


@pytest.mark.parametrize(
    "cod_moneda, row, esperado",
    [
        (None, None, False),
        (1, None, False),
        (1, {"nombre_moneda": "Dólar", "simbolo": "$"}, False),
        (2, {"nombre_moneda": "Bolívar", "simbolo": "Bs"}, True),
        (3, {"nombre_moneda": "Moneda Local", "simbolo": "VES"}, True),
        (4, {"nombre_moneda": "Bolivar Digital", "simbolo": ""}, True),
    ]
)
def test_unit_pagos_moneda_es_bolivar(mocker, cod_moneda, row, esperado):
    """Unitaria: Verifica detección correcta de monedas en bolívares."""
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = row

    assert Pagos.moneda_es_bolivar(cod_moneda, mock_cursor) is esperado
    if not cod_moneda:
        mock_cursor.execute.assert_not_called()


def test_unit_pagos_convertir_a_usd_moneda_extranjera_y_bolivar(mocker):
    """Unitaria: Verifica conversión directa en USD y conversión dividida por tasa en Bs."""
    mock_cursor = mocker.MagicMock()

    # Caso 1: USD (no es bolívar)
    mock_cursor.fetchone.return_value = {"nombre_moneda": "Dólar", "simbolo": "$"}
    monto_usd, tasa = Pagos.convertir_a_usd(150, 1, mock_cursor)
    assert (monto_usd, tasa) == (150.0, None)

    # Caso 2: Bolívar con tasa válida
    mock_cursor.fetchone.side_effect = [
        {"nombre_moneda": "Bolívar", "simbolo": "Bs"},
        {"valor": Decimal("50.00")}
    ]
    monto_usd, tasa = Pagos.convertir_a_usd(5000, 2, mock_cursor)
    assert monto_usd == 100.0
    assert tasa == 50.0


@pytest.mark.parametrize("tasa_row, mensaje", [
    (None, "No existe una tasa de cambio registrada."),
    ({"valor": None}, "No existe una tasa de cambio registrada."),
    ({"valor": 0}, "No existe una tasa de cambio registrada."),
    ({"valor": -10}, "La tasa de cambio registrada no es válida."),
])
def test_unit_pagos_convertir_a_usd_tasa_inexistente_o_invalida_falla(mocker, tasa_row, mensaje):
    """Unitaria (Valores límite): Lanza ValueError si no hay tasa o si la tasa es <= 0."""
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.side_effect = [
        {"nombre_moneda": "Bolívar", "simbolo": "Bs"},
        tasa_row
    ]

    with pytest.raises(ValueError, match=mensaje):
        Pagos.convertir_a_usd(1000, 2, mock_cursor)


# ==============================================================================
# PRUEBAS UNITARIAS: PROCESAR ABONO (TRANSACCIÓN, VALIDACIONES Y ROLLBACK)
# ==============================================================================

def test_unit_pagos_procesar_abono_cuenta_no_existe(mocker):
    """Unitaria: Rechaza abono si la cuenta por cobrar no existe."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    pago = Pagos({"cod_cuentas": 999, "monto_pago": 100, "cod_metodo": "2"})
    resultado = pago.procesar_abono("V-Admin")

    assert resultado == {"status": False, "error": "La cuenta por cobrar no existe."}
    mock_conexion.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_pagos_procesar_abono_cuenta_no_pendiente_o_saldada(mocker):
    """Unitaria: Rechaza abono si la cuenta no está 'pendiente' o tiene saldo <= 0."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    # Estado no pendiente
    mock_cursor.fetchone.return_value = {"cod_cuentas": 1, "estado": "Pagado", "deuda": 100}
    res1 = Pagos({"cod_cuentas": 1}).procesar_abono("V-Admin")
    assert res1 == {"status": False, "error": "La cuenta seleccionada no tiene una deuda pendiente."}

    # Saldo <= 0
    mock_cursor.fetchone.return_value = {"cod_cuentas": 1, "estado": "Pendiente", "deuda": 0}
    res2 = Pagos({"cod_cuentas": 1}).procesar_abono("V-Admin")
    assert res2 == {"status": False, "error": "La cuenta seleccionada ya está pagada."}


def test_unit_pagos_procesar_abono_falla_validacion_externa(mocker):
    """Unitaria: Retorna error si validar_abono_pago retorna status False."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": False, "error": "Referencia requerida"})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {"cod_cuentas": 1, "estado": "Pendiente", "deuda": 500}
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    res = Pagos({"cod_cuentas": 1, "monto_pago": 100, "cod_metodo": "3"}).procesar_abono("V-Admin")

    assert res == {"status": False, "error": "Referencia requerida"}
    mock_conexion.commit.assert_not_called()


def test_unit_pagos_procesar_abono_monto_cero_o_excede_deuda(mocker):
    """Unitaria (Valores límite): Rechaza monto <= 0 o mayor al saldo pendiente."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    # Monto <= 0
    mock_cursor.fetchone.side_effect = [{"cod_cuentas": 1, "estado": "Pendiente", "deuda": 500}]
    res_cero = Pagos({"cod_cuentas": 1, "monto_pago": 0, "cod_metodo": "2"}).procesar_abono("V-Admin")
    assert res_cero == {"status": False, "error": "El monto convertido a USD debe ser mayor a cero."}

    # Monto excede deuda
    mock_cursor.fetchone.side_effect = [{"cod_cuentas": 1, "estado": "Pendiente", "deuda": 100}]
    res_exceso = Pagos({"cod_cuentas": 1, "monto_pago": 150, "cod_metodo": "2"}).procesar_abono("V-Admin")
    assert res_exceso["status"] is False
    assert "la deuda pendiente es $100.00 USD" in res_exceso["error"]
    mock_conexion.commit.assert_not_called()


def test_unit_pagos_procesar_abono_efectivo_liquida_cuenta_exitoso(mocker):
    """Unitaria: Abono en efectivo USD que salda la cuenta ('Pagado'), limpia referencia y hace commit."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.side_effect = [
        {"cod_cuentas": 1, "estado": "Pendiente", "deuda": Decimal("300.00")},
        {"nombre_moneda": "Dólar", "simbolo": "$"}
    ]
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[101, 201])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    pago = Pagos({
        "cod_cuentas": 1,
        "monto_pago": 300,
        "cod_moneda": 1,
        "cod_metodo": Pagos.METODO_EFECTIVO,
        "referencia": "NO-DEBE-GUARDARSE",
        "descripcion": ""
    })
    res = pago.procesar_abono("V-Admin")

    assert res == {"status": True, "cod_pagos": 101, "monto_usd": 300.0, "nuevo_saldo": 0.0, "tasa": None}
    # Referencia forzada a None para efectivo
    pago_call = [c for c in mock_cursor.execute.call_args_list if "INSERT INTO pago_cuentas" in c.args[0]][0]
    assert pago_call.args[1][1] is None
    # Descripción por defecto y estado Pagado
    det_call = [c for c in mock_cursor.execute.call_args_list if "INSERT INTO det_pago" in c.args[0]][0]
    assert det_call.args[1][1] == "Abono de cuenta"
    upd_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE cuentas_por_cobrar" in c.args[0]][0]
    assert upd_call.args[1] == (0.0, "Pagado", 1)
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=1, cod_modulo=15)
    mock_conexion.commit.assert_called_once()


def test_unit_pagos_procesar_abono_bancario_en_bolivares_parcial(mocker):
    """Unitaria: Abono bancario en Bs convierte a USD con tasa, inserta det_banco y deja 'Pendiente'."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.side_effect = [
        {"cod_cuentas": 2, "estado": "Pendiente", "deuda": Decimal("300.00")},
        {"nombre_moneda": "Bolívar", "simbolo": "Bs"},
        {"valor": Decimal("50.00")}
    ]
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[102, 202])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    pago = Pagos({
        "cod_cuentas": 2,
        "monto_pago": 5000,
        "cod_moneda": 2,
        "cod_metodo": Pagos.METODO_PAGO_MOVIL,
        "cod_banco": 4,
        "referencia": "PM-5566",
        "descripcion": "Pago parcial"
    })
    res = pago.procesar_abono("V-Admin")

    assert res == {"status": True, "cod_pagos": 102, "monto_usd": 100.0, "nuevo_saldo": 200.0, "tasa": 50.0}
    banco_call = [c for c in mock_cursor.execute.call_args_list if "INSERT INTO det_banco" in c.args[0]][0]
    assert banco_call.args[1] == (5000.0, "PM-5566", 4, 202)
    upd_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE cuentas_por_cobrar" in c.args[0]][0]
    assert upd_call.args[1] == (200.0, "Pendiente", 2)
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=1, cod_modulo=15)
    mock_conexion.commit.assert_called_once()


def test_unit_pagos_procesar_abono_digital_exitoso(mocker):
    """Unitaria: Abono digital fuerza cod_moneda=None en det_pago e inserta det_nom_digital."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.side_effect = [
        {"cod_cuentas": 3, "estado": "Pendiente", "deuda": Decimal("500.00")},
        {"nombre_moneda": "Dólar", "simbolo": "$"}
    ]
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[103, 203])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    pago = Pagos({
        "cod_cuentas": 3,
        "monto_pago": 200,
        "cod_moneda": 1,
        "cod_metodo": Pagos.METODO_ZELLE,
        "cod_mon_digital": 2,
        "referencia": "ZLL-99"
    })
    res = pago.procesar_abono("V-Admin")

    assert res["status"] is True
    det_call = [c for c in mock_cursor.execute.call_args_list if "INSERT INTO det_pago" in c.args[0]][0]
    assert det_call.args[1][4] is None  # cod_moneda en None para digital
    dig_call = [c for c in mock_cursor.execute.call_args_list if "INSERT INTO det_nom_digital" in c.args[0]][0]
    assert dig_call.args[1] == (200.0, "ZLL-99", 2, 203)
    mock_conexion.commit.assert_called_once()

@pytest.mark.parametrize(
    "extra_data, error_esperado",
    [
        ({"cod_metodo": Pagos.METODO_ZELLE, "cod_mon_digital": None}, "Debe seleccionar la moneda/plataforma digital."),
        ({"cod_metodo": Pagos.METODO_TRANSFERENCIA, "cod_banco": None}, "Debe seleccionar el banco."),
        ({"cod_metodo": "99"}, "Método de pago no reconocido: 99"),
    ]
)
def test_unit_pagos_procesar_abono_errores_metodo_hacen_rollback(mocker, extra_data, error_esperado):
    """Unitaria: Verifica rollback() y cierre de recursos ante faltante de banco/digital o método inválido."""
    mocker.patch("utils.validaciones_pagos.validar_abono_pago", return_value={"status": True})

    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {"cod_cuentas": 1, "estado": "Pendiente", "deuda": 500}
    type(mock_cursor).lastrowid = mocker.PropertyMock(side_effect=[1, 2])
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    data = {"cod_cuentas": 1, "monto_pago": 100, **extra_data}
    res = Pagos(data).procesar_abono("V-Admin")

    assert res == {"status": False, "error": error_esperado}
    mock_conexion.rollback.assert_called_once()
    mock_conexion.commit.assert_not_called()
    mock_bitacora.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: ANULACIÓN DE PAGO
# ==============================================================================

def test_unit_pagos_anular_no_encontrado_o_ya_anulado(mocker):
    """Unitaria: Retorna False sin hacer commit si el pago no existe o ya estaba anulado."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    mock_cursor.fetchone.return_value = None
    assert Pagos.anular(999, "V-Admin", "Error") is False

    mock_cursor.fetchone.return_value = {"cod_pagos": 1, "estado": "Anulado"}
    assert Pagos.anular(1, "V-Admin", "Doble") is False

    mock_conexion.commit.assert_not_called()
    assert mock_cursor.close.call_count == 2
    assert mock_conexion.close.call_count == 2


def test_unit_pagos_anular_exitoso_con_venta_y_motivo_default(mocker):
    """Unitaria: Restaura deuda (tope deuda_total), anula venta, libera vehículo y registra bitácora."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {
        "cod_pagos": 10,
        "cod_cuentas": 5,
        "monto_abonado": Decimal("300.00"),
        "estado": "Procesado",
        "deuda": Decimal("800.00"),
        "deuda_total": Decimal("1000.00"),  # 800 + 300 = 1100 -> se limita a 1000.00
        "cod_venta": 20,
    }
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    resultado = Pagos.anular(10, "V-Admin", None)

    assert resultado is True
    mock_cursor.execute.assert_any_call("UPDATE pago_cuentas SET estado = 'Anulado' WHERE cod_pagos = %s", (10,))
    motivo_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE det_pago" in c.args[0]][0]
    assert motivo_call.args[1] == ("Sin motivo especificado", 10)
    mock_cursor.execute.assert_any_call("UPDATE cuentas_por_cobrar SET deuda = %s, estado = 'Anulado' WHERE cod_cuentas = %s", (1000.0, 5))
    mock_cursor.execute.assert_any_call("UPDATE ventas SET estado = 'Anulada' WHERE cod_venta = %s", (20,))
    veh_call = [c for c in mock_cursor.execute.call_args_list if "UPDATE vehiculo" in c.args[0]][0]
    assert veh_call.args[1] == (20,)
    mock_bitacora.assert_called_once_with("V-Admin", cod_accion=4, cod_modulo=15)
    mock_conexion.commit.assert_called_once()


def test_unit_pagos_anular_sin_cod_venta_y_error_rollback(mocker):
    """Unitaria: Omite actualizar venta/vehículo si cod_venta es None, y hace rollback ante error."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = {
        "cod_pagos": 11, "cod_cuentas": 6, "monto_abonado": 100,
        "estado": "Procesado", "deuda": 200, "deuda_total": 500, "cod_venta": None
    }
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(Bitacora, "registrar")

    assert Pagos.anular(11, "V-Admin", "Ajuste") is True
    sqls = [c.args[0] for c in mock_cursor.execute.call_args_list]
    assert not any("UPDATE ventas" in s or "UPDATE vehiculo" in s for s in sqls)

    # Fallo SQL -> rollback y False
    mock_conexion.reset_mock()
    mock_cursor.execute.side_effect = Exception("Deadlock")
    assert Pagos.anular(11, "V-Admin", "Ajuste") is False
    mock_conexion.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


# ==============================================================================
# PRUEBAS UNITARIAS: COMPROBANTE DE PAGO (OBTENER DATOS FACTURA)
# ==============================================================================

def test_unit_pagos_obtener_datos_factura_procesado_bancario_exitoso(mocker):
    """Unitaria: Arma comprobante bancario, calcula saldo_antes y cierra ambas BD."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion_seg = mocker.MagicMock()
    mock_cursor_seg = mocker.MagicMock()

    pago_row = {
        "cod_pagos": 1, "cod_cuentas": 10, "cedula_cliente": "V-1234",
        "monto_abonado": Decimal("200.00"), "deuda_total": Decimal("1000.00"),
        "saldo_pendiente": Decimal("300.00"), "precio": Decimal("1000.00"),
        "estado_pago": "Procesado",
        "nombre_moneda": "Dólar", "simbolo": "$",
        "nombre_metodo": "Transferencia",
        "referencia_banco": "BNC-001", "monto_banco": Decimal("200.00"),
    }
    mock_cursor.fetchone.side_effect = [pago_row, {"total_pagado": Decimal("700.00")}]
    mock_cursor_seg.fetchone.return_value = {"cedula_usuario": "V-1234", "nombre": "Ana", "apellido": "López"}

    mock_conexion.cursor.return_value = mock_cursor
    mock_conexion_seg.cursor.return_value = mock_cursor_seg
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion_seg)

    res = Pagos.obtener_datos_factura(1)

    assert res["pago"]["saldo_antes"] == 500.0
    assert res["pago"]["saldo_pendiente"] == 300.0
    assert res["pago"]["total_pagado"] == 700.0
    assert res["pago"]["referencia"] == "BNC-001"
    assert res["pago"]["monto_recibido"] == 200.0
    assert res["pago"]["moneda"] == "Dólar"
    assert res["cliente"]["nombre"] == "Ana"

    mock_cursor_seg.close.assert_called_once()
    mock_conexion_seg.close.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_pagos_obtener_datos_factura_anulado_digital_y_cliente_fallback(mocker):
    """Unitaria: Verifica pago anulado, moneda digital y cliente respaldo 'no disponible'."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion_seg = mocker.MagicMock()
    mock_cursor_seg = mocker.MagicMock()

    pago_row = {
        "cod_pagos": 2, "cod_cuentas": 11, "cedula_cliente": "V-0000",
        "monto_abonado": Decimal("100.00"), "deuda_total": Decimal("500.00"),
        "saldo_pendiente": Decimal("400.00"), "precio": None,
        "estado_pago": "Anulado",
        "nombre_digital": "Zelle", "simbolo_digital": "ZLL",
        "nombre_metodo": "Zelle",
        "referencia_digital": "Z-77", "monto_digital": Decimal("100.00"),
    }
    mock_cursor.fetchone.side_effect = [pago_row, None]
    mock_cursor_seg.fetchone.return_value = None

    mock_conexion.cursor.return_value = mock_cursor
    mock_conexion_seg.cursor.return_value = mock_cursor_seg
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion_seg)

    res = Pagos.obtener_datos_factura(2)

    assert res["pago"]["saldo_antes"] == 400.0  # Por estar anulado no suma monto_pago
    assert res["pago"]["moneda"] == "Zelle"
    assert res["pago"]["simbolo_moneda"] == "ZLL"
    assert res["pago"]["referencia"] == "Z-77"
    assert res["pago"]["monto_recibido"] == 100.0
    assert res["pago"]["total_pagado"] == 0.0
    assert res["cliente"]["nombre"] == "Cliente"
    assert res["cliente"]["apellido"] == "no disponible"


def test_unit_pagos_obtener_datos_factura_no_existe_y_error_bd(mocker):
    """Unitaria: Retorna None si pago no existe o falla SQL sin abrir BD seguridad."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_seg = mocker.patch.object(ConexionBD, "obtener_conexion_seguridad")

    assert Pagos.obtener_datos_factura(999) is None
    mock_seg.assert_not_called()

    mock_cursor.execute.side_effect = Exception("Error SQL")
    assert Pagos.obtener_datos_factura(1) is None


# ==============================================================================
# PRUEBAS UNITARIAS: CONSULTAS Y LISTADOS (CLIENTE Y ADMIN)
# ==============================================================================

def test_unit_pagos_obtener_todos_cliente_exitoso_y_error(mocker):
    """Unitaria: Verifica listado por cliente con bitácora y retorno [] ante error."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    pagos_cliente = [{"cod_pagos": 1, "monto_abonado": 100}]
    mock_cursor.fetchall.return_value = pagos_cliente
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_bitacora = mocker.patch.object(Bitacora, "registrar")

    assert Pagos.obtener_todos("V-12345") == pagos_cliente
    mock_bitacora.assert_called_once_with("V-12345", cod_accion=2, cod_modulo=15)

    mock_bitacora.reset_mock()
    mock_cursor.execute.side_effect = Exception("Fallo consulta")
    assert Pagos.obtener_todos("V-12345") == []
    mock_bitacora.assert_not_called()
    assert mock_cursor.close.call_count == 2
    assert mock_conexion.close.call_count == 2


def test_unit_pagos_obtener_deudas_pendientes(mocker):
    """Unitaria: Verifica consulta de deudas pendientes del cliente y cierre en finally."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    deudas = [{"cod_cuentas": 3, "placa": "ABC123", "saldo_pendiente": 400.0}]
    mock_cursor.fetchall.return_value = deudas
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)

    assert Pagos.obtener_deudas_pendientes("V-12345") == deudas
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()


def test_unit_pagos_obtener_todos_admin_con_enriquecimiento_y_vacios(mocker):
    """Unitaria: Verifica listado admin con cruce de usuarios, respaldos y lista vacía."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conexion_seg = mocker.MagicMock()
    mock_cursor_seg = mocker.MagicMock()

    mock_conexion.cursor.return_value = mock_cursor
    mock_conexion_seg.cursor.return_value = mock_cursor_seg
    mocker.patch.object(ConexionBD, "obtener_conexion", return_value=mock_conexion)
    mock_seg = mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion_seg)

    # Caso 1: Sin pagos -> no abre BD seguridad
    mock_cursor.fetchall.return_value = []
    assert Pagos.obtener_todos_admin() == []
    mock_seg.assert_not_called()

    # Caso 2: Con pagos (uno encontrado en seguridad y otro no encontrado)
    mock_cursor.fetchall.return_value = [
        {"cod_pagos": 1, "cedula_usuario": "V-111"},
        {"cod_pagos": 2, "cedula_usuario": "V-999"},
    ]
    mock_cursor_seg.fetchall.return_value = [
        {"cedula_usuario": "V-111", "nombre": "Luis", "apellido": "Sivira", "telefono": "0414", "direccion": "Centro"}
    ]

    res = Pagos.obtener_todos_admin()

    assert len(res) == 2
    assert res[0]["nombre"] == "Luis"
    assert res[1]["nombre"] == "Sin Nombre"
    assert res[1]["telefono"] == "Sin Teléfono"
    mock_cursor_seg.close.assert_called_once()
    mock_conexion_seg.close.assert_called_once()

    # Caso 3: Error BD
    mock_cursor.execute.side_effect = Exception("Error BD admin")
    assert Pagos.obtener_todos_admin() == []


def test_unit_pagos_obtener_todos_clientes(mocker):
    """Unitaria: Verifica consulta general de clientes desde la BD de seguridad."""
    mock_conexion = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    clientes = [{"cedula_usuario": "V-111", "nombre": "Luis"}]
    mock_cursor.fetchall.return_value = clientes
    mock_conexion.cursor.return_value = mock_cursor
    mocker.patch.object(ConexionBD, "obtener_conexion_seguridad", return_value=mock_conexion)

    assert Pagos.obtener_todos_clientes() == clientes
    mock_cursor.execute.assert_called_once_with("SELECT * FROM t_usuario")
    mock_cursor.close.assert_called_once()
    mock_conexion.close.assert_called_once()