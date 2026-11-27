import re


class ValidacionTaller:
    @staticmethod
    def validar_nombre_taller(nombre_taller, excluir_cod_taller=None, existe_func=None):
        nombre_taller = (nombre_taller or "").strip()

        if not nombre_taller:
            return "El nombre del taller es obligatorio."

        if len(nombre_taller) < 3:
            return "El nombre del taller debe tener al menos 3 caracteres."

        if len(nombre_taller) > 100:
            return "El nombre del taller no puede superar 100 caracteres."

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\.\-]+$', nombre_taller):
            return "El nombre del taller contiene caracteres no permitidos."

        if existe_func:
            if existe_func(nombre_taller, excluir_cod_taller):
                return "Ya existe un taller con ese nombre."

        return None

    @staticmethod
    def validar_direccion(direccion):
        direccion = (direccion or "").strip()

        if not direccion:
            return "La dirección es obligatoria."

        if len(direccion) < 5:
            return "La dirección debe tener al menos 5 caracteres."

        if len(direccion) > 255:
            return "La dirección no puede superar 255 caracteres."

        return None

    @staticmethod
    def validar_estado(estado):
        estado = str(estado).strip() if estado is not None else "1"

        if estado not in ("0", "1"):
            return "El estado seleccionado no es válido."

        return None

    @staticmethod
    def validar_taller(nombre_taller, direccion, estado="1", excluir_cod_taller=None, existe_func=None):
        errores = {}

        err_nombre = ValidacionTaller.validar_nombre_taller(
            nombre_taller,
            excluir_cod_taller=excluir_cod_taller,
            existe_func=existe_func
        )
        if err_nombre:
            errores["nombre_taller"] = err_nombre

        err_direccion = ValidacionTaller.validar_direccion(direccion)
        if err_direccion:
            errores["direccion"] = err_direccion

        err_estado = ValidacionTaller.validar_estado(estado)
        if err_estado:
            errores["estado"] = err_estado

        return len(errores) == 0, errores