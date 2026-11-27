from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.citas import CitasModel
from utils.decorators import login_required
from models.bitacora import Bitacora
from utils.validaciones_citas import (
    validar_registro_cita, 
    validar_cambios_superusuario, 
    validar_cambios_hora_cliente
)
from utils.notificaciones_manager import NotificacionManager 

citas_bp = Blueprint('citas', __name__)

@citas_bp.route('/consultar')
@login_required
def consultar():
    cod_rol = session.get('cod_rol')
    cedula_usuario = session.get('cedula_usuario')

    if cod_rol == 1:
        # Super Usuario: Ve las citas de todos los usuarios
        lista_citas = CitasModel.obtener_citas_transito()
    elif cod_rol == 4:
        # Cliente: Solo ve sus propias citas
        lista_citas = CitasModel.obtener_por_cliente(cedula_usuario)
    else:
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for('index'))
       
    Bitacora.registrar(cedula_usuario, 2, 13)
    return render_template('citas/consultar.html', citas=lista_citas)


#Agendar------------------------------------------------------------------------
@citas_bp.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    cedula_usuario = session.get('cedula_usuario')
    cod_rol = session.get('cod_rol')

    if cod_rol not in [1, 4]:
        flash("No tienes permisos para agendar citas.", "danger")
        return redirect(url_for('citas.consultar'))
    
    from models.clientes import ClienteModel
    
    if request.method == 'POST':
        fecha = request.form.get('fecha_cita')
        hora = request.form.get('hora_cita')
        cod_catalogo = request.form.get('cod_catalogo')
        
        # Si es Super Usuario, la cita se agenda bajo la cédula del cliente elegido
        if cod_rol == 1:
            cedula_cliente = request.form.get('cedula_cliente')
            if not cedula_cliente:
                flash("Debe seleccionar un cliente.", "danger")
                vehiculos_catalogo = CitasModel.obtener_todos()
                clientes_list = ClienteModel.obtener_clientes()
                return render_template('citas/agendar.html', vehiculos=vehiculos_catalogo, clientes=clientes_list, datos=request.form)
            cedula_usuario = cedula_cliente
        
        datos_formulario = {
            'fecha': fecha,
            'hora': hora,
            'cod_catalogo': cod_catalogo
        }

        # Validar si el cliente ya tiene una cita pendiente con el mismo vehículo
        if CitasModel.cliente_tiene_cita_pendiente_vehiculo(cedula_usuario, cod_catalogo):
            flash("El cliente ya posee una cita en estado Pendiente para este vehículo. No se permite agendar otra cita hasta que sea procesada o cancelada.", "danger")
            vehiculos_catalogo = CitasModel.obtener_todos()
            clientes_list = ClienteModel.obtener_clientes() if cod_rol == 1 else None
            return render_template('citas/agendar.html', vehiculos=vehiculos_catalogo, clientes=clientes_list, datos=request.form)

        #Contar citas con el mismo horario
        total_concurrentes = CitasModel.contar_citas_en_horario(fecha, hora)

        es_valido, errores = validar_registro_cita(datos_formulario, total_concurrentes)

        if not es_valido:
            for campo, mensaje in errores.items():
                flash(f"{mensaje}", "danger")
            vehiculos_catalogo = CitasModel.obtener_todos()
            clientes_list = ClienteModel.obtener_clientes() if cod_rol == 1 else None
            return render_template('citas/agendar.html', vehiculos=vehiculos_catalogo, clientes=clientes_list, datos=request.form)

        try:
            CitasModel.registrar_citas(fecha, hora, cod_catalogo, cedula_usuario)
            Bitacora.registrar(session.get('cedula_usuario'), 1, 13)

            NotificacionManager.crear_multiple(
                notificacion_cliente={
                    "id_cliente": cedula_usuario,
                    "titulo": "Cita Agendada",
                    "mensaje": f"Tu cita ha sido agendada para el {fecha} a las {hora}.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                },
                notificacion_staff={
                    "roles": [1, 2, 3],
                    "titulo": "Nueva Cita Registrada",
                    "mensaje": f"El cliente {cedula_usuario} agendó una cita para el {fecha} a las {hora}.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                }
            )

            flash("¡Cita agendada con éxito!", "success")
            return redirect(url_for('citas.consultar'))
        except Exception as e:
            flash(f"Error al agendar la cita: {str(e)}", "danger")
            vehiculos_catalogo = CitasModel.obtener_todos()
            clientes_list = ClienteModel.obtener_clientes() if cod_rol == 1 else None
            return render_template('citas/agendar.html', vehiculos=vehiculos_catalogo, clientes=clientes_list, datos=request.form)
        
    vehiculos_catalogo = CitasModel.obtener_todos()
    clientes_list = ClienteModel.obtener_clientes() if cod_rol == 1 else None
    return render_template('citas/agendar.html', vehiculos=vehiculos_catalogo, clientes=clientes_list)

# Eliminar--------------------------------------------------------------------------------------------------------
@citas_bp.route('/eliminar/<int:cod_cita>', methods=['POST'])
@login_required
def eliminar_cita(cod_cita):
    cod_rol = session.get('cod_rol')
    cedula_usuario = session.get('cedula_usuario')

    cita_orig = CitasModel.obtener_cita_por_id(cod_cita)
    # CP-CITA-50 - INICIO CORRECCIÓN
    cliente_target = (cita_orig.get('cedula_usuario') if cita_orig else None) or cedula_usuario
    # CP-CITA-50 - FIN CORRECCIÓN

    if cod_rol == 4:
        resultado = CitasModel.eliminar_cita_db(cod_cita, cedula_usuario=cedula_usuario)
        if resultado['status']:
            Bitacora.registrar(cedula_usuario, 4, 13)
            NotificacionManager.crear_multiple(
                notificacion_cliente={
                    "id_cliente": cliente_target,
                    "titulo": "Cita Cancelada",
                    "mensaje": f"Tu cita #{cod_cita} ha sido eliminada/cancelada.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                },
                notificacion_staff={
                    "roles": [1, 2, 3],
                    "titulo": "Cita Cancelada por Cliente",
                    "mensaje": f"La cita #{cod_cita} del cliente {cliente_target} fue cancelada.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                }
            )
            flash(resultado['mensaje'], "success")
        else:
            flash(resultado['mensaje'], "danger")
    # Si es Super Usuario, tiene el borrado físico sin restricciones
    elif cod_rol == 1:
        resultado = CitasModel.eliminar_cita_db(cod_cita)
        if resultado['status']:
            Bitacora.registrar(cedula_usuario, 4, 13)
            NotificacionManager.crear_multiple(
                notificacion_cliente={
                    "id_cliente": cliente_target,
                    "titulo": "Cita Cancelada por la Administración",
                    "mensaje": f"Tu cita #{cod_cita} ha sido eliminada por la administración.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                },
                notificacion_staff={
                    "roles": [1, 2, 3],
                    "titulo": "Cita Eliminada",
                    "mensaje": f"La cita #{cod_cita} fue eliminada del sistema.",
                    "url_destino": "/consultar",
                    "modulo": "citas"
                }
            )
            flash("Cita eliminada del sistema con éxito.", "warning")
        else:
            flash(resultado['mensaje'], "danger")
    else:
        flash("No tienes permisos para realizar esta acción.", "danger")

    return redirect(url_for('citas.consultar'))

# Modificar----------------------------------------------------------------------------
@citas_bp.route('/modificar/<int:cod_cita>', methods=['POST'])
@login_required
def modificar(cod_cita):
    cod_rol = session.get('cod_rol')
    cedula_usuario = session.get('cedula_usuario')

    cita_original = CitasModel.obtener_cita_por_id(cod_cita)
    if not cita_original:
        flash("No se pudo localizar la cita seleccionada.", "danger")
        return redirect(url_for('citas.consultar'))

    if cod_rol == 4: # cliente
        citas_cliente = CitasModel.obtener_por_cliente(cedula_usuario)
        pertenece = any(int(c['cod_citas']) == int(cod_cita) for c in citas_cliente)
        if not pertenece:
            flash("Acceso denegado: No tienes autorización sobre esta cita.", "danger")
            return redirect(url_for('citas.consultar'))

        nueva_hora = request.form.get('hora')
        fecha_cita = str(cita_original['fecha'])
        estado_cita = str(cita_original['estado'])

        # Contar citas en la misma fecha y la nueva hora (excluyendo esta cita)
        total_concurrentes = CitasModel.contar_citas_en_horario(fecha_cita, nueva_hora, cod_cita_excluir=cod_cita)

        es_valido, errores = validar_cambios_hora_cliente(
            nueva_hora, fecha_cita, estado_cita, total_concurrentes
        )

        if not es_valido:
            for campo, mensaje in errores.items():
                flash(f"{mensaje}", "danger")
            return redirect(url_for('citas.consultar'))

        datos_formulario = {
            'cod_citas': cod_cita,
            'fecha': fecha_cita,
            'hora': nueva_hora,
            'estado': estado_cita
        }

    elif cod_rol == 1:
        fecha_req = request.form.get('fecha') or str(cita_original['fecha'])
        hora_req = request.form.get('hora') or str(cita_original['hora'])
        estado_req = request.form.get('estado') or str(cita_original['estado'])

        datos_formulario = {
            'cod_citas': cod_cita,
            'fecha': fecha_req,
            'hora': hora_req,
            'estado': estado_req
        }

        total_concurrentes = CitasModel.contar_citas_en_horario(fecha_req, hora_req, cod_cita_excluir=cod_cita)

        es_valido, errores = validar_cambios_superusuario(datos_formulario, total_concurrentes)

        if not es_valido:
            for campo, mensaje in errores.items():
                flash(f"{mensaje}", "danger")
            return redirect(url_for('citas.consultar'))
    else:
        flash("No tienes permisos para modificar citas.", "danger")
        return redirect(url_for('citas.consultar'))

    try:
        CitasModel.actualizar_cita(datos_formulario)
        Bitacora.registrar(cedula_usuario, 3, 13)

        cliente_target = cita_original.get('cedula_usuario') or cedula_usuario
        f_final = datos_formulario.get('fecha')
        h_final = datos_formulario.get('hora')

        NotificacionManager.crear_multiple(
            notificacion_cliente={
                "id_cliente": cliente_target,
                "titulo": "Cita Reprogramada",
                "mensaje": f"Tu cita #{cod_cita} ha sido reprogramada para el {f_final} a las {h_final}.",
                "url_destino": "/consultar",
                "modulo": "citas"
            },
            notificacion_staff={
                "roles": [1, 2, 3],
                "titulo": "Cita Reprogramada",
                "mensaje": f"La cita #{cod_cita} del cliente {cliente_target} se cambió a {f_final} a las {h_final}.",
                "url_destino": "/consultar",
                "modulo": "citas"
            }
        )

        flash("La cita ha sido reprogramada y actualizada con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar modificaciones: {str(e)}", "danger")
        
    return redirect(url_for('citas.consultar'))


# Finalizar----------------------------------------------------------------------------
@citas_bp.route('/finalizar/<int:cod_citas>', methods=['POST'])
@login_required
def finalizar_cita(cod_citas):
    cod_rol = session.get('cod_rol')

    if cod_rol != 1:
        flash("Acceso denegado: Solo el Super Usuario puede finalizar citas.", "danger")
        return redirect(url_for('citas.consultar'))

    cita_orig = CitasModel.obtener_cita_por_id(cod_citas)
    cliente_target = cita_orig.get('cedula_usuario') if cita_orig else None

    CitasModel.finalizar_cita_db(cod_citas)
    Bitacora.registrar(session.get('cedula_usuario'), 3, 13)

    NotificacionManager.crear_multiple(
        notificacion_cliente={
            "id_cliente": cliente_target,
            "titulo": "Cita Completada",
            "mensaje": f"Tu cita #{cod_citas} ha sido marcada como finalizada.",
            "url_destino": "/consultar",
            "modulo": "citas"
        },
        notificacion_staff={
            "roles": [1, 2, 3],
            "titulo": "Cita Finalizada",
            "mensaje": f"La cita #{cod_citas} fue marcada como finalizada.",
            "url_destino": "/consultar",
            "modulo": "citas"
        }
    )

    flash("¡La cita ha sido marcada como Finalizada!", "success")
    return redirect(url_for('citas.consultar'))