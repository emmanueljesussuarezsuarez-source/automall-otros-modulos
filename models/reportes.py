from models.db import ConexionBD
import traceback


class ModeloReportesEstadisticos:
    
    def __init__(self):
        self.db = ConexionBD.obtener_conexion()
    
    def generar_estadisticas(self, modulo, filtros):
        try:
            if modulo == "ventas":
                return self._estadisticas_ventas(filtros)
            elif modulo == "vehiculos":
                return self._estadisticas_vehiculos(filtros)
            elif modulo == "mantenimiento":
                return self._estadisticas_mantenimiento(filtros)
            elif modulo == "servicios":
                return self._estadisticas_servicios(filtros)
            elif modulo == "citas":
                return self._estadisticas_citas(filtros)
            elif modulo == "compras_insumos":
                return self._estadisticas_compras_insumos(filtros)
            elif modulo == "pagos":
                return self._estadisticas_pagos(filtros)
            else:
                return {
                    "kpis": [],
                    "graficos": [],
                    "detalle_tabla": {"columnas": [], "filas": []},
                    "error": f"Módulo '{modulo}' no reconocido"
                }
        except Exception as e:
            error_detallado = traceback.format_exc()
            print("--- ERROR DETALLADO EN REPORTES ---")
            print(error_detallado)
            return {
                "kpis": [],
                "graficos": [],
                "detalle_tabla": {"columnas": [], "filas": []},
                "error": f"Error: {str(e)} | Detalle técnico: {error_detallado}"
            }
    
    def _estadisticas_ventas(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("placa"):
            where.append("dv.placa = %s")
            valores.append(filtros["placa"])
        if filtros.get("fecha_desde"):
            where.append("v.fecha_venta >= %s")
            valores.append(filtros["fecha_desde"])
        if filtros.get("fecha_hasta"):
            where.append("v.fecha_venta <= %s")
            valores.append(filtros["fecha_hasta"])
        if filtros.get("tipo_venta"):
            where.append("v.tipo_venta = %s")
            valores.append(filtros["tipo_venta"])
        if filtros.get("estado"):
            where.append("v.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cedula_usuario"):
            where.append("v.cedula_usuario = %s")
            valores.append(filtros["cedula_usuario"])
        
        if filtros.get("min_precio"):
            where.append("dv.precio >= %s")
            valores.append(filtros["min_precio"])
        if filtros.get("max_precio"):
            where.append("dv.precio <= %s")
            valores.append(filtros["max_precio"])
        
        if filtros.get("con_poder") == "1":
            where.append("dv.poder = 1")
        elif filtros.get("con_poder") == "0":
            where.append("dv.poder = 0")
        
        if filtros.get("con_traspaso") == "1":
            where.append("dv.traspaso_papel = 1")
        elif filtros.get("con_traspaso") == "0":
            where.append("dv.traspaso_papel = 0")
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                IFNULL(COUNT(*), 0) AS total_ventas,
                IFNULL(SUM(dv.precio), 0) AS monto_total,
                IFNULL(SUM(CASE WHEN v.tipo_venta = 'contado' THEN dv.precio ELSE 0 END), 0) AS total_contado,
                IFNULL(SUM(CASE WHEN v.tipo_venta IN ('credito', 'crédito') THEN dv.precio ELSE 0 END), 0) AS total_credito
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_ventas = int(k.get("total_ventas") or 0)
        monto_total = float(k.get("monto_total") or 0)
        total_contado = float(k.get("total_contado") or 0)
        total_credito = float(k.get("total_credito") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(v.fecha_venta, '%Y-%m') AS anio_mes,
                COUNT(*) AS cantidad,
                IFNULL(SUM(dv.precio), 0) AS monto
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT dv.placa, COUNT(*) AS cantidad
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
            GROUP BY dv.placa
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_vehiculos = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT v.tipo_venta, COUNT(*) AS cantidad
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
            GROUP BY v.tipo_venta
        """, valores)
        filas_tipo = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT v.estado, COUNT(*) AS cantidad
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
            GROUP BY v.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN dv.poder = 1 THEN 1 ELSE 0 END) AS con_poder,
                SUM(CASE WHEN dv.poder = 0 THEN 1 ELSE 0 END) AS sin_poder
            FROM ventas v
            INNER JOIN det_venta dv ON v.cod_venta = dv.cod_venta
            WHERE {where_sql}
        """, valores)
        p = cursor.fetchone() or {}
        con_poder = int(p.get("con_poder") or 0)
        sin_poder = int(p.get("sin_poder") or 0)
        
        return {
            "kpis": [
                {"titulo": "Total Ventas", "valor": str(total_ventas), "icono": "bi-cart-check", "color": "primary"},
                {"titulo": "Monto Total", "valor": f"${monto_total:,.2f}", "icono": "bi-cash-stack", "color": "success"},
                {"titulo": "Ventas Contado", "valor": f"${total_contado:,.2f}", "icono": "bi-wallet2", "color": "info"},
                {"titulo": "Ventas Crédito", "valor": f"${total_credito:,.2f}", "icono": "bi-credit-card", "color": "warning"},
            ],
            "graficos": [
                {
                    "id": "ventas-area",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Ventas por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_mes]},
                        {"name": "Monto", "data": [float(f["monto"]) for f in filas_mes]},
                    ],
                },
                {
                    "id": "ventas-barra-vehiculos",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Vehículos Más Vendidos",
                    "labels": [f["placa"] for f in filas_vehiculos],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_vehiculos]},
                    ],
                },
                {
                    "id": "ventas-pie-tipo",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Tipo de Venta",
                    "labels": [(f["tipo_venta"] or "Sin tipo") for f in filas_tipo],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_tipo] or [1]},
                    ],
                },
                {
                    "id": "ventas-doughnut-estado",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Ventas",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "ventas-doughnut-poder",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Ventas con Poder vs Sin Poder",
                    "labels": ["Con Poder", "Sin Poder"],
                    "datasets": [
                        {"data": [max(1, con_poder), max(1, sin_poder)]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Cantidad", "Monto Total"],
                "filas": [[f["anio_mes"], str(f["cantidad"]), f"{float(f['monto']):,.2f}"] for f in filas_mes],
            },
        }
    
    def _estadisticas_vehiculos(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("placa"):
            where.append("v.placa = %s")
            valores.append(filtros["placa"])
        if filtros.get("estado"):
            where.append("v.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cod_tipo"):
            where.append("v.cod_tipo = %s")
            valores.append(filtros["cod_tipo"])
        if filtros.get("cod_modelo"):
            where.append("v.cod_modelo = %s")
            valores.append(filtros["cod_modelo"])
        if filtros.get("anio_desde"):
            where.append("v.anio >= %s")
            valores.append(filtros["anio_desde"])
        if filtros.get("anio_hasta"):
            where.append("v.anio <= %s")
            valores.append(filtros["anio_hasta"])
        if filtros.get("min_kilometraje"):
            where.append("v.kilometraje >= %s")
            valores.append(filtros["min_kilometraje"])
        if filtros.get("max_kilometraje"):
            where.append("v.kilometraje <= %s")
            valores.append(filtros["max_kilometraje"])
        if filtros.get("cedula_propietario"):
            where.append("v.cedula_propietario = %s")
            valores.append(filtros["cedula_propietario"])
        if filtros.get("cod_documento"):
            where.append("v.cod_documento = %s")
            valores.append(filtros["cod_documento"])
        if filtros.get("cod_accesorio"):
            where.append("v.cod_accesorio = %s")
            valores.append(filtros["cod_accesorio"])
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                COUNT(*) AS total_vehiculos,
                SUM(CASE WHEN v.estado = 'disponible' THEN 1 ELSE 0 END) AS disponibles,
                SUM(CASE WHEN v.estado = 'vendido' THEN 1 ELSE 0 END) AS vendidos,
                SUM(CASE WHEN v.estado IN ('mantenimiento', 'servicio') THEN 1 ELSE 0 END) AS en_taller
            FROM vehiculo v
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_vehiculos = int(k.get("total_vehiculos") or 0)
        disponibles = int(k.get("disponibles") or 0)
        vendidos = int(k.get("vendidos") or 0)
        en_taller = int(k.get("en_taller") or 0)
        
        cursor.execute(f"""
            SELECT 
                v.anio AS anio,
                COUNT(*) AS cantidad
            FROM vehiculo v
            WHERE {where_sql}
            GROUP BY anio
            ORDER BY anio
        """, valores)
        filas_anio = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT m.nombre_modelo, COUNT(*) AS cantidad
            FROM vehiculo v
            INNER JOIN modelo m ON v.cod_modelo = m.cod_modelo
            WHERE {where_sql}
            GROUP BY m.nombre_modelo
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_modelos = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT v.estado, COUNT(*) AS cantidad
            FROM vehiculo v
            WHERE {where_sql}
            GROUP BY v.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT tv.nombre_tipo, COUNT(*) AS cantidad
            FROM vehiculo v
            INNER JOIN tipo_vehiculo tv ON v.cod_tipo = tv.cod_tipo
            WHERE {where_sql}
            GROUP BY tv.nombre_tipo
        """, valores)
        filas_tipo = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN v.kilometraje = 0 THEN 1 ELSE 0 END) AS nuevos,
                SUM(CASE WHEN v.kilometraje > 0 THEN 1 ELSE 0 END) AS usados
            FROM vehiculo v
            WHERE {where_sql}
        """, valores)
        n = cursor.fetchone() or {}
        nuevos = int(n.get("nuevos") or 0)
        usados = int(n.get("usados") or 0)
        
        return {
            "kpis": [
                {"titulo": "Total Vehículos", "valor": str(total_vehiculos), "icono": "bi-car-front", "color": "primary"},
                {"titulo": "Disponibles", "valor": str(disponibles), "icono": "bi-check-circle", "color": "success"},
                {"titulo": "Vendidos", "valor": str(vendidos), "icono": "bi-cart-check", "color": "info"},
                {"titulo": "En Taller", "valor": str(en_taller), "icono": "bi-tools", "color": "warning"},
            ],
            "graficos": [
                {
                    "id": "vehiculos-area-anio",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Vehículos por Año",
                    "labels": [str(f["anio"]) for f in filas_anio],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_anio]},
                    ],
                },
                {
                    "id": "vehiculos-barra-modelos",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Modelos con Más Vehículos",
                    "labels": [f["nombre_modelo"] for f in filas_modelos],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_modelos]},
                    ],
                },
                {
                    "id": "vehiculos-pie-estado",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Vehículos",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "vehiculos-doughnut-tipo",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Tipo de Vehículo",
                    "labels": [(f["nombre_tipo"] or "Sin tipo") for f in filas_tipo],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_tipo] or [1]},
                    ],
                },
                {
                    "id": "vehiculos-doughnut-nuevos",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Nuevos vs Usados",
                    "labels": ["Nuevos", "Usados"],
                    "datasets": [
                        {"data": [max(1, nuevos), max(1, usados)]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Año", "Cantidad"],
                "filas": [[str(f["anio"]), str(f["cantidad"])] for f in filas_anio],
            },
        }

    def _estadisticas_mantenimiento(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("placa"):
            where.append("dm.placa = %s")
            valores.append(filtros["placa"])
        if filtros.get("estado"):
            where.append("m.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("tipo"):
            where.append("dm.tipo = %s")
            valores.append(filtros["tipo"])
        if filtros.get("cod_mantenimiento"):
            where.append("m.cod_mantenimiento = %s")
            valores.append(filtros["cod_mantenimiento"])
        if filtros.get("cod_taller"):
            where.append("dm.cod_taller = %s")
            valores.append(filtros["cod_taller"])
        if filtros.get("fecha_solicitud_desde"):
            where.append("dm.fecha_solicitud >= %s")
            valores.append(filtros["fecha_solicitud_desde"])
        if filtros.get("fecha_solicitud_hasta"):
            where.append("dm.fecha_solicitud <= %s")
            valores.append(filtros["fecha_solicitud_hasta"])
        if filtros.get("min_costo_base"):
            where.append("m.costo_base >= %s")
            valores.append(filtros["min_costo_base"])
        if filtros.get("max_costo_base"):
            where.append("m.costo_base <= %s")
            valores.append(filtros["max_costo_base"])
        if filtros.get("min_costo_final"):
            where.append("m.costo_final >= %s")
            valores.append(filtros["min_costo_final"])
        if filtros.get("max_costo_final"):
            where.append("m.costo_final <= %s")
            valores.append(filtros["max_costo_final"])
        
        if filtros.get("con_observaciones") == "1":
            where.append("m.descripcion_general IS NOT NULL AND m.descripcion_general != ''")
        elif filtros.get("con_observaciones") == "0":
            where.append("(m.descripcion_general IS NULL OR m.descripcion_general = '')")
        
        if filtros.get("con_fecha_completada") == "1":
            where.append("dm.fecha_completada IS NOT NULL")
        elif filtros.get("con_fecha_completada") == "0":
            where.append("dm.fecha_completada IS NULL")
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                COUNT(DISTINCT m.cod_mantenimiento) AS total_mantenimientos,
                SUM(CASE WHEN m.estado = 'Activo' THEN 1 ELSE 0 END) AS activos,
                SUM(CASE WHEN m.estado = 'Finalizado' THEN 1 ELSE 0 END) AS finalizados,
                IFNULL(SUM(m.costo_base), 0) AS costo_base_total,
                IFNULL(SUM(m.costo_final), 0) AS costo_final_total
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_mantenimientos = int(k.get("total_mantenimientos") or 0)
        activos = int(k.get("activos") or 0)
        finalizados = int(k.get("finalizados") or 0)
        costo_base_total = float(k.get("costo_base_total") or 0)
        costo_final_total = float(k.get("costo_final_total") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(dm.fecha_solicitud, '%Y-%m') AS anio_mes,
                COUNT(*) AS cantidad
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT t.nombre_taller, COUNT(*) AS cantidad
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            INNER JOIN taller t ON dm.cod_taller = t.cod_taller
            WHERE {where_sql}
            GROUP BY t.nombre_taller
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_talleres = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT dm.tipo, COUNT(*) AS cantidad
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            WHERE {where_sql}
            GROUP BY dm.tipo
        """, valores)
        filas_tipo = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT m.estado, COUNT(*) AS cantidad
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            WHERE {where_sql}
            GROUP BY m.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN dm.tipo = 'Preventivo' THEN 1 ELSE 0 END) AS preventivos,
                SUM(CASE WHEN dm.tipo = 'Correctivo' THEN 1 ELSE 0 END) AS correctivos
            FROM mantenimiento m
            INNER JOIN det_mantenimiento dm ON m.cod_mantenimiento = dm.cod_mantenimiento
            WHERE {where_sql}
        """, valores)
        p = cursor.fetchone() or {}
        preventivos = int(p.get("preventivos") or 0)
        correctivos = int(p.get("correctivos") or 0)
        
        return {
            "kpis": [
                {"titulo": "Total Mantenimientos", "valor": str(total_mantenimientos), "icono": "bi-tools", "color": "primary"},
                {"titulo": "Activos", "valor": str(activos), "icono": "bi-activity", "color": "success"},
                {"titulo": "Finalizados", "valor": str(finalizados), "icono": "bi-check-circle", "color": "info"},
                {"titulo": "Costo Total", "valor": f"${costo_final_total:,.2f}", "icono": "bi-cash-stack", "color": "warning"},
            ],
            "graficos": [
                {
                    "id": "mant-area-mes",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Mantenimientos por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_mes]},
                    ],
                },
                {
                    "id": "mant-barra-talleres",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Talleres con Más Mantenimientos",
                    "labels": [f["nombre_taller"] for f in filas_talleres],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_talleres]},
                    ],
                },
                {
                    "id": "mant-pie-tipo",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Tipo de Mantenimiento",
                    "labels": [(f["tipo"] or "Sin tipo") for f in filas_tipo],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_tipo] or [1]},
                    ],
                },
                {
                    "id": "mant-doughnut-estado",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Mantenimientos",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "mant-doughnut-preventivos",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Preventivos vs Correctivos",
                    "labels": ["Preventivos", "Correctivos"],
                    "datasets": [
                        {"data": [max(1, preventivos), max(1, correctivos)]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Cantidad"],
                "filas": [[f["anio_mes"], str(f["cantidad"])] for f in filas_mes],
            },
        }
    
    def _estadisticas_servicios(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("placa"):
            where.append("ds.placa = %s")
            valores.append(filtros["placa"])
        if filtros.get("estado"):
            where.append("s.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cod_servicios"):
            where.append("s.cod_servicios = %s")
            valores.append(filtros["cod_servicios"])
        if filtros.get("fecha_realizacion_desde"):
            where.append("ds.fecha_realizacion >= %s")
            valores.append(filtros["fecha_realizacion_desde"])
        if filtros.get("fecha_realizacion_hasta"):
            where.append("ds.fecha_realizacion <= %s")
            valores.append(filtros["fecha_realizacion_hasta"])
        if filtros.get("min_costo_base"):
            where.append("s.costo_base >= %s")
            valores.append(filtros["min_costo_base"])
        if filtros.get("max_costo_base"):
            where.append("s.costo_base <= %s")
            valores.append(filtros["max_costo_base"])
        if filtros.get("min_costo_final"):
            where.append("ds.costo_final >= %s")
            valores.append(filtros["min_costo_final"])
        if filtros.get("max_costo_final"):
            where.append("ds.costo_final <= %s")
            valores.append(filtros["max_costo_final"])
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                COUNT(DISTINCT s.cod_servicios) AS total_servicios,
                SUM(CASE WHEN s.estado = 'Activo' THEN 1 ELSE 0 END) AS activos,
                SUM(CASE WHEN s.estado = 'Finalizado' THEN 1 ELSE 0 END) AS finalizados,
                IFNULL(SUM(s.costo_base), 0) AS costo_base_total,
                IFNULL(SUM(ds.costo_final), 0) AS costo_final_total
            FROM servicios s
            LEFT JOIN det_servicios ds ON s.cod_servicios = ds.cod_servicios
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_servicios = int(k.get("total_servicios") or 0)
        activos = int(k.get("activos") or 0)
        finalizados = int(k.get("finalizados") or 0)
        costo_base_total = float(k.get("costo_base_total") or 0)
        costo_final_total = float(k.get("costo_final_total") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(ds.fecha_realizacion, '%Y-%m') AS anio_mes,
                COUNT(*) AS cantidad
            FROM servicios s
            LEFT JOIN det_servicios ds ON s.cod_servicios = ds.cod_servicios
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT s.nombre_servicio, COUNT(ds.cod_det_servicio) AS cantidad
            FROM servicios s
            LEFT JOIN det_servicios ds ON s.cod_servicios = ds.cod_servicios
            WHERE {where_sql}
            GROUP BY s.nombre_servicio
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_servicios = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT s.estado, COUNT(DISTINCT s.cod_servicios) AS cantidad
            FROM servicios s
            LEFT JOIN det_servicios ds ON s.cod_servicios = ds.cod_servicios
            WHERE {where_sql}
            GROUP BY s.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN ds.costo_final IS NOT NULL AND ds.costo_final > 0 THEN 1 ELSE 0 END) AS con_costo,
                SUM(CASE WHEN ds.costo_final IS NULL OR ds.costo_final = 0 THEN 1 ELSE 0 END) AS sin_costo
            FROM servicios s
            LEFT JOIN det_servicios ds ON s.cod_servicios = ds.cod_servicios
            WHERE {where_sql}
        """, valores)
        p = cursor.fetchone() or {}
        con_costo = int(p.get("con_costo") or 0)
        sin_costo = int(p.get("sin_costo") or 0)
        
        return {
            "kpis": [
                {"titulo": "Total Servicios", "valor": str(total_servicios), "icono": "bi-gear-wide-connected", "color": "primary"},
                {"titulo": "Activos", "valor": str(activos), "icono": "bi-activity", "color": "success"},
                {"titulo": "Finalizados", "valor": str(finalizados), "icono": "bi-check-circle", "color": "info"},
                {"titulo": "Costo Total", "valor": f"${costo_final_total:,.2f}", "icono": "bi-cash-stack", "color": "warning"},
            ],
            "graficos": [
                {
                    "id": "servicios-area-mes",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Servicios por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_mes]},
                    ],
                },
                {
                    "id": "servicios-barra-servicios",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Servicios Más Realizados",
                    "labels": [f["nombre_servicio"] for f in filas_servicios],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_servicios]},
                    ],
                },
                {
                    "id": "servicios-pie-estado",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Servicios",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "servicios-doughnut-costo",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Servicios con Costo Final vs Sin Costo",
                    "labels": ["Con Costo", "Sin Costo"],
                    "datasets": [
                        {"data": [max(1, con_costo), max(1, sin_costo)]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Cantidad"],
                "filas": [[f["anio_mes"], str(f["cantidad"])] for f in filas_mes],
            },
        }

    def _estadisticas_citas(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("placa"):
            where.append("v.placa = %s")
            valores.append(filtros["placa"])
        if filtros.get("estado"):
            where.append("c.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cod_catalogo"):
            where.append("c.cod_catalogo = %s")
            valores.append(filtros["cod_catalogo"])
        if filtros.get("cedula_usuario"):
            where.append("c.cedula_usuario = %s")
            valores.append(filtros["cedula_usuario"])
        if filtros.get("fecha_desde"):
            where.append("c.fecha >= %s")
            valores.append(filtros["fecha_desde"])
        if filtros.get("fecha_hasta"):
            where.append("c.fecha <= %s")
            valores.append(filtros["fecha_hasta"])
        if filtros.get("hora_desde"):
            where.append("c.hora >= %s")
            valores.append(filtros["hora_desde"])
        if filtros.get("hora_hasta"):
            where.append("c.hora <= %s")
            valores.append(filtros["hora_hasta"])
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                COUNT(*) AS total_citas,
                SUM(CASE WHEN c.estado = 'Pendiente' THEN 1 ELSE 0 END) AS pendientes,
                SUM(CASE WHEN c.estado = 'Atendida' THEN 1 ELSE 0 END) AS atendidas,
                SUM(CASE WHEN c.estado = 'Cancelada' THEN 1 ELSE 0 END) AS canceladas
            FROM citas c
            LEFT JOIN catalogo cat ON c.cod_catalogo = cat.cod_catalogo
            LEFT JOIN vehiculo v ON cat.placa = v.placa
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_citas = int(k.get("total_citas") or 0)
        pendientes = int(k.get("pendientes") or 0)
        atendidas = int(k.get("atendidas") or 0)
        canceladas = int(k.get("canceladas") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(c.fecha, '%Y-%m') AS anio_mes,
                COUNT(*) AS cantidad
            FROM citas c
            LEFT JOIN catalogo cat ON c.cod_catalogo = cat.cod_catalogo
            LEFT JOIN vehiculo v ON cat.placa = v.placa
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT v.placa, COUNT(*) AS cantidad
            FROM citas c
            INNER JOIN catalogo cat ON c.cod_catalogo = cat.cod_catalogo
            INNER JOIN vehiculo v ON cat.placa = v.placa
            WHERE {where_sql}
            GROUP BY v.placa
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_vehiculos = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT c.estado, COUNT(*) AS cantidad
            FROM citas c
            LEFT JOIN catalogo cat ON c.cod_catalogo = cat.cod_catalogo
            LEFT JOIN vehiculo v ON cat.placa = v.placa
            WHERE {where_sql}
            GROUP BY c.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT c.cedula_usuario, COUNT(*) AS cantidad
            FROM citas c
            LEFT JOIN catalogo cat ON c.cod_catalogo = cat.cod_catalogo
            LEFT JOIN vehiculo v ON cat.placa = v.placa
            WHERE {where_sql}
            GROUP BY c.cedula_usuario
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_usuarios = cursor.fetchall() or []
        
        return {
            "kpis": [
                {"titulo": "Total Citas", "valor": str(total_citas), "icono": "bi-calendar-check", "color": "primary"},
                {"titulo": "Pendientes", "valor": str(pendientes), "icono": "bi-clock", "color": "warning"},
                {"titulo": "Atendidas", "valor": str(atendidas), "icono": "bi-check-circle", "color": "success"},
                {"titulo": "Canceladas", "valor": str(canceladas), "icono": "bi-x-circle", "color": "danger"},
            ],
            "graficos": [
                {
                    "id": "citas-area-mes",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Citas por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_mes]},
                    ],
                },
                {
                    "id": "citas-barra-vehiculos",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Vehículos Más Solicitados",
                    "labels": [f["placa"] for f in filas_vehiculos],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_vehiculos]},
                    ],
                },
                {
                    "id": "citas-pie-estado",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Citas",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "citas-doughnut-usuarios",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Top 5 Usuarios con Más Citas",
                    "labels": [(f["cedula_usuario"] or "Sin usuario") for f in filas_usuarios],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_usuarios] or [1]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Cantidad"],
                "filas": [[f["anio_mes"], str(f["cantidad"])] for f in filas_mes],
            },
        }
    
    def _estadisticas_compras_insumos(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("estado"):
            where.append("ca.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cod_compras"):
            where.append("ca.cod_compras = %s")
            valores.append(filtros["cod_compras"])
        if filtros.get("cod_insumo"):
            where.append("dc.cod_insumo = %s")
            valores.append(filtros["cod_insumo"])
        if filtros.get("rif_cedula_proveedor"):
            where.append("ca.rif_cedula_proveedor = %s")
            valores.append(filtros["rif_cedula_proveedor"])
        if filtros.get("fecha_compra_desde"):
            where.append("ca.fecha_compra >= %s")
            valores.append(filtros["fecha_compra_desde"])
        if filtros.get("fecha_compra_hasta"):
            where.append("ca.fecha_compra <= %s")
            valores.append(filtros["fecha_compra_hasta"])
        if filtros.get("min_cantidad"):
            where.append("dc.cantidad >= %s")
            valores.append(filtros["min_cantidad"])
        if filtros.get("max_cantidad"):
            where.append("dc.cantidad <= %s")
            valores.append(filtros["max_cantidad"])
        if filtros.get("min_precio"):
            where.append("ca.precio >= %s")
            valores.append(filtros["min_precio"])
        if filtros.get("max_precio"):
            where.append("ca.precio <= %s")
            valores.append(filtros["max_precio"])
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                COUNT(DISTINCT ca.cod_compras) AS total_compras,
                IFNULL(SUM(ca.precio), 0) AS monto_total,
                IFNULL(SUM(dc.cantidad), 0) AS cantidad_total,
                SUM(CASE WHEN ca.estado = 'Confirmada' THEN 1 ELSE 0 END) AS confirmadas,
                SUM(CASE WHEN ca.estado = 'Pendiente' THEN 1 ELSE 0 END) AS pendientes
            FROM compras_accesorios ca
            LEFT JOIN det_compra dc ON ca.cod_compras = dc.cod_compras
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_compras = int(k.get("total_compras") or 0)
        monto_total = float(k.get("monto_total") or 0)
        cantidad_total = int(k.get("cantidad_total") or 0)
        confirmadas = int(k.get("confirmadas") or 0)
        pendientes = int(k.get("pendientes") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(ca.fecha_compra, '%Y-%m') AS anio_mes,
                COUNT(DISTINCT ca.cod_compras) AS cantidad,
                IFNULL(SUM(ca.precio), 0) AS monto
            FROM compras_accesorios ca
            LEFT JOIN det_compra dc ON ca.cod_compras = dc.cod_compras
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT i.nombre_insumo, SUM(dc.cantidad) AS cantidad
            FROM compras_accesorios ca
            LEFT JOIN det_compra dc ON ca.cod_compras = dc.cod_compras
            LEFT JOIN insumos i ON dc.cod_insumo = i.cod_insumo
            WHERE {where_sql}
            GROUP BY i.nombre_insumo
            ORDER BY cantidad DESC
            LIMIT 5
        """, valores)
        filas_insumos = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT ca.estado, COUNT(DISTINCT ca.cod_compras) AS cantidad
            FROM compras_accesorios ca
            LEFT JOIN det_compra dc ON ca.cod_compras = dc.cod_compras
            WHERE {where_sql}
            GROUP BY ca.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT ca.tipo_compra, COUNT(DISTINCT ca.cod_compras) AS cantidad
            FROM compras_accesorios ca
            LEFT JOIN det_compra dc ON ca.cod_compras = dc.cod_compras
            WHERE {where_sql}
            GROUP BY ca.tipo_compra
        """, valores)
        filas_tipo = cursor.fetchall() or []
        
        return {
            "kpis": [
                {"titulo": "Total Compras", "valor": str(total_compras), "icono": "bi-cart-plus", "color": "primary"},
                {"titulo": "Monto Total", "valor": f"${monto_total:,.2f}", "icono": "bi-cash-stack", "color": "success"},
                {"titulo": "Cantidad Total", "valor": str(cantidad_total), "icono": "bi-box-seam", "color": "info"},
                {"titulo": "Confirmadas", "valor": str(confirmadas), "icono": "bi-check-circle", "color": "warning"},
            ],
            "graficos": [
                {
                    "id": "compras-area-mes",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Compras por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_mes]},
                        {"name": "Monto", "data": [float(f["monto"]) for f in filas_mes]},
                    ],
                },
                {
                    "id": "compras-barra-insumos",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Insumos Más Comprados",
                    "labels": [f["nombre_insumo"] for f in filas_insumos],
                    "datasets": [
                        {"name": "Cantidad", "data": [int(f["cantidad"]) for f in filas_insumos]},
                    ],
                },
                {
                    "id": "compras-pie-estado",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Compras",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]},
                    ],
                },
                {
                    "id": "compras-doughnut-tipo",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Tipo de Compra",
                    "labels": [(f["tipo_compra"] or "Sin tipo") for f in filas_tipo],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_tipo] or [1]},
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Cantidad", "Monto Total"],
                "filas": [[f["anio_mes"], str(f["cantidad"]), f"{float(f['monto']):,.2f}"] for f in filas_mes],
            },
        }

    def _estadisticas_pagos(self, filtros):
        cursor = self.db.cursor(dictionary=True)
        
        where = []
        valores = []
        
        if filtros.get("estado"):
            where.append("cpc.estado = %s")
            valores.append(filtros["estado"])
        if filtros.get("cod_cuentas"):
            where.append("cpc.cod_cuentas = %s")
            valores.append(filtros["cod_cuentas"])
        if filtros.get("cod_venta"):
            where.append("cpc.cod_venta = %s")
            valores.append(filtros["cod_venta"])
        if filtros.get("fecha_emision_desde"):
            where.append("cpc.fecha_emision >= %s")
            valores.append(filtros["fecha_emision_desde"])
        if filtros.get("fecha_emision_hasta"):
            where.append("cpc.fecha_emision <= %s")
            valores.append(filtros["fecha_emision_hasta"])
        if filtros.get("fecha_vencimiento_desde"):
            where.append("cpc.fecha_vencimiento >= %s")
            valores.append(filtros["fecha_vencimiento_desde"])
        if filtros.get("fecha_vencimiento_hasta"):
            where.append("cpc.fecha_vencimiento <= %s")
            valores.append(filtros["fecha_vencimiento_hasta"])
        if filtros.get("min_deuda_total"):
            where.append("cpc.deuda_total >= %s")
            valores.append(filtros["min_deuda_total"])
        if filtros.get("max_deuda_total"):
            where.append("cpc.deuda_total <= %s")
            valores.append(filtros["max_deuda_total"])
        if filtros.get("min_deuda"):
            where.append("cpc.deuda >= %s")
            valores.append(filtros["min_deuda"])
        if filtros.get("max_deuda"):
            where.append("cpc.deuda <= %s")
            valores.append(filtros["max_deuda"])
        
        where_sql = " AND ".join(where) if where else "1=1"
        
        cursor.execute(f"""
            SELECT 
                IFNULL(SUM(cpc.deuda_total), 0) AS total_deuda,
                IFNULL(SUM(cpc.deuda_total - cpc.deuda), 0) AS total_cobrado,
                IFNULL(SUM(cpc.deuda), 0) AS total_pendiente,
                COUNT(*) AS cuentas
            FROM cuentas_por_cobrar cpc
            WHERE {where_sql}
        """, valores)
        k = cursor.fetchone() or {}
        
        total_deuda = float(k.get("total_deuda") or 0)
        total_cobrado = float(k.get("total_cobrado") or 0)
        total_pendiente = float(k.get("total_pendiente") or 0)
        cuentas = int(k.get("cuentas") or 0)
        
        cursor.execute(f"""
            SELECT 
                DATE_FORMAT(pc.fecha_pago, '%Y-%m') AS anio_mes,
                IFNULL(SUM(pc.monto_abonado), 0) AS monto
            FROM pago_cuentas pc
            JOIN cuentas_por_cobrar cpc ON cpc.cod_cuentas = pc.cod_cuentas
            WHERE {where_sql}
            GROUP BY anio_mes
            ORDER BY anio_mes
        """, valores)
        filas_mes = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT cpc.cod_cuentas, cpc.deuda_total
            FROM cuentas_por_cobrar cpc
            WHERE {where_sql}
            ORDER BY cpc.deuda_total DESC
            LIMIT 5
        """, valores)
        filas_cuentas = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT cpc.estado, COUNT(*) AS cantidad
            FROM cuentas_por_cobrar cpc
            WHERE {where_sql}
            GROUP BY cpc.estado
        """, valores)
        filas_estado = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN cpc.deuda_total < 10000 THEN 'Menos de 10k'
                    WHEN cpc.deuda_total BETWEEN 10000 AND 30000 THEN '10k - 30k'
                    WHEN cpc.deuda_total BETWEEN 30000 AND 60000 THEN '30k - 60k'
                    ELSE 'Más de 60k'
                END AS rango,
                COUNT(*) AS cantidad
            FROM cuentas_por_cobrar cpc
            WHERE {where_sql}
            GROUP BY rango
        """, valores)
        filas_rangos = cursor.fetchall() or []
        
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN cpc.deuda = 0 THEN 1 ELSE 0 END) AS pagadas,
                SUM(CASE WHEN cpc.deuda > 0 THEN 1 ELSE 0 END) AS pendientes
            FROM cuentas_por_cobrar cpc
            WHERE {where_sql}
        """, valores)
        p = cursor.fetchone() or {}
        pagadas = int(p.get("pagadas") or 0)
        pend = int(p.get("pendientes") or 0)
        
        return {
            "kpis": [
                {"titulo": "Total Deuda", "valor": f"${total_deuda:,.2f}", "icono": "bi-piggy-bank", "color": "primary"},
                {"titulo": "Total Cobrado", "valor": f"${total_cobrado:,.2f}", "icono": "bi-wallet2", "color": "success"},
                {"titulo": "Saldo Pendiente", "valor": f"${total_pendiente:,.2f}", "icono": "bi-exclamation-triangle", "color": "warning"},
                {"titulo": "Cuentas", "valor": str(cuentas), "icono": "bi-people", "color": "info"},
            ],
            "graficos": [
                {
                    "id": "pagos-area-mes",
                    "tipo": "area",
                    "colSpan": "col-md-6",
                    "titulo": "Pagos Recibidos por Mes",
                    "labels": [f["anio_mes"] for f in filas_mes],
                    "datasets": [
                        {"name": "Monto Abonado", "data": [float(f["monto"]) for f in filas_mes]}
                    ],
                },
                {
                    "id": "pagos-barra-cuentas",
                    "tipo": "bar",
                    "colSpan": "col-md-6",
                    "titulo": "Top 5 Cuentas con Mayor Deuda",
                    "labels": [str(f["cod_cuentas"]) for f in filas_cuentas],
                    "datasets": [
                        {"name": "Deuda Total", "data": [float(f["deuda_total"]) for f in filas_cuentas]}
                    ],
                },
                {
                    "id": "pagos-pie-estado",
                    "tipo": "pie",
                    "colSpan": "col-md-4",
                    "titulo": "Estado de Cuentas por Cobrar",
                    "labels": [(f["estado"] or "Sin estado") for f in filas_estado],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_estado] or [1]}
                    ],
                },
                {
                    "id": "pagos-doughnut-rango",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Distribución por Rango de Deuda",
                    "labels": [f["rango"] for f in filas_rangos],
                    "datasets": [
                        {"data": [max(1, int(f["cantidad"])) for f in filas_rangos] or [1]}
                    ],
                },
                {
                    "id": "pagos-doughnut-pagadas",
                    "tipo": "doughnut",
                    "colSpan": "col-md-4",
                    "titulo": "Cuentas Pagadas vs Pendientes",
                    "labels": ["Pagadas", "Pendientes"],
                    "datasets": [
                        {"data": [max(1, pagadas), max(1, pend)]}
                    ],
                },
            ],
            "detalle_tabla": {
                "columnas": ["Mes", "Monto Pagado"],
                "filas": [[f["anio_mes"], f"{float(f['monto']):,.2f}"] for f in filas_mes],
            },
        }