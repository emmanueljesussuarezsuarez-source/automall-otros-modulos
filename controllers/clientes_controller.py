from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.clientes import ClienteModel
from utils.decorators import login_required
from models.bitacora import Bitacora
from utils.validaciones import ValidacionUsuario
from utils.permisos import requiere_permiso
from utils.session_store import invalidar_sesiones_usuario

clientes_bp = Blueprint('clientes', __name__)



# Lista de clientes--------------------------------------------------------------------------------
@clientes_bp.route('/clientes')
@login_required
@requiere_permiso('Clientes', 'p_leer')
def listar_clientes():
    clientes = ClienteModel.obtener_clientes()
    Bitacora.registrar(session.get('cedula_usuario'), 2, 17)
    return render_template('usuarios/clientes.html', clientes=clientes)


# registrar----------------------------------------------------------------------------------------
@clientes_bp.route('/registrar_clientes', methods=['GET', 'POST'])
def registrar_clientes():
    if request.method == 'POST':
        cedula    = request.form.get('cedula', '').strip()
        nombre    = request.form.get('nombre', '').strip()
        apellido  = request.form.get('apellido', '').strip()
        telefono  = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        correo    = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        archivo_foto = request.files.get('foto_perfil')


        err_foto = ValidacionUsuario.validar_foto_perfil(archivo_foto)
        if err_foto:
            flash(f"{err_foto}", "danger")
            return render_template('usuarios/registrar_clientes.html', datos=request.form)


        nombre_foto = ClienteModel.guardar_foto_perfil(archivo_foto, cedula) or "uploads/perfiles/default.png"

        nuevo_cliente = ClienteModel(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            correo=correo,
            password=password,
            foto=nombre_foto,
            cod_rol=4
        )

        resultado = nuevo_cliente.registrar_cliente_db()

        if resultado['status']:
            operador = session.get('cedula_usuario') or cedula
            Bitacora.registrar(operador, 1, 17)
            flash(f"✨ {resultado['mensaje']}", "success")
            if session.get('cod_rol') == 1:
                return redirect(url_for('clientes.listar_clientes'))
            return redirect(url_for('auth.login'))
        else:
            flash(f"{resultado['mensaje']}", "danger")
            return render_template('usuarios/registrar_clientes.html', datos=request.form)

    return render_template('usuarios/registrar_clientes.html')


# Editar----------------------------------------------------------------------------------------
@clientes_bp.route('/clientes/editar/<cedula>', methods=['POST'])
@login_required
@requiere_permiso('Clientes', 'p_actualizar')
def editar_cliente(cedula):
    datos_form = {
        'nombre':    request.form.get('nombre', '').strip(),
        'apellido':  request.form.get('apellido', '').strip(),
        'telefono':  request.form.get('telefono', '').strip(),
        'direccion': request.form.get('direccion', '').strip(),
        'correo':    request.form.get('correo', '').strip(),
    }

    es_valido, errores = ValidacionUsuario.validar_modificacion_cliente(datos_form)
    if not es_valido:
        for _, mensaje in errores.items():
            flash(f"{mensaje}", "danger")
        return redirect(url_for('clientes.listar_clientes'))

    archivo_foto = request.files.get('foto_perfil')
    err_foto = ValidacionUsuario.validar_foto_perfil(archivo_foto)
    if err_foto:
        flash(f"{err_foto}", "danger")
        return redirect(url_for('clientes.listar_clientes'))

    nueva_foto = ClienteModel.guardar_foto_perfil(archivo_foto, cedula)
    if nueva_foto is None:
   
        cliente_actual = ClienteModel.obtener_por_cedula(cedula)
        nueva_foto = cliente_actual['foto'] if cliente_actual else "uploads/perfiles/default.png"

    datos_form['cedula'] = cedula
    datos_form['foto'] = nueva_foto

    if ClienteModel.actualizar_cliente(datos_form):
        Bitacora.registrar(session.get('cedula_usuario'), 3, 17)
        flash("Datos del cliente actualizados con éxito.", "success")
    else:
        flash("No se pudieron guardar los cambios.", "danger")

    return redirect(url_for('clientes.listar_clientes'))

# Eliminar ---------------------------------------------------------------------------------------
@clientes_bp.route('/clientes/eliminar/<cedula>', methods=['POST'])
@login_required
@requiere_permiso('Clientes', 'p_eliminar')
def eliminar_cliente(cedula):
    resultado = ClienteModel.eliminar_cliente(cedula)
    if resultado['status']:
        invalidar_sesiones_usuario(cedula)
        Bitacora.registrar(session.get('cedula_usuario'), 4, 17)
        flash(resultado['mensaje'], "success")
    else:
        flash(f"{resultado['mensaje']}", "danger")

    return redirect(url_for('clientes.listar_clientes'))

