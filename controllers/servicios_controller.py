from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.servicios import Servicios
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

servicios_bp = Blueprint('servicios', __name__)


@servicios_bp.route('/servicios')
@requiere_permiso('servicios', 'p_leer')
def listar_servicios():
    cedula_usuario = session.get('cedula_usuario')
    servicios = Servicios.obtener_servicios(cedula_usuario)
    vehiculos = Servicios.obtener_vehiculos()
    return render_template(
        'servicios/index.html',
        servicios=servicios,
        vehiculos=vehiculos
    )


@servicios_bp.route('/servicios/nuevo', methods=['GET', 'POST'])
@requiere_permiso('servicios', 'p_crear')
def crear_servicio():
    vehiculos = Servicios.obtener_vehiculos_disponibles()

    if request.method == 'POST':
        nombre_servicio = request.form.get('nombre_servicio', '').strip()
        costo_base = request.form.get('costo_base', '').strip()
        costo_final = request.form.get('costo_final', '').strip()
        descripcion_especifica = request.form.get('descripcion_especifica', '').strip()
        fecha_realizacion = request.form.get('fecha_realizacion', '').strip()
        placa = request.form.get('placa', '').strip()
        cedula_usuario = session.get('cedula_usuario')

        resultado = Servicios.guardar(
            nombre_servicio,
            costo_base if costo_base else None,
            costo_final if costo_final else None,
            descripcion_especifica,
            fecha_realizacion,
            placa,
            cedula_usuario
        )

        if not resultado.get('status'):
            flash(resultado.get('mensaje', 'No se pudo registrar el servicio.'), 'danger')
            return render_template('servicios/form.html', vehiculos=vehiculos, servicio=None)

        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Nuevo Servicio Registrado",
                "mensaje": f"Se registró el servicio '{nombre_servicio}' para el vehículo {placa}.",
                "url_destino": url_for('servicios.listar_servicios'),
                "modulo": "servicios"
            }
        )

        flash(resultado.get('mensaje', 'Servicio registrado correctamente.'), 'success')
        return redirect(url_for('servicios.listar_servicios'))

    return render_template('servicios/form.html', vehiculos=vehiculos, servicio=None)


@servicios_bp.route('/servicios/editar/<int:cod_servicios>', methods=['GET', 'POST'])
@requiere_permiso('servicios', 'p_actualizar')
def editar_servicio(cod_servicios):
    servicio = Servicios.obtener_servicio_por_codigo(cod_servicios)
    vehiculos = Servicios.obtener_vehiculos()

    if not servicio:
        flash('El servicio no existe.', 'danger')
        return redirect(url_for('servicios.listar_servicios'))

    if isinstance(servicio, dict):
        if servicio.get('costo_base') in [None, 'None', '']:
            servicio['costo_base'] = 0
        if servicio.get('costo_final') in [None, 'None', '']:
            servicio['costo_final'] = 0
    else:
        if getattr(servicio, 'costo_base', None) in [None, 'None', '']:
            setattr(servicio, 'costo_base', 0)
        if getattr(servicio, 'costo_final', None) in [None, 'None', '']:
            setattr(servicio, 'costo_final', 0)

    if request.method == 'POST':
        nombre_servicio = request.form.get('nombre_servicio', '').strip()
        costo_base = request.form.get('costo_base', '').strip()
        costo_final = request.form.get('costo_final', '').strip()
        descripcion_especifica = request.form.get('descripcion_especifica', '').strip()
        fecha_realizacion = request.form.get('fecha_realizacion', '').strip()
        
        placa = servicio['placa'] if isinstance(servicio, dict) else servicio.placa
        cedula_usuario = session.get('cedula_usuario')

        resultado = Servicios.actualizar(
            cod_servicios,
            nombre_servicio,
            costo_base if costo_base else None,
            costo_final if costo_final else None,
            descripcion_especifica,
            fecha_realizacion,
            placa,
            cedula_usuario
        )

        if not resultado.get('status'):
            flash(resultado.get('mensaje', 'No se pudo actualizar el servicio.'), 'danger')
            return render_template('servicios/form.html', vehiculos=vehiculos, servicio=servicio)

        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Servicio Actualizado",
                "mensaje": f"Se actualizó el servicio '{nombre_servicio}' del vehículo {placa}.",
                "url_destino": url_for('servicios.listar_servicios'),
                "modulo": "servicios"
            }
        )

        flash(resultado.get('mensaje', 'Servicio actualizado correctamente.'), 'success')
        return redirect(url_for('servicios.listar_servicios'))

    return render_template(
        'servicios/form.html',
        vehiculos=vehiculos,
        servicio=servicio
    )


@servicios_bp.route('/servicios/inactivar/<int:cod_servicios>', methods=['POST'])
@requiere_permiso('servicios', 'p_eliminar')
def inactivar_servicio(cod_servicios):
    cedula_usuario = session.get('cedula_usuario')
    resultado = Servicios.inactivar(cod_servicios, cedula_usuario)

    if not resultado.get('status'):
        flash(resultado.get('mensaje', 'No se pudo inactivar el servicio.'), 'danger')
    else:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Servicio Inactivado",
                "mensaje": f"El servicio #{cod_servicios} ha sido inactivado.",
                "url_destino": url_for('servicios.listar_servicios'),
                "modulo": "servicios"
            }
        )
        flash(resultado.get('mensaje', 'Servicio inactivado correctamente.'), 'success')

    return redirect(url_for('servicios.listar_servicios'))


@servicios_bp.route('/servicios/finalizar/<int:cod_servicios>/<string:placa>', methods=['POST'])
@requiere_permiso('servicios', 'p_actualizar')
def finalizar_servicio(cod_servicios, placa):
    cedula_usuario = session.get('cedula_usuario')
    costo_final = request.form.get('costo_final', '').strip()
    resultado = Servicios.finalizar(cod_servicios, placa, cedula_usuario, costo_final if costo_final else None)

    if not resultado.get('status'):
        flash(resultado.get('mensaje', 'No se pudo finalizar el servicio.'), 'danger')
    else:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Servicio Finalizado",
                "mensaje": f"El servicio #{cod_servicios} del vehículo {placa} ha sido finalizado.",
                "url_destino": url_for('servicios.listar_servicios'),
                "modulo": "servicios"
            }
        )
        flash(resultado.get('mensaje', 'Servicio finalizado y vehículo reactivado.'), 'success')

    return redirect(url_for('servicios.listar_servicios'))


@servicios_bp.route('/servicios/recibo/<int:cod_servicios>')
@requiere_permiso('servicios', 'p_leer')
def ver_recibo_servicio(cod_servicios):
    servicio = Servicios.obtener_servicio_por_codigo(cod_servicios)
    if not servicio:
        flash('El servicio no existe.', 'danger')
        return redirect(url_for('servicios.listar_servicios'))
    return render_template('servicios/recibo.html', servicio=servicio)