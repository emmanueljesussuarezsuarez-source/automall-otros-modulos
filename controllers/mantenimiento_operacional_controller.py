from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.mantenimiento_operacional import MantenimientoOperacional
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager


mantenimiento_operacional_bp = Blueprint('mantenimiento_operacional', __name__)


@mantenimiento_operacional_bp.route('/mantenimiento-operacional')
@requiere_permiso('mantenimiento_operacional', 'p_leer')
def listar_mantenimiento():
    cedula_usuario = session.get('cedula_usuario')
    mantenimientos = MantenimientoOperacional.obtener_mantenimientos(cedula_usuario)
    talleres = MantenimientoOperacional.obtener_talleres()
    vehiculos = MantenimientoOperacional.obtener_vehiculos_disponibles()
    return render_template(
        'mantenimiento_operacional/index.html',
        mantenimientos=mantenimientos,
        talleres=talleres,
        vehiculos=vehiculos,
        mostrar_modal_finalizar=False,
        mantenimiento_seleccionado=None,
        detalles_existentes=[]
    )


@mantenimiento_operacional_bp.route('/mantenimiento-operacional/crear', methods=['GET', 'POST'])
@requiere_permiso('mantenimiento_operacional', 'p_crear')
def crear_mantenimiento():
    talleres = MantenimientoOperacional.obtener_talleres()
    vehiculos = MantenimientoOperacional.obtener_vehiculos()
    usuarios_autorizadores = MantenimientoOperacional.obtener_usuarios_autorizadores()


    if request.method == 'POST':
        descripcion_general = request.form.get('descripcion_general', '').strip()
        quien_autoriza = request.form.get('quien_autoriza', '').strip()
        tipo = request.form.get('tipo', '').strip()
        fecha_solicitud = request.form.get('fecha_solicitud', '').strip()
        fecha_completada = request.form.get('fecha_completada', '').strip()
        placa = request.form.get('placa', '').strip()
        cod_taller = request.form.get('cod_taller', '').strip()
        cedula_usuario = session.get('cedula_usuario')
        costo_base = request.form.get('costo_base', '').strip() or None
        costo_final = request.form.get('costo_final', '').strip() or None


        detalles = []
        idx = 0
        while True:
            desc = request.form.get(f'descripcion_detalle_{idx}', '').strip()
            cant = request.form.get(f'cantidad_{idx}', '').strip()
            if not desc and not cant:
                break
            detalles.append({
                'descripcion_detalle': desc if desc else None,
                'cantidad': int(cant) if cant else None
            })
            idx += 1


        if not descripcion_general or not quien_autoriza or not tipo or not fecha_solicitud or not placa or not cod_taller:
            flash('Completa todos los campos obligatorios.', 'warning')
            return render_template(
                'mantenimiento_operacional/form.html',
                talleres=talleres,
                vehiculos=vehiculos,
                usuarios_autorizadores=usuarios_autorizadores,
                mantenimiento=None
            )


        resultado = MantenimientoOperacional.guardar(
            descripcion_general,
            quien_autoriza,
            tipo,
            fecha_solicitud,
            fecha_completada if fecha_completada else None,
            placa,
            cod_taller,
            cedula_usuario,
            costo_base=float(costo_base) if costo_base else None,
            costo_final=float(costo_final) if costo_final else None,
            detalles=detalles if detalles else None
        )


        if not resultado.get('status'):
            flash(resultado.get('mensaje', 'Ocurrió un error al guardar el mantenimiento.'), 'danger')
            return render_template(
                'mantenimiento_operacional/form.html',
                talleres=talleres,
                vehiculos=vehiculos,
                usuarios_autorizadores=usuarios_autorizadores,
                mantenimiento=None
            )


        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Nuevo Mantenimiento Registrado",
                "mensaje": f"Se registró un mantenimiento para el vehículo {placa}.",
                "url_destino": url_for('mantenimiento_operacional.listar_mantenimiento'),
                "modulo": "mantenimiento_operacional"
            }
        )


        flash(resultado.get('mensaje', 'Mantenimiento registrado correctamente.'), 'success')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    return render_template(
        'mantenimiento_operacional/form.html',
        talleres=talleres,
        vehiculos=vehiculos,
        usuarios_autorizadores=usuarios_autorizadores,
        mantenimiento=None
    )


@mantenimiento_operacional_bp.route('/mantenimiento-operacional/editar/<int:cod_mantenimiento>', methods=['GET', 'POST'])
@requiere_permiso('mantenimiento_operacional', 'p_actualizar')
def editar_mantenimiento(cod_mantenimiento):
    talleres = MantenimientoOperacional.obtener_talleres()
    vehiculos = MantenimientoOperacional.obtener_vehiculos()
    usuarios_autorizadores = MantenimientoOperacional.obtener_usuarios_autorizadores()
    mantenimientos = MantenimientoOperacional.obtener_mantenimientos()


    mantenimiento = None
    for m in mantenimientos:
        if m['cod_mantenimiento'] == cod_mantenimiento:
            mantenimiento = m
            break


    if not mantenimiento:
        flash('Mantenimiento no encontrado.', 'warning')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    detalles = MantenimientoOperacional.obtener_detalle_por_mantenimiento(cod_mantenimiento)


    if request.method == 'POST':
        descripcion_general = request.form.get('descripcion_general', '').strip()
        quien_autoriza = request.form.get('quien_autoriza', '').strip()
        tipo = request.form.get('tipo', '').strip()
        fecha_solicitud = request.form.get('fecha_solicitud', '').strip()
        fecha_completada = request.form.get('fecha_completada', '').strip()
        cod_taller = request.form.get('cod_taller', '').strip()
        cedula_usuario = session.get('cedula_usuario')
        costo_base = request.form.get('costo_base', '').strip() or None
        costo_final = request.form.get('costo_final', '').strip() or None


        detalles = []
        idx = 0
        while True:
            desc = request.form.get(f'descripcion_detalle_{idx}', '').strip()
            cant = request.form.get(f'cantidad_{idx}', '').strip()
            if not desc and not cant:
                break
            detalles.append({
                'descripcion_detalle': desc if desc else None,
                'cantidad': int(cant) if cant else None
            })
            idx += 1


        placa = mantenimiento['placa']


        if not descripcion_general or not quien_autoriza or not tipo or not fecha_solicitud or not placa or not cod_taller:
            flash('Completa todos los campos obligatorios.', 'warning')
            return render_template(
                'mantenimiento_operacional/form.html',
                talleres=talleres,
                vehiculos=vehiculos,
                usuarios_autorizadores=usuarios_autorizadores,
                mantenimiento=mantenimiento
            )


        resultado = MantenimientoOperacional.actualizar(
            cod_mantenimiento,
            descripcion_general,
            quien_autoriza,
            tipo,
            fecha_solicitud,
            fecha_completada if fecha_completada else None,
            placa,
            cod_taller,
            cedula_usuario,
            costo_base=float(costo_base) if costo_base else None,
            costo_final=float(costo_final) if costo_final else None,
            detalles=detalles if detalles else None
        )


        if not resultado.get('status'):
            flash(resultado.get('mensaje', 'Ocurrió un error al actualizar el mantenimiento.'), 'danger')
            return render_template(
                'mantenimiento_operacional/form.html',
                talleres=talleres,
                vehiculos=vehiculos,
                usuarios_autorizadores=usuarios_autorizadores,
                mantenimiento=mantenimiento
            )


        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Mantenimiento Actualizado",
                "mensaje": f"Se actualizaron los datos del mantenimiento #{cod_mantenimiento}.",
                "url_destino": url_for('mantenimiento_operacional.listar_mantenimiento'),
                "modulo": "mantenimiento_operacional"
            }
        )


        flash(resultado.get('mensaje', 'Mantenimiento actualizado correctamente.'), 'success')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    return render_template(
        'mantenimiento_operacional/form.html',
        talleres=talleres,
        vehiculos=vehiculos,
        usuarios_autorizadores=usuarios_autorizadores,
        mantenimiento=mantenimiento,
        detalles=detalles
    )


@mantenimiento_operacional_bp.route('/mantenimiento-operacional/inactivar/<int:cod_mantenimiento>', methods=['POST'])
@requiere_permiso('mantenimiento_operacional', 'p_actualizar')
def inactivar_mantenimiento(cod_mantenimiento):
    try:
        cedula_usuario = session.get('cedula_usuario')
        MantenimientoOperacional.inactivar(cod_mantenimiento, cedula_usuario)


        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Mantenimiento Inactivado",
                "mensaje": f"El mantenimiento #{cod_mantenimiento} ha sido inactivado.",
                "url_destino": url_for('mantenimiento_operacional.listar_mantenimiento'),
                "modulo": "mantenimiento_operacional"
            }
        )


        flash('Mantenimiento inactivado correctamente.', 'success')
    except Exception:
        flash('Ocurrió un error al inactivar el mantenimiento.', 'danger')


    return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


@mantenimiento_operacional_bp.route('/mantenimiento-operacional/finalizar/<int:cod_mantenimiento>/<placa>', methods=['GET', 'POST'])
@requiere_permiso('mantenimiento_operacional', 'p_actualizar')
def finalizar_mantenimiento(cod_mantenimiento, placa):
    cedula_usuario = session.get('cedula_usuario')
    mantenimiento = None
    mantenimientos = MantenimientoOperacional.obtener_mantenimientos()
    for m in mantenimientos:
        if m['cod_mantenimiento'] == cod_mantenimiento:
            mantenimiento = m
            break


    if not mantenimiento:
        flash('Mantenimiento no encontrado.', 'warning')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    detalles_existentes = MantenimientoOperacional.obtener_detalle_por_mantenimiento(cod_mantenimiento)


    if request.method == 'POST':
        costo_final = request.form.get('costo_final', '').strip() or None
        
        detalles = []
        idx = 0
        while True:
            desc = request.form.get(f'descripcion_detalle_{idx}', '').strip()
            cant = request.form.get(f'cantidad_{idx}', '').strip()
            if not desc and not cant:
                break
            detalles.append({
                'descripcion_detalle': desc if desc else None,
                'cantidad': int(cant) if cant else None
            })
            idx += 1
        
        try:
            MantenimientoOperacional.finalizar(
                cod_mantenimiento,
                placa,
                cedula_usuario,
                costo_final=float(costo_final) if costo_final else None,
                detalles=detalles if detalles else None
            )


            NotificacionManager.crear_multiple(
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Mantenimiento Finalizado",
                    "mensaje": f"El mantenimiento #{cod_mantenimiento} del vehículo {placa} ha sido finalizado.",
                    "url_destino": url_for('mantenimiento_operacional.listar_mantenimiento'),
                    "modulo": "mantenimiento_operacional"
                }
            )


            flash('Mantenimiento finalizado correctamente.', 'success')
        except Exception as e:
            flash(f'Ocurrió un error al finalizar el mantenimiento: {str(e)}', 'danger')


        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    # Si es GET, mostrar el modal en el index
    return render_template(
        'mantenimiento_operacional/index.html',
        mantenimientos=mantenimientos,
        talleres=MantenimientoOperacional.obtener_talleres(),
        vehiculos=MantenimientoOperacional.obtener_vehiculos_disponibles(),
        mostrar_modal_finalizar=True,
        mantenimiento_seleccionado=mantenimiento,
        detalles_existentes=detalles_existentes
    )


@mantenimiento_operacional_bp.route('/mantenimiento-operacional/ver-recibo/<int:cod_mantenimiento>')
@requiere_permiso('mantenimiento_operacional', 'p_leer')
def ver_recibo(cod_mantenimiento):
    mantenimientos = MantenimientoOperacional.obtener_mantenimientos()
    mantenimiento = None
    for m in mantenimientos:
        if m['cod_mantenimiento'] == cod_mantenimiento:
            mantenimiento = m
            break


    if not mantenimiento:
        flash('Mantenimiento no encontrado.', 'warning')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))


    detalles = MantenimientoOperacional.obtener_detalle_por_mantenimiento(cod_mantenimiento)
    
    return render_template(
        'mantenimiento_operacional/recibo.html',
        mantenimiento=mantenimiento,
        detalles=detalles
    )