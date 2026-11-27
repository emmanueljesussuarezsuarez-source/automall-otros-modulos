from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models.taller import Taller
from utils.permisos import requiere_permiso, requiere_superusuario
from utils.notificaciones_manager import NotificacionManager


tallerbp = Blueprint('tallerbp', __name__)


@tallerbp.route('/taller')
@requiere_permiso('Taller', 'p_leer')
def listar_talleres():
    cedula_usuario = session.get('cedula_usuario')
    talleres = Taller.obtener_todos(cedula_usuario)
    return render_template(
        'taller/index.html',
        talleres=talleres
    )


@tallerbp.route('/taller/nuevo', methods=['POST'])
@requiere_permiso('Taller', 'p_crear')
def crear_taller():
    nombre_taller = request.form.get('nombre_taller', '').strip()
    direccion = request.form.get('direccion', '').strip()
    estado = request.form.get('estado', '1').strip()
    cedula_usuario = session.get('cedula_usuario')

    resultado = Taller.guardar(
        nombre_taller,
        direccion,
        estado,
        cedula_usuario
    )

    if not resultado.get('status'):
        flash(
            resultado.get(
                'mensaje',
                'No se pudo registrar el taller.'
            ),
            'danger'
        )
        return redirect(
            url_for('tallerbp.listar_talleres')
        )

    NotificacionManager.crear_multiple(
        notificacion_staff={
            "roles": [1, 2],
            "titulo": "Nuevo Taller Registrado",
            "mensaje": f"Se ha registrado el taller '{nombre_taller}'.",
            "url_destino": url_for('tallerbp.listar_talleres'),
            "modulo": "taller"
        }
    )

    flash(
        resultado.get(
            'mensaje',
            'Taller registrado correctamente.'
        ),
        'success'
    )

    return redirect(
        url_for('tallerbp.listar_talleres')
    )


@tallerbp.route('/taller/editar/<int:cod_taller>', methods=['POST'])
@requiere_permiso('Taller', 'p_actualizar')
def editar_taller(cod_taller):
    taller = Taller.obtener_por_id(cod_taller)

    if not taller:
        flash('El taller no existe.', 'danger')
        return redirect(
            url_for('tallerbp.listar_talleres')
        )

    nombre_taller = request.form.get(
        'nombre_taller',
        ''
    ).strip()

    direccion = request.form.get(
        'direccion',
        ''
    ).strip()

    estado = request.form.get(
        'estado',
        '1'
    ).strip()

    cedula_usuario = session.get('cedula_usuario')

    resultado = Taller.actualizar(
        cod_taller,
        nombre_taller,
        direccion,
        estado,
        cedula_usuario
    )

    if not resultado.get('status'):
        flash(
            resultado.get(
                'mensaje',
                'No se pudo actualizar el taller.'
            ),
            'danger'
        )
        return redirect(
            url_for('tallerbp.listar_talleres')
        )

    NotificacionManager.crear_multiple(
        notificacion_staff={
            "roles": [1, 2],
            "titulo": "Taller Actualizado",
            "mensaje": f"Se han actualizado los datos del taller '{nombre_taller}'.",
            "url_destino": url_for('tallerbp.listar_talleres'),
            "modulo": "taller"
        }
    )

    flash(
        resultado.get(
            'mensaje',
            'Taller actualizado correctamente.'
        ),
        'success'
    )

    return redirect(
        url_for('tallerbp.listar_talleres')
    )


@tallerbp.route('/taller/eliminar/<int:cod_taller>', methods=['POST'])
@requiere_permiso('Taller', 'p_eliminar')
def eliminar_taller(cod_taller):
    cedula_usuario = session.get('cedula_usuario')
    taller = Taller.obtener_por_id(cod_taller)
    nombre_taller = taller.get('nombre_taller') if taller else 'Taller'

    resultado = Taller.eliminar(
        cod_taller,
        cedula_usuario
    )

    if not resultado.get('status'):
        flash(
            resultado.get(
                'mensaje',
                'No se pudo desactivar el taller.'
            ),
            'danger'
        )
    else:
        NotificacionManager.crear_multiple(
            notificacion_staff={
                "roles": [1, 2],
                "titulo": "Taller Desactivado",
                "mensaje": f"El taller '{nombre_taller}' ha sido desactivado del sistema.",
                "url_destino": url_for('tallerbp.listar_talleres'),
                "modulo": "taller"
            }
        )

        flash(
            resultado.get(
                'mensaje',
                'Taller desactivado correctamente.'
            ),
            'success'
        )

    return redirect(
        url_for('tallerbp.listar_talleres')
    )