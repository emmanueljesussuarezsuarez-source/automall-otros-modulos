import os
from flask import Blueprint, request, redirect, url_for, flash, make_response, session
from models.servicios import Servicios
from models.bitacora import Bitacora
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Inches
from io import BytesIO


reporte_servicios_bp = Blueprint('reporte_servicios', __name__)


@reporte_servicios_bp.route('/servicios/reporte/generar', methods=['GET'])
@requiere_permiso('servicios', 'p_leer')
def generar_reporte_servicios():
    cod_servicio = request.args.get('cod_servicio', '').strip()
    nombre_servicio = request.args.get('nombre_servicio', '').strip()
    estado = request.args.get('estado', '').strip()
    placa = request.args.get('placa', '').strip()
    accion = request.args.get('accion', 'ver').strip()

    datos = Servicios.filtrar_reporte(cod_servicio, nombre_servicio, estado, placa)

    if not datos:
        flash('No se encontraron registros para los filtros seleccionados.', 'warning')
        return redirect(url_for('servicios.listar_servicios'))

    encabezados = ['Código', 'Servicio', 'Estado', 'Costo Base', 'Costo Final', 'Descripción', 'Fecha', 'Placa']
    filas_datos = []

    for s in datos:
        filas_datos.append([
            str(s.get('cod_servicios', '')),
            str(s.get('nombre_servicio', '')),
            str(s.get('estado', '')),
            str(s.get('costo_base', '')),
            str(s.get('costo_final', '')),
            str(s.get('descripcion_especifica', '')),
            str(s.get('fecha_realizacion', '')),
            str(s.get('placa', ''))
        ])

    if accion == 'descargar_excel':
        workbook = Workbook()
        hoja = workbook.active
        hoja.title = 'Reporte de Servicios'
        hoja.append(['Reporte de Servicios'])
        hoja.append([])
        hoja.append(encabezados)

        for fila in filas_datos:
            hoja.append(fila)

        hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(encabezados))
        hoja['A1'].font = Font(bold=True, size=14)
        hoja['A1'].alignment = Alignment(horizontal='center')

        encabezado_fill = PatternFill(fill_type='solid', fgColor='343A40')

        for celda in hoja[3]:
            celda.font = Font(bold=True, color='FFFFFF')
            celda.fill = encabezado_fill
            celda.alignment = Alignment(horizontal='center')

        for numero_columna, columna in enumerate(hoja.iter_cols(), start=1):
            maximo = 0
            letra_columna = get_column_letter(numero_columna)

            for celda in columna:
                if celda.value is not None:
                    maximo = max(maximo, len(str(celda.value)))

            hoja.column_dimensions[letra_columna].width = min(maximo + 2, 35)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_servicios.xlsx'

    elif accion == 'descargar_word':
        documento = Document()
        logo_path = os.path.join('static', 'img', 'automall.jpeg')
        if os.path.exists(logo_path):
            documento.add_picture(logo_path, width=Inches(1.5))

        documento.add_heading('Reporte de Servicios', level=1)

        tabla = documento.add_table(rows=1, cols=len(encabezados))
        tabla.style = 'Table Grid'

        for indice, encabezado in enumerate(encabezados):
            tabla.rows[0].cells[indice].text = encabezado

        for fila in filas_datos:
            celdas = tabla.add_row().cells

            for indice, valor in enumerate(fila):
                celdas[indice].text = valor

        buffer = BytesIO()
        documento.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_servicios.docx'

    else:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=40,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=styles['Title'],
            alignment=TA_CENTER
        ))

        story = []

        # Insertar logo de la compañía centrado
        logo_path = os.path.join('static', 'img', 'automall.jpeg')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=110, height=42)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 10))

        story.append(Paragraph('Reporte de Servicios', styles['CenterTitle']))
        story.append(Spacer(1, 12))

        filas = [encabezados]
        filas.extend(filas_datos)

        tabla = Table(filas, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(tabla)
        doc.build(story)

        pdf = buffer.getvalue()
        buffer.close()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'

        if accion == 'descargar':
            response.headers['Content-Disposition'] = 'attachment; filename=reporte_servicios.pdf'
        else:
            response.headers['Content-Disposition'] = 'inline; filename=reporte_servicios.pdf'

    cedula_usuario = session.get('cedula_usuario')

    if cedula_usuario:
        Bitacora.registrar(
            cedula_usuario,
            cod_accion=5,
            cod_modulo=9
        )

    NotificacionManager.crear_multiple(
        notificacion_staff={
            "roles": [1, 2],
            "titulo": "Reporte de Servicios Generado",
            "mensaje": f"Se ha generado un reporte de servicios.",
            "url_destino": url_for('servicios.listar_servicios'),
            "modulo": "servicios"
        }
    )

    return response