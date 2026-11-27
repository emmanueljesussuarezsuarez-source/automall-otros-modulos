# utils/export_reports.py

import io
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class GeneradorReportes:

    @staticmethod
    def generar_pdf(modulo, datos):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=0
        )

        h2_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=12,
            spaceAfter=8
        )

        cell_title_style = ParagraphStyle(
            'CellTitle',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor('#475569')
        )

        cell_val_style = ParagraphStyle(
            'CellVal',
            fontName='Helvetica-Bold',
            fontSize=13,
            textColor=colors.HexColor('#0F172A')
        )

        # Buscar la ruta del logo de forma robusta
        logo_path = os.path.join('static', 'img', 'automall.jpeg')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'img', 'automall.jpeg')

        title_para = Paragraph(f"Reporte de {modulo.replace('_', ' ').title()}", title_style)
        subtitle_para = Paragraph("Sistema de Gestión Automall", subtitle_style)

        # Crear encabezado con Logo y Títulos alineados
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=120, height=45)
                logo.hAlign = 'LEFT'
                header_table = Table([[logo, [title_para, subtitle_para]]], colWidths=[130, doc.width - 130])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (1, 0), (1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(header_table)
            except Exception:
                elements.append(title_para)
                elements.append(subtitle_para)
        else:
            elements.append(title_para)
            elements.append(subtitle_para)

        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=15))

        # KPIs
        elements.append(Paragraph("Indicadores Clave (KPIs)", h2_style))
        kpis = datos.get('kpis', [])
        if kpis:
            kpi_data = []
            row_titles = [Paragraph(kpi.get('titulo', ''), cell_title_style) for kpi in kpis]
            row_values = [Paragraph(str(kpi.get('valor', '')), cell_val_style) for kpi in kpis]
            kpi_data.append(row_titles)
            kpi_data.append(row_values)

            col_width = (doc.width) / len(kpis)
            kpi_table = Table(kpi_data, colWidths=[col_width] * len(kpis))
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
                ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(kpi_table)

        elements.append(Spacer(1, 15))

        # Detalle de Registros / Gráficos
        elements.append(Paragraph("Detalle de Registros", h2_style))
        graficos = datos.get('graficos', [])
        for g in graficos:
            elements.append(Paragraph(
                g.get('titulo', 'Gráfico'),
                ParagraphStyle('GTitle', fontName='Helvetica-Bold', fontSize=10,
                               textColor=colors.HexColor('#334155'),
                               spaceBefore=6, spaceAfter=4)
            ))

            labels = g.get('labels', [])
            datasets = g.get('datasets', [])
            table_data = [["Categoría / Etiqueta", "Cantidad / Valor"]]

            if datasets and 'data' in datasets[0]:
                val_list = datasets[0]['data']
                for idx, lbl in enumerate(labels):
                    val = val_list[idx] if idx < len(val_list) else 0
                    table_data.append([str(lbl), str(val)])

            g_table = Table(table_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
            g_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F8FAFC')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8.5),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))
            elements.append(g_table)
            elements.append(Spacer(1, 10))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_excel(modulo, datos):
        wb = Workbook()
        ws = wb.active
        ws.title = "Estadísticas"
        ws.views.sheetView[0].showGridLines = True

        fill_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        fill_kpi_header = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        font_title = Font(name="Calibri", size=15, bold=True, color="0F172A")
        font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=10, bold=True)
        font_regular = Font(name="Calibri", size=10)

        border_thin = Side(border_style="thin", color="CBD5E1")
        border_all = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        # Título
        ws.cell(row=1, column=1, value=f"REPORTE DE ESTADÍSTICAS: {modulo.upper().replace('_', ' ')}").font = font_title
        ws.row_dimensions[1].height = 25

        # KPIs
        ws.cell(row=3, column=1, value="INDICADORES").font = font_bold
        kpis = datos.get('kpis', [])

        current_row = 4
        if kpis:
            headers_kpi = ["Métrica", "Valor"]
            for col_num, h_text in enumerate(headers_kpi, 1):
                cell = ws.cell(row=current_row, column=col_num, value=h_text)
                cell.font = font_header
                cell.fill = fill_kpi_header
                cell.alignment = align_center

            current_row += 1
            for kpi in kpis:
                c1 = ws.cell(row=current_row, column=1, value=kpi.get('titulo'))
                c2 = ws.cell(row=current_row, column=2, value=kpi.get('valor'))
                c1.font = font_regular
                c2.font = font_bold
                c1.border = border_all
                c2.border = border_all
                c1.alignment = align_left
                c2.alignment = align_right
                current_row += 1

        current_row += 2

        # Gráficos / Tablas
        ws.cell(row=current_row, column=1, value="DESGLOSE DE DATOS").font = font_bold
        current_row += 1

        graficos = datos.get('graficos', [])
        for g in graficos:
            ws.cell(row=current_row, column=1, value=g.get('titulo')).font = font_bold
            current_row += 1

            ws.cell(row=current_row, column=1, value="Etiqueta").font = font_header
            ws.cell(row=current_row, column=1).fill = fill_header
            ws.cell(row=current_row, column=2, value="Valor").font = font_header
            ws.cell(row=current_row, column=2).fill = fill_header

            current_row += 1
            labels = g.get('labels', [])
            datasets = g.get('datasets', [])
            data_list = datasets[0].get('data', []) if datasets else []

            for idx, label in enumerate(labels):
                val = data_list[idx] if idx < len(data_list) else 0
                c1 = ws.cell(row=current_row, column=1, value=str(label))
                c2 = ws.cell(row=current_row, column=2, value=val)

                c1.font = font_regular
                c2.font = font_regular
                c1.border = border_all
                c2.border = border_all
                c1.alignment = align_left
                c2.alignment = align_right

                if idx % 2 == 1:
                    c1.fill = fill_zebra
                    c2.fill = fill_zebra

                current_row += 1

            current_row += 2

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer