import csv
import html
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
REPORTES_DIR = os.path.join(BASE_DIR, "reportes")
HOST = "http://127.0.0.1:5000"

# Duración de cada corrida de 1, 20 y 50 usuarios (total completo ~18-19 minutos).
DURACION_NIVEL = "50s"

CASOS_FIJOS = [
    ("CP-TAL-PERF-01", "Cargar formulario taller", "CP01CargarFormularioTaller"),
    ("CP-TAL-PERF-02", "Listar talleres", "CP02ListarTalleres"),
    ("CP-TAL-PERF-03", "Crear taller (POST)", "CP03CrearTaller"),
    ("CP-TAL-PERF-04", "Editar taller (POST)", "CP04EditarTaller"),
    ("CP-TAL-PERF-05", "Eliminar taller (POST)", "CP05EliminarTaller"),
    ("CP-TAL-PERF-06", "Flujo mixto Taller", "CP06FlujoMixtoTaller"),
]

ESPECIALES = [
    ("CP-TAL-PERF-07", "Pico repentino (10->50 en 10s)", os.path.join(BASE_DIR, "cp07_pico_taller.py"), "10->50u"),
    ("CP-TAL-PERF-08", "Estres progresivo (5->100 en 2m)", os.path.join(BASE_DIR, "cp08_estres_taller.py"), "5->100u"),
]

NIVELES = [
    (1, 1),
    (20, 5),
    (50, 10),
]


def verificar_bd_prueba():
    sys.path.insert(0, ROOT_DIR)
    from config import Config

    db_neg = Config.DB_NEGOCIO.get("database")
    db_seg = Config.DB_SEGURIDAD.get("database")
    if db_neg != "automall_test" or db_seg != "seguridad_test":
        print(
            f"[BLOQUEADO] config.py apunta a ({db_neg}, {db_seg}). "
            "Debe apuntar a 'automall_test' y 'seguridad_test'."
        )
        sys.exit(1)
    print(f"[OK] Base de datos verificada: {db_neg} / {db_seg}")


def verificar_servidor_activo():
    try:
        with urllib.request.urlopen(f"{HOST}/login", timeout=5) as resp:
            if resp.status == 200:
                print(f"[OK] Servidor AutoMall activo en {HOST}")
                return
    except urllib.error.URLError:
        pass
    print(f"[ERROR] No responde AutoMall en {HOST}.")
    print("Abre otra terminal y ejecuta primero: python app.py")
    sys.exit(1)


def _valor_columna(fila, *nombres):
    for nombre in nombres:
        if nombre in fila and fila[nombre] != "":
            return fila[nombre]
    return "0"


def _fmt_num(valor, decimales=2):
    try:
        num = float(valor)
        return f"{num:,.{decimales}f}" if decimales > 0 else f"{int(round(num)):,}"
    except (TypeError, ValueError):
        return str(valor)


def leer_resumen_csv(csv_stats_path):
    if not os.path.exists(csv_stats_path):
        return None
    with open(csv_stats_path, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        return None

    objetivo = next((r for r in filas if r.get("Name") == "Aggregated"), filas[-1])
    total = int(float(_valor_columna(objetivo, "Request Count", "Requests")))
    fallos = int(float(_valor_columna(objetivo, "Failure Count", "Failures")))
    pct_fallos = (fallos / total * 100.0) if total > 0 else 0.0

    return {
        "requests": total,
        "fallos": fallos,
        "pct_fallos": f"{pct_fallos:.2f}%",
        "mediana_ms": _valor_columna(objetivo, "Median Response Time", "50%"),
        "p95_ms": _valor_columna(objetivo, "95%"),
        "max_ms": _valor_columna(objetivo, "Max Response Time", "Max"),
        "rps": _valor_columna(objetivo, "Requests/s", "RPS"),
    }


def recolectar_resumenes():
    resumenes = []
    for codigo, descripcion, _ in CASOS_FIJOS:
        for usuarios, _ in NIVELES:
            prefijo = f"{codigo.lower()}_{usuarios}u"
            datos = leer_resumen_csv(os.path.join(REPORTES_DIR, f"{prefijo}_stats.csv"))
            if datos:
                resumenes.append({
                    "caso": codigo,
                    "escenario": descripcion,
                    "carga": f"{usuarios}u",
                    "archivo_html": f"{prefijo}.html",
                    **datos,
                })

    for codigo, descripcion, _, carga in ESPECIALES:
        prefijo = codigo.lower()
        datos = leer_resumen_csv(os.path.join(REPORTES_DIR, f"{prefijo}_stats.csv"))
        if datos:
            resumenes.append({
                "caso": codigo,
                "escenario": descripcion,
                "carga": carga,
                "archivo_html": f"{prefijo}.html",
                **datos,
            })

    return resumenes


def generar_resumen_html(resumenes, ruta_html):
    total_req = sum(int(r["requests"]) for r in resumenes)
    total_fallos = sum(int(r["fallos"]) for r in resumenes)
    pct_global = (total_fallos / total_req * 100.0) if total_req > 0 else 0.0
    max_p95 = max((float(r["p95_ms"]) for r in resumenes), default=0.0)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filas_html = []
    for r in resumenes:
        badge_clase = "ok" if int(r["fallos"]) == 0 else "err"
        enlace_html = r.get("archivo_html", "")
        celda_detalle = (
            f'<a href="{html.escape(enlace_html)}" target="_blank">Ver reporte</a>'
            if enlace_html and os.path.exists(os.path.join(REPORTES_DIR, enlace_html))
            else "-"
        )
        filas_html.append(
            "<tr>"
            f"<td><strong>{html.escape(r['caso'])}</strong></td>"
            f"<td>{html.escape(r['escenario'])}</td>"
            f"<td><span class='badge carga'>{html.escape(r['carga'])}</span></td>"
            f"<td class='num'>{int(r['requests']):,}</td>"
            f"<td><span class='badge {badge_clase}'>{html.escape(r['pct_fallos'])}</span></td>"
            f"<td class='num'>{_fmt_num(r['mediana_ms'], 0)} ms</td>"
            f"<td class='num'>{_fmt_num(r['p95_ms'], 0)} ms</td>"
            f"<td class='num'>{_fmt_num(r['max_ms'], 2)} ms</td>"
            f"<td class='num'>{_fmt_num(r['rps'], 2)}</td>"
            f"<td>{celda_detalle}</td>"
            "</tr>"
        )

    plantilla = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resumen Final - Pruebas de Rendimiento Taller</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #1f2937; margin: 0; padding: 28px; }
  .wrap { max-width: 1200px; margin: 0 auto; }
  .header { background: #111827; color: #fff; padding: 24px 28px; border-radius: 12px; margin-bottom: 20px; }
  .header h1 { margin: 0 0 6px 0; font-size: 22px; }
  .header p { margin: 0; color: #9ca3af; font-size: 14px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .card { background: #fff; padding: 16px 20px; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .card .lbl { font-size: 12px; text-transform: uppercase; color: #6b7280; margin-bottom: 6px; }
  .card .val { font-size: 24px; font-weight: 700; color: #111827; }
  .panel { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { background: #1f2937; color: #fff; text-align: left; padding: 12px 14px; font-weight: 600; }
  td { padding: 11px 14px; border-bottom: 1px solid #e5e7eb; }
  tr:hover td { background: #f9fafb; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .badge.ok { background: #dcfce7; color: #166534; }
  .badge.err { background: #fee2e2; color: #991b1b; }
  .badge.carga { background: #e0e7ff; color: #1e40af; }
  a { color: #2563eb; text-decoration: none; font-weight: 600; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Resumen Final — Pruebas de Rendimiento (Módulo Taller)</h1>
    <p>AutoMall &bull; Base de pruebas: automall_test / seguridad_test &bull; Generado: __FECHA__</p>
  </div>
  <div class="cards">
    <div class="card"><div class="lbl">Corridas ejecutadas</div><div class="val">__CORRIDAS__</div></div>
    <div class="card"><div class="lbl">Peticiones totales</div><div class="val">__TOTAL_REQ__</div></div>
    <div class="card"><div class="lbl">Tasa global de fallos</div><div class="val">__PCT_GLOBAL__</div></div>
    <div class="card"><div class="lbl">Mayor P95 observado</div><div class="val">__MAX_P95__ ms</div></div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>Caso</th>
          <th>Escenario</th>
          <th>Carga</th>
          <th style="text-align:right">Peticiones</th>
          <th>Fallos</th>
          <th style="text-align:right">Mediana</th>
          <th style="text-align:right">Percentil 95</th>
          <th style="text-align:right">Máximo</th>
          <th style="text-align:right">RPS</th>
          <th>Detalle</th>
        </tr>
      </thead>
      <tbody>
        __FILAS__
      </tbody>
    </table>
  </div>
</div>
</body>
</html>
"""
    contenido = (
        plantilla
        .replace("__FECHA__", fecha)
        .replace("__CORRIDAS__", str(len(resumenes)))
        .replace("__TOTAL_REQ__", f"{total_req:,}")
        .replace("__PCT_GLOBAL__", f"{pct_global:.2f}%")
        .replace("__MAX_P95__", _fmt_num(max_p95, 0))
        .replace("__FILAS__", "\n        ".join(filas_html))
    )

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(contenido)


def ejecutar_comando(cmd, etiqueta):
    print(f"\n{'=' * 70}")
    print(f"EJECUTANDO: {etiqueta}")
    print(f"{'=' * 70}")
    resultado = subprocess.run(cmd)
    if resultado.returncode not in (0, 1):
        print(f"[AVISO] Locust terminó con código inesperado {resultado.returncode} en {etiqueta}")


def guardar_e_imprimir_resumen(resumenes):
    if not resumenes:
        print("[AVISO] No se encontraron archivos *_stats.csv en reportes.")
        return

    resumen_csv = os.path.join(REPORTES_DIR, "resumen_taller.csv")
    campos = [k for k in resumenes[0].keys() if k != "archivo_html"]
    with open(resumen_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resumenes:
            writer.writerow({k: r[k] for k in campos})

    resumen_html = os.path.join(REPORTES_DIR, "resumen_taller.html")
    generar_resumen_html(resumenes, resumen_html)

    print("\n" + "=" * 95)
    print("RESUMEN FINAL - PRUEBAS DE RENDIMIENTO MODULO TALLER")
    print("=" * 95)
    print(f"{'Caso':<16} {'Carga':<8} {'Req':<7} {'Fallos':<9} {'Med(ms)':<9} {'P95(ms)':<9} {'Max(ms)':<9} {'RPS':<8}")
    print("-" * 95)
    for r in resumenes:
        print(
            f"{r['caso']:<16} {r['carga']:<8} {r['requests']:<7} {r['pct_fallos']:<9} "
            f"{r['mediana_ms']:<9} {r['p95_ms']:<9} {r['max_ms']:<9} {r['rps']:<8}"
        )
    print("=" * 95)
    print(f"CSV consolidado:  {resumen_csv}")
    print(f"HTML consolidado: {resumen_html}")


def main():
    os.makedirs(REPORTES_DIR, exist_ok=True)

    if "--solo-resumen" in sys.argv:
        resumenes = recolectar_resumenes()
        guardar_e_imprimir_resumen(resumenes)
        return

    verificar_bd_prueba()
    verificar_servidor_activo()

    locust_file = os.path.join(BASE_DIR, "locustfile_taller.py")

    for codigo, descripcion, clase in CASOS_FIJOS:
        for usuarios, tasa in NIVELES:
            prefijo = f"{codigo.lower()}_{usuarios}u"
            csv_base = os.path.join(REPORTES_DIR, prefijo)
            html_path = os.path.join(REPORTES_DIR, f"{prefijo}.html")

            cmd = [
                sys.executable, "-m", "locust",
                "-f", locust_file,
                "--host", HOST,
                "--headless",
                "-u", str(usuarios),
                "-r", str(tasa),
                "-t", DURACION_NIVEL,
                "--only-summary",
                "--csv", csv_base,
                "--html", html_path,
                clase,
            ]
            ejecutar_comando(cmd, f"{codigo} | {descripcion} | {usuarios} usuario(s)")

    for codigo, descripcion, archivo_forma, _ in ESPECIALES:
        prefijo = codigo.lower()
        csv_base = os.path.join(REPORTES_DIR, prefijo)
        html_path = os.path.join(REPORTES_DIR, f"{prefijo}.html")

        cmd = [
            sys.executable, "-m", "locust",
            "-f", archivo_forma,
            "--host", HOST,
            "--headless",
            "--only-summary",
            "--csv", csv_base,
            "--html", html_path,
        ]
        ejecutar_comando(cmd, f"{codigo} | {descripcion}")

    resumenes = recolectar_resumenes()
    guardar_e_imprimir_resumen(resumenes)


if __name__ == "__main__":
    main()