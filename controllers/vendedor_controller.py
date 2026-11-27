from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.vendedor import Vendedor
from utils.decorators import login_required
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

vendedor_bp = Blueprint('vendedor', __name__, url_prefix='/vendedores')

@vendedor_bp.route('/')
@login_required
@requiere_permiso('Vendedor', 'p_leer')
def listar():
    cedula_usuario = session.get('cedula_usuario')
    vendedores = Vendedor.obtener_todos(cedula_usuario)
    return render_template('vendedor/index.html', vendedores=vendedores)

@vendedor_bp.route('/registrar', methods=['POST'])
@login_required
@requiere_permiso('Vendedor', 'p_crear')
def registrar():
    cedula = request.form.get('cedula')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    correo = request.form.get('email')
    password = request.form.get('password')
    cedula_usuario = session.get('cedula_usuario')

    if not all([cedula, nombre, apellido, telefono, direccion, correo, password]):
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('vendedor.listar'))

    nuevo_vendedor = Vendedor(
        cedula=cedula,
        nombre=nombre,
        apellido=apellido,
        telefono=telefono,
        direccion=direccion,
        correo=correo,
        password=password
    )

    resultado = nuevo_vendedor.guardar(cedula_usuario)

    if resultado['status']:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Nuevo Vendedor Registrado",
                "mensaje": f"Se registró al vendedor {nombre} {apellido} (Cédula: {cedula}).",
                "url_destino": url_for('vendedor.listar'),
                "modulo": "vendedor"
            }
        )
        flash(resultado['mensaje'], "success")
    else:
        flash(resultado['mensaje'], "danger")

    return redirect(url_for('vendedor.listar'))

@vendedor_bp.route('/editar/<cedula>', methods=['POST'])
@login_required
@requiere_permiso('Vendedor', 'p_actualizar')
def editar(cedula):
    cedula_usuario = session.get('cedula_usuario')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')

    resultado = Vendedor.actualizar(
        cedula,
        nombre,
        apellido,
        request.form.get('telefono'),
        request.form.get('direccion'),
        request.form.get('email'),
        cedula_usuario
    )

    if resultado['status']:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Vendedor Actualizado",
                "mensaje": f"Se actualizaron los datos del vendedor {nombre} {apellido} (Cédula: {cedula}).",
                "url_destino": url_for('vendedor.listar'),
                "modulo": "vendedor"
            }
        )
        flash(resultado['mensaje'], "success")
    else:
        flash(resultado['mensaje'], "danger")

    return redirect(url_for('vendedor.listar'))

@vendedor_bp.route('/cambiar_estado/<cedula>')
@login_required
@requiere_permiso('Vendedor', 'p_eliminar')
def cambiar_estado(cedula):
    cedula_usuario = session.get('cedula_usuario')
    vendedor = Vendedor.obtener_por_cedula(cedula)
    if vendedor:
        nuevo_estado = 0 if vendedor.get('estado') == 1 else 1
        Vendedor.cambiar_estado(cedula, nuevo_estado, cedula_usuario)
        estado_texto = "activado" if nuevo_estado == 1 else "desactivado"
        
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": f"Vendedor {estado_texto.capitalize()}",
                "mensaje": f"El vendedor {vendedor.get('nombre')} {vendedor.get('apellido')} ha sido {estado_texto}.",
                "url_destino": url_for('vendedor.listar'),
                "modulo": "vendedor"
            }
        )
        flash(f"Vendedor {estado_texto} correctamente", "success")
    return redirect(url_for('vendedor.listar'))