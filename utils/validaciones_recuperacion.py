import re


class ValidacionesRecuperacion:

    @staticmethod
    def validar_respuesta_recuperacion(respuesta):
        if respuesta is None or respuesta.strip() == "":
            return "La respuesta no puede estar vacía."
        if len(respuesta.strip()) < 2:
            return "La respuesta debe tener al menos 2 caracteres."
        return None

    @staticmethod
    def validar_password_recuperacion(password):
        if password is None or password.strip() == "":
            return "La contraseña no puede estar vacía."

        password = password.strip()

        if len(password) < 8:
            return "La contraseña debe tener al menos 8 caracteres."
        if not re.search(r"[A-Z]", password):
            return "La contraseña debe tener al menos una letra mayúscula."
        if not re.search(r"[a-z]", password):
            return "La contraseña debe tener al menos una letra minúscula."
        # Corregido: r"\d" para buscar números correctamente
        if not re.search(r"\d", password):
            return "La contraseña debe tener al menos un número."
        # Nueva validación de caracteres especiales sin conflictos de comillas
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\\\[\];\']', password):
            return "La contraseña debe tener al menos un carácter especial."

        return None