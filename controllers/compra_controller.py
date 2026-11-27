from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.compra import CompraModel, ESTADO_COMPLETADA, ESTADO_ANULADA
from models.bitacora import Bitacora
from utils.decorators import login_required
from utils.permisos import requiere_permiso

compra_bp = Blueprint('compras', __name__, url_prefix='/compras')

COD_MODULO_COMPRA = 21
COD_ACCION_INSERT = 1
COD_ACCION_UPDATE = 3
COD_ACCION_DELETE = 4


@compra_bp.route('/')
@login_required
@requiere_permiso('Compras', 'p_leer')
def listar():
    compras = CompraModel.obtener_todas()
    return render_template('compras/index.html', compras=compras)


@compra_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@requiere_permiso('Compras', 'p_crear')
def nueva():
    if request.method == 'POST':
        rif = request.form.get('rif_proveedor')
        tipo = request.form.get('tipo_compra', 'Normal').strip()
        observaciones = request.form.get('observaciones', '').strip()
        cedula = session['cedula_usuario']

        if not rif:
            flash("Debe seleccionar un proveedor.", "danger")
            return render_template('compras/nueva.html',
                                   proveedores=CompraModel.obtener_proveedores())

        try:
            cod_compras = CompraModel.crear(
                rif_cedula_proveedor=rif,
                tipo_compra=tipo,
                observaciones=observaciones,
                id_usuario_sesion=cedula,
            )
        except Exception as e:
            flash(str(e), "danger")
            return render_template('compras/nueva.html',
                                   proveedores=CompraModel.obtener_proveedores())

        flash(f"Compra #{cod_compras} creada. Agregue los insumos.", "success")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    proveedores = CompraModel.obtener_proveedores()
    return render_template('compras/nueva.html', proveedores=proveedores)


@compra_bp.route('/compra/<int:cod_compras>')
@login_required
@requiere_permiso('Compras', 'p_leer')
def detalle(cod_compras):
    compra = CompraModel.obtener_por_id(cod_compras)
    if not compra:
        flash("Compra no encontrada.", "danger")
        return redirect(url_for('compras.listar'))

    insumos = CompraModel.obtener_insumos_activos()
    return render_template('compras/detalle.html',
                           compra=compra,
                           insumos=insumos)


@compra_bp.route('/compra/<int:cod_compras>/agregar', methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_actualizar')
def agregar_insumo(cod_compras):
    cod_insumo = request.form.get('cod_insumo')
    cantidad_raw = request.form.get('cantidad', '1')
    cedula = session['cedula_usuario']

    if not cod_insumo:
        flash("Debe seleccionar un insumo.", "danger")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    try:
        cantidad = int(cantidad_raw)
    except (TypeError, ValueError):
        flash("La cantidad debe ser un número entero.", "danger")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    if cantidad <= 0:
        flash("La cantidad debe ser mayor a 0.", "danger")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    resultado = CompraModel.agregar_detalle(
        cod_compras=cod_compras,
        cod_insumo=cod_insumo,
        cantidad=cantidad,
        id_usuario_sesion=cedula,
    )

    if resultado['status']:
        insumo = CompraModel.obtener_insumo_por_id(cod_insumo)
        nombre = insumo['nombre_insumo'] if insumo else f"#{cod_insumo}"
        Bitacora.registrar(
            cedula,
            cod_accion=COD_ACCION_UPDATE,
            cod_modulo=COD_MODULO_COMPRA,
        )
        flash(resultado['mensaje'], "success")
    else:
        flash(resultado['mensaje'], "danger")

    return redirect(url_for('compras.detalle', cod_compras=cod_compras))


@compra_bp.route('/compra/<int:cod_compras>/detalle/<int:cod_det_compra>/eliminar',
                 methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_actualizar')
def eliminar_detalle(cod_compras, cod_det_compra):

    cedula = session['cedula_usuario']

    resultado = CompraModel.eliminar_detalle(
        cod_det_compra=cod_det_compra,
        id_usuario_sesion=cedula,
    )

    if resultado['status']:
        Bitacora.registrar(
            cedula,
            cod_accion=COD_ACCION_DELETE,
            cod_modulo=COD_MODULO_COMPRA,
        )
        flash(resultado['mensaje'], "success")
    else:
        flash(resultado['mensaje'], "danger")

    return redirect(url_for('compras.detalle', cod_compras=cod_compras))


@compra_bp.route('/compra/<int:cod_compras>/finalizar', methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_actualizar')
def finalizar(cod_compras):
    cedula = session['cedula_usuario']

    compra = CompraModel.obtener_por_id(cod_compras)
    if not compra:
        flash("Compra no encontrada.", "danger")
        return redirect(url_for('compras.listar'))

    if not compra.get('detalles'):
        flash("No se puede finalizar una compra sin insumos.", "warning")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    try:
        ok = CompraModel.actualizar_estado(
            cod_compras,
            ESTADO_COMPLETADA,
            id_usuario_sesion=cedula,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('compras.detalle', cod_compras=cod_compras))

    if ok:
        flash("Compra finalizada correctamente.", "success")
    else:
        flash("No se pudo finalizar la compra.", "danger")

    return redirect(url_for('compras.listar'))

@compra_bp.route('/compra/<int:cod_compras>/reactivar', methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_actualizar')
def reactivar(cod_compras):
    cedula = session['cedula_usuario']

    try:
        ok = CompraModel.actualizar_estado(
            cod_compras,
            'Pendiente',
            id_usuario_sesion=cedula,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('compras.listar'))

    if ok:
        flash(f"Compra #{cod_compras} reactivada como Pendiente.", "success")
    else:
        flash("No se pudo reactivar la compra.", "danger")

    return redirect(url_for('compras.listar'))

@compra_bp.route('/compra/<int:cod_compras>/eliminar', methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_eliminar')
def eliminar(cod_compras):
    cedula = session['cedula_usuario']

    resultado = CompraModel.eliminar(cod_compras, id_usuario_sesion=cedula)

    if resultado['status']:
        flash(resultado['mensaje'], "success")
    else:
        flash(resultado['mensaje'], "danger")

    return redirect(url_for('compras.listar'))


@compra_bp.route('/proveedores')
@login_required
@requiere_permiso('Compras', 'p_leer')
def listar_proveedores():
    proveedores = CompraModel.obtener_proveedores(solo_activos=False)
    return render_template('compras/proveedores.html', proveedores=proveedores)


@compra_bp.route('/proveedor/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_permiso('Compras', 'p_crear')
def nuevo_proveedor():
    if request.method == 'POST':
        rif = request.form.get('rif')
        razon_social = request.form.get('razon_social')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        cedula = session['cedula_usuario']

        if not all([rif, razon_social, direccion, telefono, correo]):
            flash("Todos los campos son obligatorios.", "danger")
            return render_template('compras/proveedor_nuevo.html')

        try:
            CompraModel.crear_proveedor(
                rif, razon_social, direccion, telefono, correo,
                id_usuario_sesion=cedula,
            )
        except Exception as e:
            flash(str(e), "danger")
            return render_template('compras/proveedor_nuevo.html')

        flash("Proveedor creado con éxito.", "success")
        return redirect(url_for('compras.listar_proveedores'))

    return render_template('compras/proveedor_nuevo.html')


@compra_bp.route('/proveedor/<int:rif>/editar', methods=['GET', 'POST'])
@login_required
@requiere_permiso('Compras', 'p_actualizar')
def editar_proveedor(rif):
    proveedor = CompraModel.obtener_proveedor_por_rif(rif)
    if not proveedor:
        flash("Proveedor no encontrado.", "danger")
        return redirect(url_for('compras.listar_proveedores'))

    if request.method == 'POST':
        razon_social = request.form.get('razon_social')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        estado = request.form.get('estado', 'Activo')
        cedula = session['cedula_usuario']

        if not all([razon_social, direccion, telefono, correo]):
            flash("Todos los campos son obligatorios.", "danger")
            return render_template('compras/proveedor_editar.html',
                                   proveedor=proveedor)

        try:
            ok = CompraModel.actualizar_proveedor(
                rif, razon_social, direccion, telefono, correo,
                estado=estado, id_usuario_sesion=cedula,
            )
        except Exception as e:
            flash(str(e), "danger")
            return render_template('compras/proveedor_editar.html',
                                   proveedor=proveedor)

        if ok:
            flash("Proveedor actualizado correctamente.", "success")
        else:
            flash("No se pudo actualizar el proveedor.", "danger")
        return redirect(url_for('compras.listar_proveedores'))

    return render_template('compras/proveedor_editar.html', proveedor=proveedor)


@compra_bp.route('/proveedor/<int:rif>/eliminar', methods=['POST'])
@login_required
@requiere_permiso('Compras', 'p_eliminar')
def eliminar_proveedor(rif):
    cedula = session['cedula_usuario']

    try:
        ok = CompraModel.eliminar_proveedor(rif, id_usuario_sesion=cedula)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('compras.listar_proveedores'))

    if ok:
        flash("Proveedor inactivado correctamente.", "success")
    else:
        flash("No se pudo inactivar el proveedor.", "danger")

    return redirect(url_for('compras.listar_proveedores'))