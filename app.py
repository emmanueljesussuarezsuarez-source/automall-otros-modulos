from flask import Flask, render_template, session, request 
from dotenv import load_dotenv
from models.catalogo import Catalogo
from models.permiso import Permiso

import os

load_dotenv() # Esto lee el archivo .env automáticamente

# Importación de todos los Blueprints del sistema
from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.vehiculos_controller import vehiculos_bp
from controllers.catalogo_controller import catalogo_bp
from controllers.marca_controller import marca_bp
from controllers.modelo_controller import modelo_bp
from controllers.propietario_controller import propietario_bp 
from controllers.venta_controller import ventas_bp 
from controllers.citas_controller import citas_bp 
from controllers.permisos_controller import permisos_bp
from controllers.bitacora_controller import bitacora_bp
from controllers.mantenimientobd_controller import mantenimiento_bp
from controllers.tallercontroller import tallerbp
from controllers.mantenimiento_operacional_controller import mantenimiento_operacional_bp
from controllers.reporte_mantenimiento_operacional_controller import reporte_mantenimiento_operacional_bp
from controllers.servicios_controller import servicios_bp
from controllers.reporte_servicios_controller import reporte_servicios_bp
from controllers.pago_controller import pagos_bp
from controllers.clientes_controller import clientes_bp
from controllers.vendedor_controller import vendedor_bp
from controllers.compra_controller import compra_bp
from controllers.insumo_controller import insumo_bp
from controllers.tasa_controller import tasa_bp
from controllers.reportes_estadisticos_controller import estadisticas_bp
from controllers.rolcontroller import roles_bp
from controllers.configuracion_controller import config_bp
from controllers.bancos import bancos_bp
from controllers.metodo import metodos_pago_bp
from controllers.monedas import moneda_bp
from controllers.notificaciones_controller import notificaciones_bp
from controllers.asistente import asistente_bp
from controllers.ayuda_controller import ayuda_bp  # <-- NUEVO: Blueprint del Manual de Usuario y Ayuda


app = Flask(__name__)
app.secret_key = '123456789' # nosec B105

# Registro de todos los Blueprints en la aplicación Flask
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(vehiculos_bp)
app.register_blueprint(catalogo_bp)
app.register_blueprint(marca_bp)
app.register_blueprint(modelo_bp)
app.register_blueprint(propietario_bp)
app.register_blueprint(citas_bp)
app.register_blueprint(permisos_bp)
app.register_blueprint(bitacora_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(mantenimiento_bp)
app.register_blueprint(tallerbp)
app.register_blueprint(mantenimiento_operacional_bp)
app.register_blueprint(reporte_mantenimiento_operacional_bp)
app.register_blueprint(servicios_bp)
app.register_blueprint(reporte_servicios_bp)
app.register_blueprint(pagos_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(vendedor_bp)
app.register_blueprint(compra_bp)
app.register_blueprint(insumo_bp)
app.register_blueprint(tasa_bp)
app.register_blueprint(estadisticas_bp)
app.register_blueprint(roles_bp)
app.register_blueprint(config_bp)
app.register_blueprint(bancos_bp)
app.register_blueprint(metodos_pago_bp)
app.register_blueprint(moneda_bp)
app.register_blueprint(notificaciones_bp)
app.register_blueprint(asistente_bp)
app.register_blueprint(ayuda_bp)  # <-- NUEVO: Registramos el blueprint de ayuda


# --- CONTEXT PROCESSOR SEGURO ---
@app.context_processor
def inject_permisos():
    def tiene_permiso(modulo, tipo_permiso):
        cod_rol = session.get('cod_rol')
        
        if not cod_rol:
            return False
        
        # Si es Super Usuario (Rol 1), omitimos la consulta y damos acceso total en las vistas
        if cod_rol == 1:
            return True
            
        # Delegamos la validación y consulta SQL directamente a la capa del Modelo
        return Permiso.verificar_acceso(cod_rol, modulo, tipo_permiso)
        
    return dict(tiene_permiso=tiene_permiso)


@app.route('/')
def index():
    todos_disponibles = Catalogo.obtener_disponibles()
    vehiculos_destacados = todos_disponibles[:6] 
    
    return render_template('index.html', vehiculos=vehiculos_destacados)

if __name__ == '__main__':
    app.run(debug=True)  # nosec B201