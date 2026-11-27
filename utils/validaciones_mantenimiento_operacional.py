import re
from datetime import datetime, date


class ValidacionMantenimientoOperacional:

    @staticmethod
    def validar_descripcion_general(texto):
        if not texto or len(texto.strip()) < 10:
            return "La descripción general debe tener al menos 10 caracteres."
        return None

    @staticmethod
    def validar_quien_autoriza(valor):
        if not valor or not str(valor).strip():
            return "Debe seleccionar quién autoriza."
        if not str(valor).strip().isdigit():
            return "El valor de autorización debe ser numérico."
        return None

    @staticmethod
    def validar_tipo_mantenimiento(tipo):
        if not tipo or not str(tipo).strip():
            return "Debe seleccionar el tipo de mantenimiento."
        if tipo not in {"Preventivo", "Correctivo"}:
            return "El tipo de mantenimiento no es válido."
        return None

    @staticmethod
    def validar_fecha_no_pasada(fecha, campo="Fecha"):
        if not fecha or not str(fecha).strip():
            return f"{campo} es obligatoria."
        try:
            f = datetime.strptime(str(fecha).strip(), "%Y-%m-%d").date()
        except ValueError:
            return f"El formato de {campo.lower()} no es válido. Use YYYY-MM-DD."
        if f < date.today():
            return f"{campo} no puede ser anterior a hoy."
        return None

    @staticmethod
    def validar_fecha_completada(fecha_completada, fecha_solicitud):
        if not fecha_completada or not str(fecha_completada).strip():
            return None
        try:
            fc = datetime.strptime(str(fecha_completada).strip(), "%Y-%m-%d").date()
        except ValueError:
            return "El formato de fecha completada no es válido. Use YYYY-MM-DD."
        try:
            fs = datetime.strptime(str(fecha_solicitud).strip(), "%Y-%m-%d").date()
        except ValueError:
            return "La fecha de solicitud no es válida."
        if fc < fs:
            return "La fecha completada no puede ser anterior a la fecha de solicitud."
        return None

    @staticmethod
    def validar_placa(placa):
        if not placa or not str(placa).strip():
            return "Debe seleccionar una placa."
        placa = str(placa).strip()
        if len(placa) < 5 or len(placa) > 7:
            return "La placa debe tener entre 5 y 7 caracteres."
        return None

    @staticmethod
    def validar_cod_taller(cod_taller):
        if not cod_taller or not str(cod_taller).strip():
            return "Debe seleccionar un taller."
        if not str(cod_taller).strip().isdigit():
            return "El código del taller debe ser numérico."
        return None

    @staticmethod
    def validar_mantenimiento(datos):
        errores = {}

        checks = [
            ("descripcion_general", ValidacionMantenimientoOperacional.validar_descripcion_general(datos.get("descripcion_general"))),
            ("quien_autoriza", ValidacionMantenimientoOperacional.validar_quien_autoriza(datos.get("quien_autoriza"))),
            ("tipo", ValidacionMantenimientoOperacional.validar_tipo_mantenimiento(datos.get("tipo"))),
            ("fecha_solicitud", ValidacionMantenimientoOperacional.validar_fecha_no_pasada(datos.get("fecha_solicitud"), "Fecha de solicitud")),
            ("fecha_completada", ValidacionMantenimientoOperacional.validar_fecha_completada(datos.get("fecha_completada"), datos.get("fecha_solicitud"))),
            ("placa", ValidacionMantenimientoOperacional.validar_placa(datos.get("placa"))),
            ("cod_taller", ValidacionMantenimientoOperacional.validar_cod_taller(datos.get("cod_taller"))),
        ]

        for campo, err in checks:
            if err:
                errores[campo] = err

        return len(errores) == 0, errores