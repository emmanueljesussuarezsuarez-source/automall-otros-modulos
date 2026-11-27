from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from utils.session_store import sesion_valida, invalidar_sesiones_usuario
from models.db import ConexionBD


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_nombre' not in session:
            flash("Debes iniciar sesión para ver esta página.")
            return redirect(url_for('auth.login'))

        cedula = session.get('cedula_usuario')
        token = session.get('session_token')
        en_testing = current_app.config.get('TESTING', False)

        # En ejecución real se exige token válido en memoria; en TESTING solo si la sesión trae token
        if not en_testing or token is not None:
            if not sesion_valida(token, cedula):
                session.clear()
                flash("Tu sesión ha expirado o fue cerrada.")
                return redirect(url_for('auth.login'))

        # Verificar que el usuario siga existiendo en BD (si fue eliminado, cerrar sesión)
        if not en_testing and cedula:
            conn = ConexionBD.obtener_conexion_seguridad()
            cur = conn.cursor()
            try:
                cur.execute("SELECT 1 FROM t_usuario WHERE cedula_usuario = %s", (cedula,))
                existe = cur.fetchone()
            finally:
                cur.close()
                conn.close()

            if not existe:
                invalidar_sesiones_usuario(cedula)
                session.clear()
                flash("Tu usuario ya no está activo en el sistema.")
                return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
