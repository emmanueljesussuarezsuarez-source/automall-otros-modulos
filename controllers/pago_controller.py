from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from fpdf import FPDF
from models.pagos import Pagos
from models.ventas import Ventas
from models.tasa import Tasa
from models.user import Usuario
from utils.decorators import login_required
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager

pagos_bp = Blueprint("pagos", __name__)


# ==========================================================
# LISTAR PAGOS Y CUOTAS (CLIENTE)
# ==========================================================
@pagos_bp.route("/pagos/listar_pagos")
@login_required
@requiere_permiso("Pagos", "p_leer")
def listar_pagos():
    cedula_usuario = session.get("cedula_usuario")
    pagos = Pagos.obtener_todos(cedula_usuario)
    cuotas = Pagos.obtener_cuotas_cliente(cedula_usuario)

    return render_template(
        "pagos/lista_pagos.html",
        pagos=pagos,
        cuotas=cuotas
    )


# ==========================================================
# LISTAR ADMIN (PAGOS + CONTROL DE CUOTAS)
# ==========================================================
@pagos_bp.route("/pagos/listar_admin")
@login_required
@requiere_permiso("Pagosadmin", "p_leer")
def listar_pagos_admin():
    pagos = Pagos.obtener_todos_admin()
    cuotas = Pagos.obtener_todas_cuotas_admin()

    return render_template(
        "pagos/lista_admin.html",
        pagos=pagos,
        cuotas=cuotas
    )


@pagos_bp.route("/pagos/obtener_deudas/<cedula>")
@login_required
@requiere_permiso("Pagos", "p_crear")
def api_obtener_deudas(cedula):
    try:
        deudas = Pagos.obtener_deudas_pendientes(cedula)
        return jsonify(deudas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pagos_bp.route("/pagos/api/cuotas/<int:cod_cuentas>")
@login_required
def api_obtener_cuotas_cuenta(cod_cuentas):
    try:
        datos = Pagos.obtener_cuotas_por_cuenta(cod_cuentas)
        if not datos:
            return jsonify({"exito": False, "cuotas": []}), 404
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500


# ==========================================================
# REGISTRAR PAGO
# ==========================================================
@pagos_bp.route("/pagos/registrar_pago")
@login_required
def registrar_pago():
    cedula = session.get("cedula_usuario")
    rol = session.get("cod_rol") or session.get("rol")
    es_admin = (rol in [1, 2])

    clientes = []
    deudas = []
    if es_admin:
        clientes = Pagos.obtener_todos_clientes()
    else:
        deudas = Pagos.obtener_deudas_pendientes(cedula)

    metodos = Ventas.obtener_metodos_pago()
    monedas = Ventas.obtener_monedas()
    monedas_digitales = Ventas.obtener_moneda_digital()
    bancos = Ventas.obtener_bancos()

    tasa_db = Tasa.get_tasa()
    tasa_actual = tasa_db.get("valor") if tasa_db else 0

    return render_template(
        "pagos/registrar.html",
        deudas=deudas,
        clientes=clientes,
        es_admin=es_admin,
        metodos=metodos,
        monedas=monedas,
        monedas_digitales=monedas_digitales,
        bancos=bancos,
        tasa_actual=tasa_actual
    )


# ==========================================================
# PROCESAR PAGO
# ==========================================================
@pagos_bp.route('/pagos/procesar', methods=['POST'])
@login_required
@requiere_permiso('Pagos', 'p_crear')
def procesar_pago():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos."}), 400

        pago_objeto = Pagos(data)
        cedula_logueada = session.get('cedula_usuario')
        if not cedula_logueada:
            return jsonify({"success": False, "error": "No se encontró usuario en sesión."}), 401

        resultado = pago_objeto.procesar_abono(cedula_logueada)
        if not resultado:
            return jsonify({"success": False, "error": "Sin respuesta del modelo."}), 500

        if resultado.get("status"):
            cedula_cliente = resultado.get("cedula_cliente") or data.get("cedula_cliente") or cedula_logueada
            try:
                NotificacionManager.crear_multiple(
                    notificacion_cliente={
                        "id_cliente": cedula_cliente,
                        "titulo": "Pago Procesado",
                        "mensaje": "Tu pago o abono ha sido procesado con éxito.",
                        "url_destino": "/pagos/listar_pagos",
                        "modulo": "pagos"
                    },
                    notificacion_staff={
                        "roles": [1, 2],
                        "titulo": "Nuevo Pago Registrado",
                        "mensaje": f"Se ha registrado un pago para el cliente {cedula_cliente}.",
                        "url_destino": "/pagos/listar_admin",
                        "modulo": "pagos"
                    }
                )
            except Exception as error_notificacion:
                print("Error notificación:", error_notificacion)

            return jsonify({
                "success": True,
                "status": True,
                "message": resultado.get("message", "El pago fue registrado correctamente."),
                "cod_pagos": resultado.get("cod_pagos"),
                "saldo_restante": resultado.get("saldo_restante")
            }), 200

        return jsonify({
            "success": False,
            "status": False,
            "error": resultado.get("error", "No se pudo registrar el pago.")
        }), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500


# ==========================================================
# GENERAR COMPROBANTE PDF DE PAGO
# ==========================================================
@pagos_bp.route("/pagos/factura/<int:cod_pagos>")
@login_required
def generar_factura_pdf(cod_pagos):
    datos = Pagos.obtener_datos_factura(cod_pagos)
    if not datos:
        return jsonify({"exito": False, "mensaje": "El pago solicitado no existe."}), 404

    pago = datos["pago"]
    cliente = datos["cliente"]
    cuotas_aplicadas = datos.get("cuotas_aplicadas", [])

    cliente_nombre = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}".strip() or "No disponible"
    cedula_cliente = cliente.get("cedula_usuario") or pago.get("cedula_cliente") or "No disponible"
    telefono = cliente.get("telefono") or "No registrado"
    direccion = cliente.get("direccion") or "No registrada"
    correo = cliente.get("correo") or "No registrado"

    marca = pago.get("marca") or "N/D"
    modelo = pago.get("modelo") or "N/D"
    anio = pago.get("anio") or "N/D"
    color = pago.get("color") or "N/D"
    placa = pago.get("placa") or "N/D"
    tipo_vehiculo = pago.get("tipo_vehiculo") or "N/D"

    monto_pago = float(pago.get("monto_abonado") or 0)
    monto_recibido = float(pago.get("monto_recibido") or monto_pago)
    deuda_total = float(pago.get("deuda_total") or 0)
    saldo_antes = float(pago.get("saldo_antes") or 0)
    saldo_pendiente = float(pago.get("saldo_pendiente") or 0)
    total_pagado = float(pago.get("total_pagado") or 0)

    def moneda(valor):
        return f"${float(valor or 0):,.2f}"

    def texto(valor):
        if valor is None:
            return ""
        valor = str(valor)
        try:
            valor.encode("latin-1")
            return valor
        except UnicodeEncodeError:
            return valor.encode("latin-1", "replace").decode("latin-1")

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

    metodo = pago.get("metodo_pago") or "N/D"
    moneda_pago = pago.get("moneda") or "N/D"
    simbolo_moneda = pago.get("simbolo_moneda") or ""
    banco = pago.get("nombre_banco") or "N/A"
    referencia = pago.get("referencia") or "N/D"
    descripcion = pago.get("descripcion") or "Abono de cuenta"
    estado_pago = pago.get("estado_pago") or "N/D"

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(190, 10, txt=texto("AUTOMALL DEL CENTRO"), ln=True, align="C")
    pdf.set_font("Arial", "B", 13)
    pdf.cell(190, 8, txt=texto("COMPROBANTE DE PAGO / ABONO"), ln=True, align="C")
    pdf.ln(6)

    # INFORMACIÓN DEL PAGO
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, txt=texto("INFORMACIÓN DEL PAGO"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, txt=texto(f"Nro. de pago: {cod_pagos}"))
    pdf.cell(95, 7, txt=texto(f"Fecha: {fecha_hora_formateada(pago.get('fecha_pago'))}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Nro. de cuenta: {pago.get('cod_cuentas') or 'N/D'}"))
    pdf.cell(95, 7, txt=texto(f"Nro. de venta: {pago.get('cod_venta') or 'N/D'}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Tipo de pago: {pago.get('tipo_pago') or 'Abono'}"))
    pdf.cell(95, 7, txt=texto(f"Estado: {estado_pago}"), ln=True)
    pdf.ln(4)

    # DATOS DEL CLIENTE
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, txt=texto("DATOS DEL CLIENTE"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, txt=texto(f"Cliente: {cliente_nombre}"))
    pdf.cell(95, 7, txt=texto(f"Cédula: {cedula_cliente}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Teléfono: {telefono}"))
    pdf.cell(95, 7, txt=texto(f"Correo: {correo}"), ln=True)
    pdf.multi_cell(190, 7, txt=texto(f"Dirección: {direccion}"))
    pdf.ln(4)

    # DATOS DEL VEHÍCULO
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, txt=texto("DATOS DEL VEHÍCULO"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, txt=texto(f"Marca: {marca}"))
    pdf.cell(95, 7, txt=texto(f"Modelo: {modelo}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Año: {anio}"))
    pdf.cell(95, 7, txt=texto(f"Color: {color}"), ln=True)
    pdf.cell(95, 7, txt=texto(f"Placa: {placa}"))
    pdf.cell(95, 7, txt=texto(f"Tipo: {tipo_vehiculo}"), ln=True)
    pdf.ln(4)

    # DETALLES DE LA TRANSACCIÓN
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, txt=texto("DETALLES DE LA TRANSACCIÓN"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, txt=texto("Método de pago:"))
    pdf.cell(95, 7, txt=texto(metodo), ln=True)
    pdf.cell(95, 7, txt=texto("Moneda:"))
    pdf.cell(95, 7, txt=texto(f"{moneda_pago} {simbolo_moneda}"), ln=True)
    pdf.cell(95, 7, txt=texto("Banco:"))
    pdf.cell(95, 7, txt=texto(banco), ln=True)
    pdf.cell(95, 7, txt=texto("Referencia / TXID:"))
    pdf.cell(95, 7, txt=texto(referencia), ln=True)
    pdf.multi_cell(190, 7, txt=texto(f"Descripción: {descripcion}"))
    pdf.ln(4)

    # CUOTAS CUBIERTAS POR ESTE PAGO
    if cuotas_aplicadas:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(190, 8, txt=texto("CUOTAS APLICADAS EN ESTE PAGO"), ln=True)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(35, 7, txt=texto("Cuota"), border=1, align="C")
        pdf.cell(40, 7, txt=texto("Vencimiento"), border=1, align="C")
        pdf.cell(40, 7, txt=texto("Monto Cuota"), border=1, align="C")
        pdf.cell(40, 7, txt=texto("Monto Aplicado"), border=1, align="C")
        pdf.cell(35, 7, txt=texto("Estado Cuota"), border=1, align="C", ln=True)

        pdf.set_font("Arial", "", 8)
        for ca in cuotas_aplicadas:
            pdf.cell(35, 6, txt=texto(f"Cuota #{ca.get('numero_cuota')}"), border=1, align="C")
            pdf.cell(40, 6, txt=texto(fecha_formateada(ca.get("fecha_vencimiento"))), border=1, align="C")
            pdf.cell(40, 6, txt=texto(moneda(ca.get("monto_cuota"))), border=1, align="R")
            pdf.cell(40, 6, txt=texto(moneda(ca.get("monto_aplicado"))), border=1, align="R")
            pdf.cell(35, 6, txt=texto(ca.get("estado") or "N/D"), border=1, align="C", ln=True)
        pdf.ln(4)

    # RESUMEN ECONÓMICO
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, txt=texto("RESUMEN ECONÓMICO"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 7, txt=texto("Deuda total:"))
    pdf.cell(95, 7, txt=texto(moneda(deuda_total)), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Saldo antes del pago:"))
    pdf.cell(95, 7, txt=texto(moneda(saldo_antes)), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Monto recibido:"))
    pdf.cell(95, 7, txt=texto(f"{monto_recibido:,.2f} {simbolo_moneda}"), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Monto aplicado a la deuda:"))
    pdf.cell(95, 7, txt=texto(moneda(monto_pago)), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Saldo posterior:"))
    pdf.cell(95, 7, txt=texto(moneda(saldo_pendiente)), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Total pagado de la cuenta:"))
    pdf.cell(95, 7, txt=texto(moneda(total_pagado)), align="R", ln=True)
    pdf.cell(95, 7, txt=texto("Estado de la cuenta:"))
    pdf.cell(95, 7, txt=texto(pago.get("estado_cuenta") or "N/D"), align="R", ln=True)
    pdf.ln(6)

    if estado_pago.lower() == "anulado":
        pdf.set_font("Arial", "B", 11)
        pdf.cell(190, 8, txt=texto("PAGO ANULADO"), ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(190, 7, txt=texto(f"Motivo de anulación: {descripcion}"))
        pdf.ln(4)

    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(190, 5, txt=texto("Automall del Centro."), align="C")
    pdf.set_text_color(0, 0, 0)

    salida = pdf.output(dest="S")
    pdf_bytes = salida.encode("latin-1") if isinstance(salida, str) else bytes(salida)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="comprobante_pago_{cod_pagos}.pdf"'
    response.headers["Content-Length"] = str(len(pdf_bytes))
    return response


# ==========================================================
# ANULAR PAGO
# ==========================================================
@pagos_bp.route("/pagos/anular", methods=["POST"])
@login_required
@requiere_permiso("Pagos", "p_eliminar")
def anular_pago():
    cod_pagos = request.form.get("cod_pagos")
    motivo = (request.form.get("motivo") or "Sin motivo especificado").strip()
    cedula_usuario = session.get("cedula_usuario")

    if not cod_pagos:
        flash("No se especificó el pago que desea anular.", "danger")
        return redirect(request.referrer or url_for("pagos.listar_pagos"))

    resultado = Pagos.anular(cod_pagos, cedula_usuario, motivo)

    if resultado:
        cedula_cliente = resultado.get("cedula_cliente") if isinstance(resultado, dict) else cedula_usuario
        try:
            NotificacionManager.crear_multiple(
                notificacion_cliente={
                    "id_cliente": cedula_cliente,
                    "titulo": "Pago Anulado",
                    "mensaje": f"Se ha anulado un pago. Motivo: {motivo[:50]}",
                    "url_destino": "/pagos/listar_pagos",
                    "modulo": "pagos"
                },
                notificacion_staff={
                    "roles": [1, 2],
                    "titulo": "Pago Anulado",
                    "mensaje": f"El usuario {cedula_usuario} anuló el pago #{cod_pagos}. Motivo: {motivo}",
                    "url_destino": "/pagos/listar_admin",
                    "modulo": "pagos"
                }
            )
        except Exception as e:
            print(f"Advertencia: error en notificación: {e}")

        flash("Pago anulado correctamente. El monto fue restaurado a la deuda pendiente y sus cuotas.", "success")
    else:
        flash("No se pudo procesar la anulación. El pago puede no existir o ya estar anulado.", "danger")

    return redirect(request.referrer or url_for("pagos.listar_pagos"))