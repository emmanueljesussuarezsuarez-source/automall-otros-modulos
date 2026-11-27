import re
from datetime import datetime, date


class ValidacionServicios:
    @staticmethod
    def validar_nombre_servicio(nombre_servicio):
        nombre_servicio = (nombre_servicio or "").strip()

        if not nombre_servicio:
            return "El nombre del servicio es obligatorio."

        if len(nombre_servicio) < 3:
            return "El nombre del servicio debe tener al menos 3 caracteres."

        if len(nombre_servicio) > 100:
            return "El nombre del servicio no puede superar 100 caracteres."

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre_servicio):
            return "El nombre del servicio solo puede contener letras y espacios."

        return None

    @staticmethod
    def validar_costo_base(costo_base):
        costo_base = ("" if costo_base is None else str(costo_base)).strip()

        if not costo_base:
            return None

        try:
            valor = float(costo_base)
        except ValueError:
            return "El costo base debe ser un número válido."

        if valor < 0:
            return "El costo base no puede ser negativo."

        return None

    @staticmethod
    def validar_costo_final(costo_final, obligatorio=False):
        costo_final = ("" if costo_final is None else str(costo_final)).strip()

        if not costo_final:
            if obligatorio:
                return "Debe registrar el costo final antes de finalizar el servicio."
            return None

        try:
            valor = float(costo_final)
        except ValueError:
            return "El costo final debe ser un número válido."

        if valor < 0:
            return "El costo final no puede ser negativo."

        return None

    @staticmethod
    def validar_descripcion_especifica(descripcion_especifica):
        descripcion_especifica = (descripcion_especifica or "").strip()

        if not descripcion_especifica:
            return "La descripción específica es obligatoria."

        if len(descripcion_especifica) < 10:
            return "La descripción específica debe tener al menos 10 caracteres."

        return None

    @staticmethod
    def validar_fecha_realizacion(fecha_realizacion):
        fecha_realizacion = (fecha_realizacion or "").strip()

        if not fecha_realizacion:
            return "La fecha de realización es obligatoria."

        try:
            f = datetime.strptime(fecha_realizacion, "%Y-%m-%d").date()
        except ValueError:
            return "El formato de fecha de realización no es válido. Use YYYY-MM-DD."

        if f < date.today():
            return "La fecha de realización no puede ser anterior a hoy."

        return None

    @staticmethod
    def validar_placa(placa):
        placa = (placa or "").strip()

        if not placa:
            return "Debe seleccionar una placa."

        if len(placa) < 5 or len(placa) > 7:
            return "La placa debe tener entre 5 y 7 caracteres."

        return None

    @staticmethod
    def validar_servicio(nombre_servicio, costo_base, costo_final, descripcion_especifica, fecha_realizacion, placa, costo_final_obligatorio=False):
        errores = {}

        err_nombre = ValidacionServicios.validar_nombre_servicio(nombre_servicio)
        if err_nombre:
            errores["nombre_servicio"] = err_nombre

        err_costo_base = ValidacionServicios.validar_costo_base(costo_base)
        if err_costo_base:
            errores["costo_base"] = err_costo_base

        err_costo_final = ValidacionServicios.validar_costo_final(costo_final, obligatorio=costo_final_obligatorio)
        if err_costo_final:
            errores["costo_final"] = err_costo_final

        err_desc = ValidacionServicios.validar_descripcion_especifica(descripcion_especifica)
        if err_desc:
            errores["descripcion_especifica"] = err_desc

        err_fecha = ValidacionServicios.validar_fecha_realizacion(fecha_realizacion)
        if err_fecha:
            errores["fecha_realizacion"] = err_fecha

        err_placa = ValidacionServicios.validar_placa(placa)
        if err_placa:
            errores["placa"] = err_placa

        return len(errores) == 0, errores