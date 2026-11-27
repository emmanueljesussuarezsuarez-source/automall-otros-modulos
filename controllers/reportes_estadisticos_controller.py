from flask import Blueprint, jsonify, render_template, request, send_file, session, url_for
from models.reportes import ModeloReportesEstadisticos as Reporte
from models.bitacora import Bitacora
from utils.decorators import login_required
from utils.export_reports import GeneradorReportes
from utils.notificaciones_manager import NotificacionManager

estadisticas_bp = Blueprint('estadisticas', __name__)

@estadisticas_bp.route('/reportes/estadisticas')
@login_required
def vista_estadisticas():
    cedula_usuario = session.get('cedula_usuario')
    
    if cedula_usuario:
        Bitacora.registrar(
            cedula_usuario,
            cod_accion=2,
            cod_modulo=5
        )
    
    return render_template('reportes_estadisticos/estadisticas.html')

@estadisticas_bp.route('/api/reportes/<string:modulo>')
@login_required
def api_data_reportes(modulo):
    cedula_usuario = session.get('cedula_usuario')
    
    modulos_validos = ['ventas', 'vehiculos', 'mantenimiento', 'servicios', 'citas', 'compras_insumos', 'pagos']
    if modulo not in modulos_validos:
        return jsonify({
            "status": False,
            "code": 400,
            "error": f"Módulo '{modulo}' no válido. Módulos válidos: {', '.join(modulos_validos)}"
        }), 400
    
    params = request.args.to_dict()
    
    resultado = Reporte().generar_estadisticas(modulo, params)
    
    if "error" in resultado:
        return jsonify({
            "status": False,
            "code": 400,
            "error": resultado.get("error")
        }), 400
    
    if cedula_usuario:
        Bitacora.registrar(
            cedula_usuario,
            cod_accion=12,
            cod_modulo=5
        )
    
    return jsonify(resultado)

@estadisticas_bp.route('/api/reportes/<string:modulo>/exportar')
@login_required
def exportar_reporte(modulo):
    cedula_usuario = session.get('cedula_usuario')
    
    formato = request.args.get('formato', 'pdf').lower()
    if formato not in ['pdf', 'excel']:
        return jsonify({"error": "Formato no soportado. Use 'pdf' o 'excel'"}), 400
    
    params = request.args.to_dict()
    params.pop('formato', None)
    
    modulos_validos = ['ventas', 'vehiculos', 'mantenimiento', 'servicios', 'citas', 'compras_insumos', 'pagos']
    if modulo not in modulos_validos:
        return jsonify({
            "status": False,
            "code": 400,
            "error": f"Módulo '{modulo}' no válido. Módulos válidos: {', '.join(modulos_validos)}"
        }), 400
    
    datos = Reporte().generar_estadisticas(modulo, params)
    
    if "error" in datos:
        return jsonify({
            "status": False,
            "code": 400,
            "error": datos.get("error")
        }), 400
    
    if cedula_usuario:
        Bitacora.registrar(
            cedula_usuario,
            cod_accion=5,
            cod_modulo=5
        )
    
    if formato == 'pdf':
        buffer = GeneradorReportes.generar_pdf(modulo, datos)
        mimetype = 'application/pdf'
        ext = 'pdf'
    else:
        buffer = GeneradorReportes.generar_excel(modulo, datos)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    
    NotificacionManager.crear_multiple(
        notificacion_staff={
            "roles": [1, 2],
            "titulo": "Reporte Estadístico exportado",
            "mensaje": f"Se ha exportado el reporte estadístico del módulo '{modulo}' en formato {formato.upper()}.",
            "url_destino": url_for('estadisticas.vista_estadisticas'),
            "modulo": "estadisticas"
        }
    )
    
    nombre_archivo = f"reporte_{modulo}.{ext}"
    
    return send_file(
        buffer,
        mimetype=mimetype,
        as_attachment=True,
        download_name=nombre_archivo
    )