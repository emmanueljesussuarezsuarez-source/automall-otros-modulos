import re
from datetime import datetime, timedelta

def buscar_horario_disponible(fecha_inicial, hora_inicial):

# Busca el horario diponibnle mas cercano. Maximo 3 citas en la misma hora
   
    formato_fecha = "%Y-%m-%d"
    formato_hora = "%H:%M"
    
    try:
        hora_limpia = hora_inicial.strip()[:5]
        dt_actual = datetime.strptime(f"{fecha_inicial.strip()} {hora_limpia}", f"{formato_fecha} {formato_hora}")
    except Exception:
        dt_actual = datetime.now() + timedelta(days=1)
        dt_actual = dt_actual.replace(hour=8, minute=0, second=0, microsecond=0)

    if dt_actual.hour < 8:
        dt_actual = dt_actual.replace(hour=8, minute=0)
    elif dt_actual.hour >= 18:
        dt_actual = (dt_actual + timedelta(days=1)).replace(hour=8, minute=0)

    limite = dt_actual + timedelta(days=10)
    
    from models.citas import CitasModel

    while dt_actual < limite:
        # Saltar domingos
        if dt_actual.weekday() == 6:
            dt_actual = (dt_actual + timedelta(days=1)).replace(hour=8, minute=0)
            continue
            
        fecha_str = dt_actual.strftime(formato_fecha)
        hora_str = dt_actual.strftime("%H:%M:%S")
        
        cantidad_citas = CitasModel.contar_citas_en_horario(fecha_str, hora_str)
        if cantidad_citas < 3:
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias_semana[dt_actual.weekday()]
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            nombre_mes = meses[dt_actual.month - 1]
            
            fecha_legible = f"{nombre_dia}, {dt_actual.day} de {nombre_mes}"
            hora_legible = dt_actual.strftime("%I:%M %p")
            
            return {
                "fecha": fecha_str,
                "hora": hora_str,
                "fecha_legible": fecha_legible,
                "hora_legible": hora_legible
            }

        dt_actual += timedelta(minutes=30)
        
        if dt_actual.hour > 18 or (dt_actual.hour == 18 and dt_actual.minute > 0):
            dt_actual = (dt_actual + timedelta(days=1)).replace(hour=8, minute=0)
            
    return None


def validar_registro_cita(datos, citas_actuales, limite_maximo=3):
    
    errores = {}
    
    fecha = datos.get('fecha')
    if not fecha:
        errores['fecha'] = "Debe ingresar una fecha para la cita."
    else:
        try:
            datetime.strptime(fecha.strip(), '%Y-%m-%d')
        except ValueError:
            errores['fecha'] = "El formato de la fecha es incorrecto. Use el selector."

    hora = datos.get('hora')
    if not hora:
        errores['hora'] = "Debe ingresar una hora para la cita."
    else:
        try:
            hora_limpia = hora.strip()[:5]
            datetime.strptime(hora_limpia, '%H:%M')
        except ValueError:
            errores['hora'] = "El formato de la hora es incorrecto. Use el selector."
            
    cod_catalogo = datos.get('cod_catalogo')
    if not cod_catalogo:
        errores['cod_catalogo'] = "Debe seleccionar un vehículo del catálogo."

    if not errores:
        if citas_actuales >= limite_maximo:
            sugerencia = buscar_horario_disponible(fecha, hora)
            if sugerencia:
                errores['horario'] = (
                    f"Disponibilidad agotada en este horario. "
                    f"Te sugerimos agendar el: {sugerencia['fecha_legible']} a las {sugerencia['hora_legible']}."
                )
            else:
                errores['horario'] = "Disponibilidad agotada para el horario seleccionado."

    return len(errores) == 0, errores


def validar_cambios_superusuario(datos, citas_actuales, limite_maximo=3):

    errores = {}
    
    cod_citas = datos.get('cod_citas')
    if not cod_citas or not str(cod_citas).isdigit():
        errores['cod_citas'] = "Identificador de cita inválido."

    fecha = datos.get('fecha')
    if not fecha:
        errores['fecha'] = "Debe ingresar una fecha."
    else:
        try:
            datetime.strptime(fecha.strip(), '%Y-%m-%d')
        except ValueError:
            errores['fecha'] = "Formato de fecha inválido."

    hora = datos.get('hora')
    if not hora:
        errores['hora'] = "Debe ingresar una hora."
    else:
        try:
            hora_limpia = hora.strip()[:5]
            datetime.strptime(hora_limpia, '%H:%M')
        except ValueError:
            errores['hora'] = "Formato de hora inválido."

    estado = datos.get('estado')
    if not estado or estado.strip() not in ['Pendiente', 'Finalizada']:
        errores['estado'] = "El estado seleccionado es incorrecto."

    if not errores:
        if citas_actuales >= limite_maximo:
            sugerencia = buscar_horario_disponible(fecha, hora)
            if sugerencia:
                errores['horario'] = (
                    f"Disponibilidad agotada en este horario. "
                    f"Sugerencia alternativa: {sugerencia['fecha_legible']} a las {sugerencia['hora_legible']}."
                )
            else:
                errores['horario'] = "Disponibilidad agotada para el horario seleccionado."

    return len(errores) == 0, errores


def validar_cambios_hora_cliente(nueva_hora, fecha_cita, estado_cita, citas_actuales, limite_maximo=3):

    errores = {}

    if estado_cita != 'Pendiente':
        errores['estado'] = "Solo puedes modificar la hora de citas que estén en estado 'Pendiente'."

    if not nueva_hora:
        errores['hora'] = "Debe ingresar una nueva hora."
    else:
        try:
            hora_limpia = nueva_hora.strip()[:5]
            datetime.strptime(hora_limpia, '%H:%M')
        except ValueError:
            errores['hora'] = "Formato de hora inválido."

    if not errores:
        if citas_actuales >= limite_maximo:
            sugerencia = buscar_horario_disponible(fecha_cita, nueva_hora)
            if sugerencia:
                errores['horario'] = (
                    f"Disponibilidad agotada en este horario. "
                    f"Te sugerimos agendar el: {sugerencia['fecha_legible']} a las {sugerencia['hora_legible']}."
                )
            else:
                errores['horario'] = "Disponibilidad agotada para el horario seleccionado."

    return len(errores) == 0, errores