from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from models.auth import Auth
from utils.validaciones_recuperacion import ValidacionesRecuperacion
from utils.captcha import generar_captcha_sesion, validar_captcha
from utils.session_store import crear_sesion, invalidar_sesion, invalidar_sesiones_usuario

auth_bp = Blueprint('auth', __name__)


# CAPTCHA DAVID
@auth_bp.route('/captcha', methods=['GET'])
def obtener_captcha():
    imagen_bytes = generar_captcha_sesion()
    respuesta = Response(imagen_bytes, mimetype='image/png')
    respuesta.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    respuesta.headers['Pragma'] = 'no-cache'
    respuesta.headers['Expires'] = '0'
    return respuesta


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # CP-LOG-33 - INICIO CORRECCIÓN
        datos = request.get_json(silent=True)
        # CP-LOG-33 - FIN CORRECCIÓN

        if not datos:
            return jsonify({"status": "error", "message": "Datos de petición inválidos."}), 400

        # CAPTCHA DAVID
        codigo_captcha = datos.get('captcha')
        es_valido, mensaje_captcha = validar_captcha(codigo_captcha)
        if not es_valido:
            return jsonify({
                "status": "error",
                "message": mensaje_captcha,
                "recargar_captcha": True
            })

        correo = datos.get('email')
        password = datos.get('password')

        usuario = Auth.verificar_credenciales(correo, password)

        if isinstance(usuario, dict) and 'error' in usuario:
            return jsonify({
                "status": "error",
                "message": usuario['error'],
                "recargar_captcha": True
            })

        if usuario:
            session['cedula_usuario'] = usuario['cedula_usuario']
            session['usuario_nombre'] = usuario['nombre']
            session['cod_rol'] = usuario['cod_rol']
            session['session_token'] = crear_sesion(usuario['cedula_usuario'])

            return jsonify({
                "status": "success",
                "redirect": url_for('index'),
                "nombre": usuario['nombre']
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Correo o contraseña incorrectos.",
                "recargar_captcha": True
            })

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    token = session.get('session_token')
    cedula = session.get('cedula_usuario')
    if token:
        invalidar_sesion(token)
    elif cedula:
        invalidar_sesiones_usuario(cedula)
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        correo = request.form.get('email')

        datos = Auth.obtener_pregunta(correo)

        if isinstance(datos, dict) and 'error' in datos:
            flash(datos['error'], "warning")
            return render_template('auth/olvido_password.html')

        if datos and datos.get('nombre_preguntas'):
            session['recuperar_correo'] = correo
            session['recuperar_cedula'] = datos['cedula_usuario']

            preguntas = [datos['nombre_preguntas']]
            if datos.get('nombre_preguntas_2'):
                preguntas.append(datos['nombre_preguntas_2'])

            return render_template('auth/verificar_pregunta.html', preguntas=preguntas)

        else:
            flash("El correo no existe o no tiene una pregunta de seguridad configurada.", "warning")

    return render_template('auth/olvido_password.html')


@auth_bp.route('/verificar_respuesta', methods=['POST'])
def verificar_respuesta():
    correo = session.get('recuperar_correo')
    respuestas = request.form.getlist('respuesta')

    if not correo:
        flash("Sesión de recuperación expirada.", "danger")
        return redirect(url_for('auth.recuperar'))

    if len(respuestas) < 2 or not respuestas[0].strip() or not respuestas[1].strip():
        flash("Debes responder las dos preguntas.", "danger")
        return redirect(url_for('auth.recuperar'))

    respuesta1 = respuestas[0].strip()
    respuesta2 = respuestas[1].strip()

    usuario1 = Auth.validar_respuesta(correo, respuesta1)
    usuario2 = Auth.validar_respuesta(correo, respuesta2)

    if usuario1 and usuario2:
        session['recuperacion_autorizada'] = True
        return render_template('auth/cambio_password.html')
    else:
        flash("Una o ambas respuestas son incorrectas.", "danger")
        return redirect(url_for('auth.recuperar'))


@auth_bp.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    correo = session.get('recuperar_correo')
    autorizada = session.get('recuperacion_autorizada')
    nueva_pass = request.form.get('nueva_password')
    confirmar_pass = request.form.get('confirmar_password')

    if not correo or not autorizada:
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('auth.login'))

    if nueva_pass != confirmar_pass:
        flash("Las contraseñas no coinciden.", "warning")
        return render_template('auth/cambio_password.html')

    # Validación de robustez en backend mediante la utilidad de recuperación
    error_pass = ValidacionesRecuperacion.validar_password_recuperacion(nueva_pass)
    if error_pass:
        flash(error_pass, "danger")
        return render_template('auth/cambio_password.html')

    resultado = Auth.actualizar_password(correo, nueva_pass)

    if resultado['status']:
        session.pop('recuperar_correo', None)
        session.pop('recuperar_cedula', None)
        session.pop('recuperacion_autorizada', None)
        flash(resultado['mensaje'], "success")
        return redirect(url_for('auth.login'))
    else:
        flash(resultado['mensaje'], "danger")
        return render_template('auth/cambio_password.html')