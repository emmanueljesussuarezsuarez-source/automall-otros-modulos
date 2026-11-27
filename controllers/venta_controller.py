import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from flask import jsonify, make_response
from models.ventas import Ventas
from models.user import Usuario
from models.vehiculo import Vehiculo
from utils.decorators import login_required
from utils.permisos import requiere_permiso
from fpdf import FPDF
from models.clientes import ClienteModel
from models.bitacora import Bitacora
from utils.notificaciones_manager import NotificacionManager

ventas_bp = Blueprint('ventas', __name__)


@ventas_bp.route('/ventas/registrar_venta', methods=['GET'])
@login_required
def vista_registro():
    bancos = Ventas.obtener_bancos()
    metodos_pago = Ventas.obtener_metodos_pago()
    monedas = Ventas.obtener_monedas()
    monedas_digitales = Ventas.obtener_moneda_digital()
    vehiculos = Vehiculo.obtener_vehiculos_disponibles()
    clientes = Ventas.obtener_clientes()
    tasa_actual = Ventas.obtener_tasa_actual()

    return render_template(
        'ventas/registrar_venta.html',
        bancos=bancos,
        metodos_pago=metodos_pago,
        monedas=monedas,
        monedas_digitales=monedas_digitales,
        vehiculos=vehiculos,
        clientes=clientes,
        tasa_actual=tasa_actual
    )


# =========================================================================
# API BUSCAR CLIENTE
# =========================================================================
@ventas_bp.route('/ventas/api/cliente/<string:termino>', methods=['GET'])
@login_required
def api_buscar_cliente(termino):
    cliente = Ventas.buscar_cliente(termino)
    if cliente:
        return jsonify({
            'exito': True,
            'cedula': cliente.get('cedula_usuario'),
            'nombre': cliente.get('nombre'),
            'apellido': cliente.get('apellido'),
            'telefono': cliente.get('telefono'),
            'correo': cliente.get('correo'),
            'direccion': cliente.get('direccion')
        })
    return jsonify({
        'exito': False,
        'mensaje': 'Cliente no encontrado o no coincide con la búsqueda'
    }), 404


# =========================================================================
# API: REGISTRO RÁPIDO DE CLIENTES DESDE EL FORMULARIO DE VENTAS
# =========================================================================
@ventas_bp.route('/ventas/api/cliente/registrar', methods=['POST'])
@login_required
@requiere_permiso('Ventas', 'p_crear')
def api_registrar_cliente_rapido():
    datos = request.get_json(silent=True) or {}

    cedula = str(datos.get('cedula', '')).strip()
    nombre = str(datos.get('nombre', '')).strip()
    apellido = str(datos.get('apellido', '')).strip()
    telefono = str(datos.get('telefono', '')).strip()
    direccion = str(datos.get('direccion', '')).strip()
    correo = str(datos.get('correo', '')).strip()
    password = str(datos.get('password') or 'Admin1234*')

    campos = {
        'Cédula': cedula,
        'nombre': nombre,
        'apellido': apellido,
        'teléfono': telefono,
        'dirección': direccion,
        'correo': correo
    }
    faltantes = [campo for campo, valor in campos.items() if not valor]
    if faltantes:
        return jsonify({
            'exito': False,
            'mensaje': 'Completa los siguientes campos: ' + ', '.join(faltantes) + '.'
        }), 400

    try:
        nuevo_cliente = ClienteModel(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            correo=correo,
            password=password,
            foto='uploads/perfiles/default.png',
            cod_rol=4
        )
        resultado = nuevo_cliente.registrar_cliente_db()

        if not resultado.get('status'):
            return jsonify({
                'exito': False,
                'mensaje': resultado.get('mensaje', 'No se pudo registrar el cliente.')
            }), 400

        try:
            operador = session.get('cedula_usuario')
            if operador:
                Bitacora.registrar(operador, 1, 17)
        except Exception as error_bitacora:
            print(f'Advertencia bitácora cliente rápido: {error_bitacora}')

        return jsonify({
            'exito': True,
            'mensaje': 'Cliente registrado correctamente.',
            'cliente': {
                'cedula': cedula,
                'nombre': nombre,
                'apellido': apellido,
                'telefono': telefono,
                'correo': correo,
                'direccion': direccion
            }
        }), 201

    except Exception as error:
        print(f'Error al registrar cliente desde ventas: {error}')
        return jsonify({
            'exito': False,
            'mensaje': 'Ocurrió un error al registrar el cliente.'
        }), 500


# =========================================================================
# API BUSCAR VEHÍCULO POR PLACA
# =========================================================================
@ventas_bp.route('/ventas/api/vehiculo/<string:placa>', methods=['GET'])
@login_required
def api_buscar_vehiculo(placa):
    respuesta = Ventas.buscar_por_placa(placa)
    if respuesta:
        return jsonify(respuesta)
    return jsonify({
        'exito': False,
        'mensaje': 'Vehículo no encontrado o no disponible para la venta'
    }), 404


# =========================================================================
# REGISTRAR VENTA
# =========================================================================
@ventas_bp.route('/ventas/registrar_venta', methods=['POST'])
@login_required
@requiere_permiso('Ventas', 'p_crear')
def registrar_venta():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"exito": False, "mensaje": "No se recibieron datos"}), 400

    try:
        nueva_venta = Ventas(data)
        cedula_usuario = session.get('cedula_usuario')
        if not cedula_usuario:
            return jsonify({"exito": False, "mensaje": "No se pudo identificar al usuario de la sesión"}), 401

        resultado = nueva_venta.registrar(cedula_usuario)
        if not resultado.get("status"):
            return jsonify({
                "exito": False,
                "mensaje": resultado.get("error", "Error desconocido al registrar la venta")
            }), 400

        cedula_cliente = data.get('cedula_cliente')
        cod_venta = resultado.get("cod_venta")

        try:
            NotificacionManager.crear_multiple(
                notificacion_cliente={
                    "id_cliente": cedula_cliente,
                    "titulo": "Vehículo Adquirido",
                    "mensaje": "Tu compra ha sido registrada con éxito. ¡Felicidades por tu nuevo vehículo!",
                    "url_destino": "/ventas/lista_ventas",
                    "modulo": "ventas"
                } if cedula_cliente else None,
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Nueva Venta Registrada",
                    "mensaje": f"Se ha registrado exitosamente una nueva venta (#{cod_venta}) para el cliente {cedula_cliente}.",
                    "url_destino": "/ventas/lista_ventas",
                    "modulo": "ventas"
                }
            )
        except Exception as e:
            print(f"Advertencia notificaciones venta #{cod_venta}: {e}")

        return jsonify({
            "exito": True,
            "mensaje": "Venta y plan de pagos registrados exitosamente",
            "cod_venta": cod_venta,
            "pdf_url": url_for('ventas.generar_factura_pdf', cod_venta=cod_venta)
        })

    except Exception as e:
        print(f"Error en controlador registrar_venta: {e}")
        return jsonify({"exito": False, "mensaje": "Ocurrió un error inesperado al registrar la venta"}), 500


# =========================================================================
# GENERAR COMPROBANTE PDF
# =========================================================================
@ventas_bp.route('/ventas/factura/<int:cod_venta>')
@login_required
def generar_factura_pdf(cod_venta):
    datos = Ventas.obtener_datos_factura(cod_venta)
    if not datos:
        return jsonify({"exito": False, "mensaje": "La venta solicitada no existe"}), 404

    venta = datos['venta']
    cliente = datos['cliente']
    pagos = datos['pagos']
    cuotas = datos.get('cuotas', [])

    cliente_nombre = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}".strip() or "No disponible"
    cedula_cliente = cliente.get('cedula_usuario', venta.get('cedula_cliente', 'No disponible'))
    telefono = cliente.get('telefono') or 'No registrado'
    direccion = cliente.get('direccion') or 'No registrada'
    correo = cliente.get('correo') or 'No registrado'

    marca = venta.get('marca') or 'N/D'
    modelo = venta.get('modelo') or 'N/D'
    anio = venta.get('anio') or 'N/D'
    color = venta.get('color') or 'N/D'
    placa = venta.get('placa') or 'N/D'
    tipo_vehiculo = venta.get('tipo_vehiculo') or 'N/D'

    precio = float(venta.get('precio') or 0)
    deuda_total = float(venta.get('deuda_total') or 0)
    total_pagado = float(venta.get('total_pagado') or 0)
    saldo_pendiente = float(venta.get('saldo_pendiente') or 0)
    tasa_interes = float(venta.get('tasa_interes') or 0)

    def moneda(valor):
        return f"${valor:,.2f}"

    def texto(valor):
        if valor is None:
            return ""
        valor = str(valor)
        try:
            valor.encode('latin-1')
            return valor
        except UnicodeEncodeError:
            return valor.encode('latin-1', 'replace').decode('latin-1')

    def fecha_formateada(fecha):
        if not fecha:
            return "N/D"
        try:
            return fecha.strftime("%d/%m/%Y")
        except AttributeError:
            return str(fecha)

    def fecha_hora_formateada(fecha):
        if not fecha:
            return "N/D"
        try:
            return fecha.strftime("%d/%m/%Y %H:%M")
        except AttributeError:
            return str(fecha)

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    ruta_logo = 'static/img/automall.jpeg'
    if os.path.exists(ruta_logo):
        pdf.image(ruta_logo, x=15, y=10, w=45)

    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 10, txt=texto("AUTOMALL DEL CENTRO"), ln=True, align='C')
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(190, 8, txt=texto("COMPROBANTE DE VENTA"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # INFORMACIÓN DE LA OPERACIÓN
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("INFORMACIÓN DE LA OPERACIÓN"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, txt=texto(f"Nro. de operación: {cod_venta}"))
    pdf.cell(95, 7, txt=texto(f"Fecha: {fecha_formateada(venta.get('fecha_venta'))}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Tipo de venta: {venta.get('tipo_venta') or 'N/D'}"))
    pdf.cell(95, 7, txt=texto(f"Estado: {venta.get('estado_venta') or 'N/D'}"), ln=True)
    if venta.get('tipo_venta') == 'credito':
        pdf.cell(95, 7, txt=texto(f"Frecuencia: {venta.get('frecuencia_pago') or 'Mensual'}"))
        pdf.cell(95, 7, txt=texto(f"Cuotas: {venta.get('cantidad_cuotas') or 1}"), ln=True)
    pdf.ln(4)

    # CLIENTE
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("DATOS DEL CLIENTE"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, txt=texto(f"Cliente: {cliente_nombre}"))
    pdf.cell(95, 7, txt=texto(f"Cédula: {cedula_cliente}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Teléfono: {telefono}"))
    pdf.cell(95, 7, txt=texto(f"Correo: {correo}"), ln=True)
    pdf.multi_cell(190, 7, txt=texto(f"Dirección: {direccion}"))
    pdf.ln(4)

    # VEHÍCULO
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("DATOS DEL VEHÍCULO"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, txt=texto(f"Marca: {marca}"))
    pdf.cell(95, 7, txt=texto(f"Modelo: {modelo}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Año: {anio}"))
    pdf.cell(95, 7, txt=texto(f"Color: {color}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Placa: {placa}"))
    pdf.cell(95, 7, txt=texto(f"Tipo: {tipo_vehiculo}"), ln=True)
    pdf.ln(4)

    # TRASPASO Y PODER
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("DOCUMENTACIÓN DE LA VENTA"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, txt=texto(f"Poder: {'Sí' if venta.get('poder') else 'No'}"))
    pdf.cell(95, 7, txt=texto(f"Traspaso de papel: {'Sí' if venta.get('traspaso_papel') else 'No'}"), ln=True)
    pdf.ln(4)

    # DOCUMENTOS ENTREGADOS
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt=texto("Documentos del vehículo incluidos:"), ln=True)
    pdf.set_font("Arial", '', 9)

    docs_presentes = []
    if venta.get('original_totalPropiedad'): docs_presentes.append("Título de Propiedad (Original)")
    if venta.get('experticia_transito'): docs_presentes.append("Experticia de Tránsito")
    if venta.get('certificado_origen'): docs_presentes.append("Certificado de Origen")
    if venta.get('carnet_circulacion'): docs_presentes.append("Carnet de Circulación")
    if venta.get('reserva_dominio'): docs_presentes.append("Reserva de Dominio")
    if venta.get('garantia_vehiculo'): docs_presentes.append("Garantía del Vehículo")
    if venta.get('certificado_garantia'): docs_presentes.append("Certificado de Garantía")
    if venta.get('manual_vehiculoGarantia'): docs_presentes.append("Manual del Vehículo")
    if venta.get('finiquito'): docs_presentes.append("Finiquito")
    if venta.get('resguardo'): docs_presentes.append("Resguardo")
    if venta.get('fecha_transferencia'): docs_presentes.append("Planilla de Transferencia")
    if venta.get('seguro'): docs_presentes.append("Póliza de Seguro")
    if venta.get('factura_compra'): docs_presentes.append("Factura de Compra")
    otro_doc = venta.get('otro_documento')
    if otro_doc and str(otro_doc).strip():
        docs_presentes.append(f"Otros: {otro_doc}")

    if docs_presentes:
        for i in range(0, len(docs_presentes), 2):
            doc1 = docs_presentes[i]
            doc2 = docs_presentes[i + 1] if i + 1 < len(docs_presentes) else ""
            pdf.cell(95, 5, txt=texto(f"[-] {doc1}"))
            if doc2:
                pdf.cell(95, 5, txt=texto(f"[-] {doc2}"), ln=True)
            else:
                pdf.ln(5)
    else:
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 5, txt=texto("No se registraron documentos adicionales para este vehículo."), ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # RESUMEN ECONÓMICO
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("RESUMEN DE LA OPERACIÓN"), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, txt=texto("Precio del vehículo:"))
    pdf.cell(95, 7, txt=texto(moneda(precio)), align='R', ln=True)
    if tasa_interes > 0:
        pdf.cell(95, 7, txt=texto("Tasa de interés aplicada:"))
        pdf.cell(95, 7, txt=texto(f"{tasa_interes:.2f}%"), align='R', ln=True)
    pdf.cell(95, 7, txt=texto("Monto total registrado en cuenta:"))
    pdf.cell(95, 7, txt=texto(moneda(deuda_total)), align='R', ln=True)
    pdf.cell(95, 7, txt=texto("Total pagado:"))
    pdf.cell(95, 7, txt=texto(moneda(total_pagado)), align='R', ln=True)
    pdf.cell(95, 7, txt=texto("Saldo pendiente:"))
    pdf.cell(95, 7, txt=texto(moneda(saldo_pendiente)), align='R', ln=True)
    pdf.cell(95, 7, txt=texto("Estado de la cuenta:"))
    pdf.cell(95, 7, txt=texto(venta.get('estado_cuenta') or 'N/D'), align='R', ln=True)
    pdf.ln(4)

    # CRONOGRAMA DE CUOTAS (SI ES CRÉDITO)
    if venta.get('tipo_venta') == 'credito' and cuotas:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, txt=texto("CRONOGRAMA DE CUOTAS"), ln=True)

        pdf.set_font("Arial", 'B', 8)
        pdf.cell(22, 7, txt=texto("Cuota"), border=1, align='C')
        pdf.cell(34, 7, txt=texto("Vencimiento"), border=1, align='C')
        pdf.cell(34, 7, txt=texto("Monto"), border=1, align='C')
        pdf.cell(34, 7, txt=texto("Pagado"), border=1, align='C')
        pdf.cell(34, 7, txt=texto("Saldo"), border=1, align='C')
        pdf.cell(32, 7, txt=texto("Estado"), border=1, align='C', ln=True)

        pdf.set_font("Arial", '', 8)
        for c in cuotas:
            m_cuota = float(c.get('monto_cuota') or 0)
            m_pagado = float(c.get('monto_pagado') or 0)
            m_saldo = max(0.0, m_cuota - m_pagado)
            pdf.cell(22, 6, txt=texto(f"#{c.get('numero_cuota')}"), border=1, align='C')
            pdf.cell(34, 6, txt=texto(fecha_formateada(c.get('fecha_vencimiento'))), border=1, align='C')
            pdf.cell(34, 6, txt=texto(moneda(m_cuota)), border=1, align='R')
            pdf.cell(34, 6, txt=texto(moneda(m_pagado)), border=1, align='R')
            pdf.cell(34, 6, txt=texto(moneda(m_saldo)), border=1, align='R')
            pdf.cell(32, 6, txt=texto(c.get('estado_actual') or c.get('estado') or 'Pendiente'), border=1, align='C', ln=True)
        pdf.ln(4)

    # PAGOS REALIZADOS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=texto("PAGOS REGISTRADOS"), ln=True)

    if pagos:
        MAPA_METODOS = {
            '1': 'Binance',
            '2': 'Efectivo',
            '3': 'Pago Móvil',
            '4': 'Zelle',
            '5': 'Transferencia Bancaria',
            '6': 'Zinli',
        }
        MAPA_MONEDAS = {
            '1': 'USD',
            '2': 'VES',
            '3': 'EUR',
        }

        pdf.set_font("Arial", 'B', 8)
        pdf.cell(22, 7, txt=texto("Pago"), border=1, align='C')
        pdf.cell(30, 7, txt=texto("Fecha"), border=1, align='C')
        pdf.cell(35, 7, txt=texto("Monto"), border=1, align='C')
        pdf.cell(35, 7, txt=texto("Método"), border=1, align='C')
        pdf.cell(30, 7, txt=texto("Moneda"), border=1, align='C')
        pdf.cell(38, 7, txt=texto("Referencia"), border=1, align='C', ln=True)

        pdf.set_font("Arial", '', 8)
        for pago in pagos:
            cod_pago = pago.get('cod_pagos', 'N/D')
            fecha_pago = fecha_hora_formateada(pago.get('fecha_pago'))
            monto_pago = moneda(pago.get('monto_abonado', 0))
            cod_metodo_original = str(pago.get('cod_metodo', ''))
            cod_moneda_original = str(pago.get('cod_moneda', ''))
            metodo = MAPA_METODOS.get(cod_metodo_original, cod_metodo_original or 'N/D')
            moneda_pago = MAPA_MONEDAS.get(cod_moneda_original, cod_moneda_original or 'USD')
            referencia = pago.get('referencia') or 'N/D'

            pdf.cell(22, 7, txt=texto(cod_pago), border=1, align='C')
            pdf.cell(30, 7, txt=texto(fecha_pago), border=1, align='C')
            pdf.cell(35, 7, txt=texto(monto_pago), border=1, align='R')
            pdf.cell(35, 7, txt=texto(metodo), border=1, align='C')
            pdf.cell(30, 7, txt=texto(moneda_pago), border=1, align='C')
            pdf.cell(38, 7, txt=texto(referencia), border=1, align='C', ln=True)
    else:
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(190, 6, txt=texto("No se registraron pagos iniciales en esta operación."), ln=True)

    salida = pdf.output(dest='S')
    pdf_bytes = salida.encode('latin-1') if isinstance(salida, str) else bytes(salida)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="comprobante_venta_{cod_venta}.pdf"'
    response.headers['Content-Length'] = str(len(pdf_bytes))
    return response


# =========================================================================
# LISTAR VENTAS
# =========================================================================
@ventas_bp.route('/ventas/lista_ventas')
@login_required
@requiere_permiso('Ventas', 'p_leer')
def listado_ventas():
    cedula_usuario = session.get('cedula_usuario')
    ventas = Ventas.obtener_todas(cedula_usuario)
    return render_template('ventas/lista_ventas.html', ventas=ventas)


# =========================================================================
# ELIMINADO LÓGICO DE VENTAS
# =========================================================================
@ventas_bp.route('/ventas/eliminar/<int:id>', methods=['POST'])
@login_required
@requiere_permiso('Ventas', 'p_eliminar')
def eliminar_venta(id):
    cedula_usuario = session.get('cedula_usuario')

    if Ventas.eliminar(id, cedula_usuario):
        try:
            NotificacionManager.crear(
                titulo="Venta Anulada",
                mensaje=f"La venta con ID #{id} ha sido anulada y el vehículo ha sido liberado.",
                url_destino="/ventas/lista_ventas",
                tipo_destino="ROL",
                roles=[1, 2, 3],
                modulo="ventas"
            )
        except Exception as e:
            print(f"Error creando notificación de venta anulada: {e}")

        flash("Venta anulada y vehículo liberado con éxito.", "success")
    else:
        flash("Error al anular la venta.", "danger")

    return redirect(url_for('ventas.listado_ventas'))


# =========================================================================
# EDITAR VENTAS
# =========================================================================
@ventas_bp.route('/ventas/editar', methods=['POST'])
@login_required
@requiere_permiso('Ventas', 'p_actualizar')
def editar_venta():
    data = request.form.to_dict()
    cedula_usuario = session.get('cedula_usuario')
    editar = Ventas.actualizar(data, cedula_usuario)

    if editar.get("status"):
        try:
            NotificacionManager.crear(
                titulo="Venta Actualizada",
                mensaje="Se ha modificado la información de un registro de venta.",
                url_destino="/ventas/lista_ventas",
                tipo_destino="ROL",
                roles=[1, 2, 3],
                modulo="ventas"
            )
        except Exception as e:
            print(f"Error creando notificación de venta actualizada: {e}")

        flash("Venta actualizada correctamente.", "success")
    else:
        mensaje_error = editar.get("error", "Error desconocido en base de datos")
        flash(f"Error al actualizar la venta: {mensaje_error}", "danger")

    return redirect(url_for('ventas.listado_ventas'))