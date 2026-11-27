def validar_abono_pago(pago, validar_monto=True):
    if not pago.cod_cuentas:
        return {
            "status": False,
            "error": "No se especificó el código de la cuenta por cobrar asociada al pago."
        }

    cod_cuota = getattr(pago, "cod_cuota", None)
    if cod_cuota not in (None, "", 0, "0"):
        try:
            if int(cod_cuota) <= 0:
                return {"status": False, "error": "La cuota seleccionada no es válida."}
        except (TypeError, ValueError):
            return {"status": False, "error": "El código de cuota no es válido."}

    if pago.monto_pago <= 0:
        return {
            "status": False,
            "error": "El monto del abono debe ser un valor mayor a cero."
        }

    if validar_monto and pago.monto_pago > pago.saldo_actual + 0.01:
        return {
            "status": False,
            "error": (
                f"El monto del abono ({pago.monto_pago:.2f}) "
                f"no puede superar el saldo pendiente ({pago.saldo_actual:.2f} USD)."
            )
        }

    if not pago.cod_metodo:
        return {"status": False, "error": "Debe seleccionar un método de pago."}

    metodo = str(pago.cod_metodo)
    METODO_EFECTIVO = "2"
    METODOS_BANCARIOS = {"3", "5"}
    METODOS_DIGITALES = {"1", "4", "6"}

    if metodo == METODO_EFECTIVO or metodo in METODOS_BANCARIOS:
        if not pago.cod_moneda:
            return {"status": False, "error": "Debe seleccionar la moneda con la que realiza el pago."}

    if metodo in METODOS_DIGITALES:
        if not pago.cod_mon_digital:
            return {"status": False, "error": "Debe seleccionar la moneda o plataforma digital."}

    if metodo in METODOS_BANCARIOS:
        if not pago.cod_banco:
            return {"status": False, "error": "Para Pago Móvil o Transferencia Bancaria debe seleccionar el banco."}

    if metodo != METODO_EFECTIVO:
        if not str(pago.referencia or "").strip():
            return {"status": False, "error": "Este método de pago requiere un número de referencia o TXID."}

    return {"status": True}


def validar_actualizacion_pago(pago):
    if not pago.cod_pagos:
        return {"status": False, "error": "El código del pago es requerido para efectuar una actualización."}

    if pago.monto_pago <= 0:
        return {"status": False, "error": "El nuevo monto del pago debe ser mayor a cero."}

    if not pago.cod_metodo:
        return {"status": False, "error": "El método de pago no puede quedar vacío."}

    metodo = str(pago.cod_metodo)
    if metodo not in {"1", "4", "6"} and not pago.cod_moneda:
        return {"status": False, "error": "La moneda asociada al pago es obligatoria."}

    return {"status": True}