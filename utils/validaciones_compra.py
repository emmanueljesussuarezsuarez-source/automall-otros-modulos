class ValidacionCompra:

    @staticmethod
    def validar_cabecera(datos):
        errores = {}

        rif = datos.get('rif_cedula_proveedor')
        try:
            rif = int(rif)
            if rif <= 0:
                errores['rif_cedula_proveedor'] = "El RIF/Cédula del proveedor no es válido."
        except (TypeError, ValueError):
            errores['rif_cedula_proveedor'] = "Debe seleccionar un proveedor."

        tipo = (datos.get('tipo_compra') or '').strip()
        if len(tipo) < 3:
            errores['tipo_compra'] = "El tipo de compra debe tener al menos 3 caracteres."
        elif len(tipo) > 50:
            errores['tipo_compra'] = "El tipo de compra no puede exceder 50 caracteres."

        obs = datos.get('observaciones') or ''
        if len(obs) > 100:
            errores['observaciones'] = "Las observaciones no pueden exceder 100 caracteres."

        return (len(errores) == 0), errores

    @staticmethod
    def validar_detalle(datos):
        errores = {}

        try:
            cod_compras = int(datos.get('cod_compras'))
            if cod_compras <= 0:
                errores['cod_compras'] = "Código de compra inválido."
        except (TypeError, ValueError):
            errores['cod_compras'] = "Código de compra inválido."

        try:
            cod_insumo = int(datos.get('cod_insumo'))
            if cod_insumo <= 0:
                errores['cod_insumo'] = "Debe seleccionar un insumo."
        except (TypeError, ValueError):
            errores['cod_insumo'] = "Debe seleccionar un insumo."

        try:
            cantidad = int(datos.get('cantidad'))
            if cantidad <= 0:
                errores['cantidad'] = "La cantidad debe ser mayor a cero."
        except (TypeError, ValueError):
            errores['cantidad'] = "La cantidad debe ser un número entero."

        return (len(errores) == 0), errores

    @staticmethod
    def validar_proveedor(datos):
        errores = {}

        try:
            rif = int(datos.get('rif'))
            if rif <= 0:
                errores['rif'] = "El RIF/Cédula no es válido."
        except (TypeError, ValueError):
            errores['rif'] = "El RIF/Cédula debe ser numérico."

        razon = (datos.get('razon_social') or '').strip()
        if len(razon) < 3:
            errores['razon_social'] = "La razón social es obligatoria (mín. 3)."
        elif len(razon) > 250:
            errores['razon_social'] = "La razón social no puede exceder 250 caracteres."

        direccion = (datos.get('direccion') or '').strip()
        if not direccion:
            errores['direccion'] = "La dirección es obligatoria."

        telefono = datos.get('telefono')
        if not telefono:
            errores['telefono'] = "El teléfono es obligatorio."
        else:
            try:
                int(telefono)
            except (TypeError, ValueError):
                errores['telefono'] = "El teléfono debe ser numérico."

        correo = (datos.get('correo') or '').strip()
        if not correo or '@' not in correo or '.' not in correo.split('@')[-1]:
            errores['correo'] = "El correo no es válido."
        elif len(correo) > 50:
            errores['correo'] = "El correo no puede exceder 50 caracteres."

        estado = datos.get('estado')
        if estado is not None and estado not in {'Activo', 'Inactivo'}:
            errores['estado'] = "Estado inválido."

        return (len(errores) == 0), errores