import os
from flask import Blueprint, request, redirect, url_for, flash, make_response, session
from models.mantenimiento_operacional import MantenimientoOperacional
from models.bitacora import Bitacora
from utils.permisos import requiere_permiso
from utils.notificaciones_manager import NotificacionManager
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Inches
from io import BytesIO


reporte_mantenimiento_operacional_bp = Blueprint('reporte_mantenimiento_operacional', __name__)


@reporte_mantenimiento_operacional_bp.route('/mantenimiento-operacional/reporte/generar', methods=['GET'])
@requiere_permiso('mantenimiento_operacional', 'p_leer')
def generar_reporte_mantenimiento():
    cod_mantenimiento = request.args.get('cod_mantenimiento', '').strip()
    placa = request.args.get('placa', '').strip()
    estado = request.args.get('estado', '').strip()
    cod_taller = request.args.get('cod_taller', '').strip()
    fecha_inicio = request.args.get('fecha_inicio', '').strip()
    fecha_fin = request.args.get('fecha_fin', '').strip()

    costo_base_desde = request.args.get('costo_base_desde', '').strip()
    costo_base_hasta = request.args.get('costo_base_hasta', '').strip()
    costo_final_desde = request.args.get('costo_final_desde', '').strip()
    costo_final_hasta = request.args.get('costo_final_hasta', '').strip()

    accion = request.args.get('accion', 'ver').strip()

    datos = MantenimientoOperacional.filtrar_reporte(
        cod_mantenimiento=cod_mantenimiento,
        placa=placa,
        estado=estado,
        cod_taller=cod_taller,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        costo_base_desde=costo_base_desde,
        costo_base_hasta=costo_base_hasta,
        costo_final_desde=costo_final_desde,
        costo_final_hasta=costo_final_hasta
    )

    if not datos:
        flash('No se encontraron registros para los filtros seleccionados.', 'warning')
        return redirect(url_for('mantenimiento_operacional.listar_mantenimiento'))

    encabezados = [
        'Código', 'Descripción', 'Autoriza', 'Estado', 'Tipo',
        'Solicitud', 'Completada', 'Placa', 'Taller',
        'Costo Base', 'Costo Final', 'Usuario'
    ]

    filas_datos = []
    for m in datos:
        costo_base_val = f"${m['costo_base']:,.2f}" if m.get('costo_base') is not None else '-'
        costo_final_val = f"${m['costo_final']:,.2f}" if m.get('costo_final') is not None else '-'

        filas_datos.append([
            str(m.get('cod_mantenimiento', '')),
            str(m.get('descripcion_general', '')),
            str(m.get('quien_autoriza', '')),
            str(m.get('estado', '')),
            str(m.get('tipo', '')),
            str(m.get('fecha_solicitud', '')),
            str(m.get('fecha_completada', '') or '-'),
            str(m.get('placa', '')),
            str(m.get('nombre_taller', '')),
            costo_base_val,
            costo_final_val,
            str(m.get('cedula_usuario', ''))
        ])

    if accion == 'descargar_excel':
        workbook = Workbook()
        hoja = workbook.active
        hoja.title = 'Reporte de Mantenimiento'
        hoja.append(['Reporte de Mantenimiento Operacional'])
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

            hoja.column_dimensions[letra_columna].width = min(max(maximo + 2, 10), 35)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_mantenimiento_operacional.xlsx'

    elif accion == 'descargar_word':
        documento = Document()
        logo_path = os.path.join('static', 'img', 'automall.jpeg')
        if os.path.exists(logo_path):
            documento.add_picture(logo_path, width=Inches(1.5))
        
        documento.add_heading('Reporte de Mantenimiento Operacional', level=1)

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
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_mantenimiento_operacional.docx'

    else:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='CenterTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            fontSize=16,
            leading=20
        )

        cell_style_header = ParagraphStyle(
            'CellHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7,
            leading=9,
            textColor=colors.white,
            alignment=TA_CENTER
        )

        cell_style_body = ParagraphStyle(
            'CellBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            alignment=TA_LEFT
        )

        cell_style_body_center = ParagraphStyle(
            'CellBodyCenter',
            parent=cell_style_body,
            alignment=TA_CENTER
        )

        story = []
        
        # Insertar logo de la compañía de forma elegante
        logo_path = os.path.join('static', 'img', 'automall.jpeg')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=110, height=42)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 10))

        story.append(Paragraph('Reporte de Mantenimiento Operacional', title_style))
        story.append(Spacer(1, 12))

        tabla_data = [[Paragraph(h, cell_style_header) for h in encabezados]]

        for fila in filas_datos:
            fila_paragraph = []
            for idx, val in enumerate(fila):
                st = cell_style_body if idx == 1 else cell_style_body_center
                fila_paragraph.append(Paragraph(val, st))
            tabla_data.append(fila_paragraph)

        col_widths = [40, 180, 60, 55, 55, 60, 60, 55, 80, 55, 55, 50]

        tabla = Table(tabla_data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(tabla)
        doc.build(story)

        pdf = buffer.getvalue()
        buffer.close()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'

        if accion == 'descargar':
            response.headers['Content-Disposition'] = 'attachment; filename=reporte_mantenimiento_operacional.pdf'
        else:
            response.headers['Content-Disposition'] = 'inline; filename=reporte_mantenimiento_operacional.pdf'

    cedula_usuario = session.get('cedula_usuario')

    if cedula_usuario:
        Bitacora.registrar(
            cedula_usuario,
            cod_accion=5,
            cod_modulo=3
        )

    NotificacionManager.crear_multiple(
        notificacion_staff={
            "roles": [1, 2],
            "titulo": "Reporte de Mantenimiento Generado",
            "mensaje": "Se ha generado un reporte de mantenimiento operacional.",
            "url_destino": url_for('mantenimiento_operacional.listar_mantenimiento'),
            "modulo": "mantenimiento_operacional"
        }
    )

    return response