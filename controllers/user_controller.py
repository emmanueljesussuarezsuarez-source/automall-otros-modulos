import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.user import Usuario
from utils.decorators import login_required
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

user_bp = Blueprint('user', __name__)


@user_bp.route('/perfil')
@login_required
def perfil():
    cedula_usuario = session.get('cedula_usuario')
    usuario_info = Usuario.obtener_por_cedula(cedula_usuario)
    preguntas = Usuario.obtener_preguntas_banco()

    if not usuario_info:
        return render_template(
            'usuarios/perfil.html',
            usuario=None,
            preguntas=preguntas,
            swal={"icon": "error", "title": "Error", "text": "No se pudo cargar la información del perfil."}
        )

    return render_template('usuarios/perfil.html', usuario=usuario_info, preguntas=preguntas, swal=None)


@user_bp.route('/perfil/actualizar-datos', methods=['POST'])
@login_required
def actualizar_datos_perfil():
    cedula_usuario = session.get('cedula_usuario')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    correo = request.form.get('correo')
    foto_perfil = request.files.get('foto_perfil')

    resultado = Usuario.actualizar_datos_perfil(cedula_usuario, telefono, direccion, correo, foto_perfil)

    if resultado['status']:
        return render_template(
            'usuarios/perfil.html',
            usuario=Usuario.obtener_por_cedula(cedula_usuario),
            preguntas=Usuario.obtener_preguntas_banco(),
            swal={"icon": "success", "title": "Éxito", "text": resultado["mensaje"]}
        )

    return render_template(
        'usuarios/perfil.html',
        usuario=Usuario.obtener_por_cedula(cedula_usuario),
        preguntas=Usuario.obtener_preguntas_banco(),
        swal={"icon": "error", "title": "Error", "text": resultado["mensaje"]}
    )


@user_bp.route('/perfil/cambiar-password', methods=['POST'])
@login_required
def cambiar_password_perfil():
    cedula_usuario = session.get('cedula_usuario')
    password_actual = request.form.get('password_actual')
    nueva_password = request.form.get('nueva_password')
    confirmar_password = request.form.get('confirmar_password')

    resultado = Usuario.cambiar_password(
        cedula_usuario,
        password_actual,
        nueva_password,
        confirmar_password
    )

    if resultado['status']:
        return render_template(
            'usuarios/perfil.html',
            usuario=Usuario.obtener_por_cedula(cedula_usuario),
            preguntas=Usuario.obtener_preguntas_banco(),
            swal={"icon": "success", "title": "Éxito", "text": resultado["mensaje"]}
        )

    return render_template(
        'usuarios/perfil.html',
        usuario=Usuario.obtener_por_cedula(cedula_usuario),
        preguntas=Usuario.obtener_preguntas_banco(),
        swal={"icon": "error", "title": "Error", "text": resultado["mensaje"]}
    )


@user_bp.route('/perfil/guardar-preguntas', methods=['POST'])
@login_required
def guardar_preguntas():
    cedula_usuario = session.get('cedula_usuario')
    pregunta_1 = request.form.get('pregunta_1')
    respuesta_1 = request.form.get('respuesta_1')
    confirmar_respuesta_1 = request.form.get('confirmar_respuesta_1')
    pregunta_2 = request.form.get('pregunta_2')
    respuesta_2 = request.form.get('respuesta_2')
    confirmar_respuesta_2 = request.form.get('confirmar_respuesta_2')

    resultado = Usuario.guardar_preguntas_seguridad(
        cedula_usuario,
        pregunta_1, respuesta_1, confirmar_respuesta_1,
        pregunta_2, respuesta_2, confirmar_respuesta_2
    )

    if resultado['status']:
        return render_template(
            'usuarios/perfil.html',
            usuario=Usuario.obtener_por_cedula(cedula_usuario),
            preguntas=Usuario.obtener_preguntas_banco(),
            swal={"icon": "success", "title": "Éxito", "text": resultado["mensaje"]}
        )

    return render_template(
        'usuarios/perfil.html',
        usuario=Usuario.obtener_por_cedula(cedula_usuario),
        preguntas=Usuario.obtener_preguntas_banco(),
        swal={"icon": "error", "title": "Error", "text": resultado["mensaje"]}
    )


@user_bp.route('/perfil/actualizar-preguntas', methods=['POST'])
@login_required
def actualizar_preguntas():
    cedula_usuario = session.get('cedula_usuario')

    respuesta_vieja_1 = request.form.get('respuesta_vieja_1')
    respuesta_vieja_2 = request.form.get('respuesta_vieja_2')

    pregunta_nueva_1 = request.form.get('pregunta_nueva_1')
    respuesta_nueva_1 = request.form.get('respuesta_nueva_1')
    confirmar_respuesta_nueva_1 = request.form.get('confirmar_respuesta_nueva_1')

    pregunta_nueva_2 = request.form.get('pregunta_nueva_2')
    respuesta_nueva_2 = request.form.get('respuesta_nueva_2')
    confirmar_respuesta_nueva_2 = request.form.get('confirmar_respuesta_nueva_2')

    resultado = Usuario.actualizar_preguntas_seguridad(
        cedula_usuario,
        respuesta_vieja_1,
        respuesta_vieja_2,
        pregunta_nueva_1,
        respuesta_nueva_1,
        confirmar_respuesta_nueva_1,
        pregunta_nueva_2,
        respuesta_nueva_2,
        confirmar_respuesta_nueva_2
    )

    if resultado['status']:
        return render_template(
            'usuarios/perfil.html',
            usuario=Usuario.obtener_por_cedula(cedula_usuario),
            preguntas=Usuario.obtener_preguntas_banco(),
            swal={"icon": "success", "title": "Éxito", "text": resultado["mensaje"]}
        )

    return render_template(
        'usuarios/perfil.html',
        usuario=Usuario.obtener_por_cedula(cedula_usuario),
        preguntas=Usuario.obtener_preguntas_banco(),
        swal={"icon": "error", "title": "Error", "text": resultado["mensaje"]}
    )


@user_bp.route('/usuarios/crear', methods=['POST'])
@login_required
@requiere_permiso('Usuarios', 'p_crear')
def crear():
    cedula_usuario = session.get('cedula_usuario')
    
    resultado = Usuario.registrar_usuario_completo(request.form, request.files, cedula_usuario)
    
    if resultado['status']:
        nombre = request.form.get('nombre', '')
        apellido = request.form.get('apellido', '')
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Nuevo Usuario Registrado",
                "mensaje": f"Se ha registrado un nuevo usuario: {nombre} {apellido}.",
                "url_destino": url_for('user.listar'),
                "modulo": "usuarios"
            }
        )
    
    tipo_alerta = "success" if resultado['status'] else "error"
    titulo = "Éxito" if resultado['status'] else "Error"
    
    return render_template(
        'usuarios/index.html', 
        usuarios=Usuario.obtener_todos(cedula_usuario), 
        roles=Usuario.obtener_roles_disponibles(),
        swal={"icon": tipo_alerta, "title": titulo, "text": resultado["mensaje"]}
    )


@user_bp.route('/usuarios')
@login_required
@requiere_permiso('Usuarios', 'p_leer')
def listar():
    cedula_usuario = session.get('cedula_usuario')
    usuarios = Usuario.obtener_todos(cedula_usuario)
    roles = Usuario.obtener_roles_disponibles()
    return render_template('usuarios/index.html', usuarios=usuarios, roles=roles, swal=None)


@user_bp.route('/usuarios/eliminar/<int:cedula_usuario>')
@login_required
@requiere_permiso('Usuarios', 'p_eliminar')
def eliminar(cedula_usuario):
    cedula_usuario_session = session.get('cedula_usuario')
    exito = Usuario.eliminar(cedula_usuario, cedula_usuario_session)
    
    if exito:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Usuario Eliminado",
                "mensaje": f"El usuario con cédula {cedula_usuario} ha sido inactivado/eliminado.",
                "url_destino": url_for('user.listar'),
                "modulo": "usuarios"
            }
        )
        alerta = {"icon": "success", "title": "Éxito", "text": "Usuario eliminado correctamente."}
    else:
        alerta = {"icon": "error", "title": "Error", "text": "Error al intentar eliminar el usuario."}

    return render_template(
        'usuarios/index.html', 
        usuarios=Usuario.obtener_todos(cedula_usuario_session), 
        roles=Usuario.obtener_roles_disponibles(),
        swal=alerta
    )


@user_bp.route('/nuevo_registro')
@login_required
def nuevo_registro():
    return render_template('usuarios/nuevo_registro.html', swal=None)


@user_bp.route('/usuarios/editar/<int:cedula_usuario>', methods=['POST'])
@login_required
@requiere_permiso('Usuarios', 'p_actualizar')
def editar(cedula_usuario):
    cedula_usuario_session = session.get('cedula_usuario')
    cod_rol = request.form.get('cod_rol')
    nombre = request.form.get('nombre', '')
    apellido = request.form.get('apellido', '')
    
    resultado = Usuario.actualizar(
        cedula_usuario,
        nombre,
        apellido,
        request.form.get('telefono'),
        request.form.get('direccion'),
        request.form.get('email'),
        cedula_usuario_session,
        cod_rol=cod_rol
    )

    if resultado['status']:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Usuario Actualizado",
                "mensaje": f"Se actualizaron los datos del usuario {nombre} {apellido}.",
                "url_destino": url_for('user.listar'),
                "modulo": "usuarios"
            }
        )

    tipo_alerta = "success" if resultado['status'] else "error"
    return render_template(
        'usuarios/index.html',
        usuarios=Usuario.obtener_todos(cedula_usuario_session),
        roles=Usuario.obtener_roles_disponibles(),
        swal={"icon": tipo_alerta, "title": "Aviso", "text": resultado["mensaje"]}
    )


@user_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        correo = request.form.get('email')
        password = request.form.get('password')

        foto = request.files.get('foto_perfil')
        nombre_foto = "default.png"

        nuevo_usuario = Usuario(
            cedula, nombre, apellido, telefono, direccion, correo, password, nombre_foto, cod_rol=4
        )

        resultado = nuevo_usuario.guardar()

        if resultado['status']:
            if foto and foto.filename != '':
                extension = os.path.splitext(foto.filename)[1]
                nombre_foto = secure_filename(f"{cedula}{extension}")
                ruta_guardado = os.path.join('static', 'uploads', 'perfiles', nombre_foto)
                foto.save(ruta_guardado)

            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Nuevo Registro Externo",
                    "mensaje": f"Un nuevo usuario se ha registrado: {nombre} {apellido} (Cédula: {cedula}).",
                    "url_destino": url_for('user.listar'),
                    "modulo": "usuarios"
                }
            )

            return render_template(
                'usuarios/registro.html',
                swal={
                    "icon": "success", 
                    "title": "Éxito", 
                    "text": resultado["mensaje"],
                    "redirect": url_for('auth.login')
                }
            )

        return render_template(
            'usuarios/registro.html',
            swal={"icon": "error", "title": "Error", "text": resultado["mensaje"]}
        )

    return render_template('usuarios/registro.html', swal=None)