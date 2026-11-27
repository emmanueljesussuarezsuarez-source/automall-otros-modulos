from datetime import datetime


METODO_BINANCE = "1"
METODO_EFECTIVO = "2"
METODO_PAGO_MOVIL = "3"
METODO_ZELLE = "4"
METODO_TRANSFERENCIA = "5"
METODO_ZINLI = "6"

METODOS_BANCARIOS = {"3", "5"}
METODOS_DIGITALES = {"1", "4", "6"}
FRECUENCIAS_VALIDAS = {"semanal", "quincenal", "mensual", "personalizado"}


def _valor_vacio(valor):
    return valor is None or not str(valor).strip()


def _a_float(valor, defecto=None):
    if valor is None or str(valor).strip() == "":
        return defecto
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _a_int(valor, defecto=None):
    if valor is None or str(valor).strip() == "":
        return defecto
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _normalizar_metodo(metodo):
    if metodo is None:
        return ""
    return str(metodo).strip()


def _parsear_fecha(fecha):
    if _valor_vacio(fecha):
        return None
    try:
        return datetime.strptime(str(fecha).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _fecha_futura(fecha):
    fecha_obj = _parsear_fecha(fecha)
    if not fecha_obj:
        return False
    return fecha_obj > datetime.now().date()


def _fecha_hoy_o_futura(fecha):
    fecha_obj = _parsear_fecha(fecha)
    if not fecha_obj:
        return False
    return fecha_obj >= datetime.now().date()


def validar_registro_venta(venta):
    # ------------------------------------------------------------
    # DATOS BÁSICOS
    # ------------------------------------------------------------
    if _valor_vacio(venta.cedula_cliente):
        return {
            "status": False,
            "error": "La cédula del cliente es obligatoria para procesar la venta.",
        }

    if _valor_vacio(venta.placa):
        return {
            "status": False,
            "error": "La placa del vehículo es obligatoria.",
        }

    if venta.tipo_venta not in ("contado", "credito"):
        return {
            "status": False,
            "error": "El tipo de venta debe ser 'contado' o 'credito'.",
        }

    precio_total = _a_float(venta.precio_total)
    if precio_total is None:
        return {"status": False, "error": "El precio del vehículo no es válido."}

    if precio_total <= 0:
        return {"status": False, "error": "El precio del vehículo debe ser mayor que cero."}

    monto_recibido = _a_float(venta.monto_recibido, 0.0)
    if monto_recibido is None:
        return {"status": False, "error": "El monto recibido no es válido."}

    if monto_recibido < 0:
        return {"status": False, "error": "El monto recibido no puede ser negativo."}

    # ------------------------------------------------------------
    # TIPO DE VENTA Y PLAN DE CUOTAS
    # ------------------------------------------------------------
    deuda_pendiente = _a_float(getattr(venta, "deuda_pendiente", 0), 0.0)
    if deuda_pendiente is None:
        return {
            "status": False,
            "error": "La deuda pendiente no tiene un valor numérico válido.",
        }

    if deuda_pendiente < 0:
        return {
            "status": False,
            "error": "La deuda pendiente no puede ser negativa.",
        }

    if venta.tipo_venta == "contado":
        if deuda_pendiente > 0.009:
            return {
                "status": False,
                "error": "Una venta de contado debe quedar completamente pagada.",
            }

        if monto_recibido <= 0:
            return {
                "status": False,
                "error": "En una venta de contado debe recibirse el pago completo.",
            }
    else:
        if monto_recibido >= precio_total:
            return {
                "status": False,
                "error": "Si el pago inicial cubre el 100% del vehículo, registre la venta como contado.",
            }

        frecuencia = str(getattr(venta, "frecuencia_pago", "Mensual") or "Mensual").strip().lower()
        if frecuencia not in FRECUENCIAS_VALIDAS:
            return {
                "status": False,
                "error": "La frecuencia de pago debe ser Semanal, Quincenal o Mensual.",
            }

        cantidad_cuotas = _a_int(getattr(venta, "cantidad_cuotas", 1), 1)
        if cantidad_cuotas is None or cantidad_cuotas < 1 or cantidad_cuotas > 120:
            return {
                "status": False,
                "error": "La cantidad de cuotas debe estar entre 1 y 120.",
            }

        tasa_interes = _a_float(getattr(venta, "tasa_interes", 0.0), 0.0)
        if tasa_interes is None or tasa_interes < 0 or tasa_interes > 100:
            return {
                "status": False,
                "error": "La tasa de interés debe estar entre 0% y 100%.",
            }

        fecha_inicio = getattr(venta, "fecha_inicio_cuotas", None)
        if not _valor_vacio(fecha_inicio):
            if not _fecha_hoy_o_futura(fecha_inicio):
                return {
                    "status": False,
                    "error": "La fecha de la primera cuota debe ser hoy o posterior.",
                }

        if not _fecha_hoy_o_futura(venta.fecha_vencimiento):
            return {
                "status": False,
                "error": "Para una venta a crédito debe indicar una fecha de vencimiento válida (hoy o futura).",
            }

        if not _valor_vacio(fecha_inicio):
            f_ini = _parsear_fecha(fecha_inicio)
            f_fin = _parsear_fecha(venta.fecha_vencimiento)
            if f_ini and f_fin and f_fin < f_ini:
                return {
                    "status": False,
                    "error": "La fecha de vencimiento final no puede ser anterior a la primera cuota.",
                }

        saldo_base = max(0.0, precio_total - monto_recibido)
        monto_interes = round(saldo_base * (tasa_interes / 100.0), 2)
        deuda_calculada = round(saldo_base + monto_interes, 2)

        if abs(round(deuda_pendiente, 2) - deuda_calculada) > 0.05:
            return {
                "status": False,
                "error": "La deuda pendiente no coincide con el precio, inicial e interés calculado.",
            }

        cuotas = getattr(venta, "cuotas", None)
        if isinstance(cuotas, list) and len(cuotas) > 0:
            if len(cuotas) != cantidad_cuotas:
                return {
                    "status": False,
                    "error": "La cantidad de cuotas del cronograma no coincide con la indicada.",
                }

            suma_cuotas = 0.0
            for item in cuotas:
                monto_c = _a_float(item.get("monto_cuota"))
                fecha_c = _parsear_fecha(item.get("fecha_vencimiento"))
                if monto_c is None or monto_c <= 0:
                    return {
                        "status": False,
                        "error": "Todas las cuotas deben tener un monto mayor a cero.",
                    }
                if not fecha_c:
                    return {
                        "status": False,
                        "error": "Todas las cuotas deben tener una fecha de vencimiento válida.",
                    }
                suma_cuotas += monto_c

            if abs(round(suma_cuotas, 2) - deuda_calculada) > 0.05:
                return {
                    "status": False,
                    "error": "La suma de las cuotas no coincide con el saldo a financiar.",
                }

    # Si no hay pago inicial, no se exige método de pago.
    if monto_recibido <= 0:
        return {"status": True}

    # ------------------------------------------------------------
    # MÉTODO DE PAGO
    # ------------------------------------------------------------
    metodo = _normalizar_metodo(venta.cod_metodo)
    if not metodo:
        return {
            "status": False,
            "error": "Debe seleccionar un método de pago.",
        }

    if metodo == METODO_EFECTIVO:
        if _valor_vacio(venta.cod_moneda):
            return {
                "status": False,
                "error": "Para efectivo debe seleccionar la moneda de recepción.",
            }
        return {"status": True}

    if metodo in METODOS_DIGITALES:
        if _valor_vacio(venta.cod_mon_digital):
            return {
                "status": False,
                "error": "Debe seleccionar la moneda/plataforma digital.",
            }
        return {"status": True}

    if metodo in METODOS_BANCARIOS:
        if _valor_vacio(venta.cod_banco):
            return {
                "status": False,
                "error": "Debe seleccionar el banco para el método de pago elegido.",
            }
        if _valor_vacio(venta.cod_moneda):
            return {
                "status": False,
                "error": "Debe seleccionar la moneda de recepción.",
            }
        if _valor_vacio(venta.referencia):
            return {
                "status": False,
                "error": "Debe ingresar la referencia o número de transacción.",
            }
        return {"status": True}

    return {
        "status": False,
        "error": "El método de pago seleccionado no es válido.",
    }


def validar_actualizacion_venta(data):
    if not data:
        return {"status": False, "error": "No se recibieron datos para actualizar."}

    if _valor_vacio(data.get("cod_venta")):
        return {"status": False, "error": "El código de venta es obligatorio."}

    if _valor_vacio(data.get("cedula_cliente")):
        return {"status": False, "error": "La cédula del cliente es obligatoria."}

    tipo_venta = str(data.get("tipo_venta", "")).strip().lower()
    if tipo_venta and tipo_venta not in ("contado", "credito"):
        return {
            "status": False,
            "error": "El tipo de venta debe ser 'contado' o 'credito'.",
        }

    deuda_total = _a_float(data.get("deuda_total"))
    if deuda_total is None or deuda_total <= 0:
        return {"status": False, "error": "La deuda total debe ser un monto válido mayor a cero."}

    if not _valor_vacio(data.get("cantidad_cuotas")):
        cant = _a_int(data.get("cantidad_cuotas"))
        if cant is None or cant < 1 or cant > 120:
            return {"status": False, "error": "La cantidad de cuotas debe estar entre 1 y 120."}

    if not _valor_vacio(data.get("frecuencia_pago")):
        frec = str(data.get("frecuencia_pago")).strip().lower()
        if frec not in FRECUENCIAS_VALIDAS:
            return {"status": False, "error": "La frecuencia de pago no es válida."}

    if not _valor_vacio(data.get("fecha_inicio_cuotas")):
        if not _parsear_fecha(data.get("fecha_inicio_cuotas")):
            return {"status": False, "error": "La fecha de la primera cuota no tiene un formato válido."}

    if tipo_venta == "credito" and not _fecha_hoy_o_futura(data.get("fecha_vencimiento")):
        return {
            "status": False,
            "error": "La fecha de vencimiento debe ser hoy o futura para una venta a crédito.",
        }

    return {"status": True}