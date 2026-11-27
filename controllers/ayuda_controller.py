from flask import Blueprint, render_template, session, redirect, url_for

ayuda_bp = Blueprint('ayuda', __name__, url_prefix='/ayuda')

@ayuda_bp.route('/')
def mostrar_manual():
    
    if 'usuario_nombre' not in session and 'cedula_usuario' not in session:
        return redirect(url_for('auth.login'))
    
  
    cod_rol = session.get('cod_rol')
    rol_text = str(session.get('usuario_rol', session.get('rol', ''))).strip().lower()
    
  
    if cod_rol == 1 or 'super' in rol_text:
        return render_template('ayuda/manual_superusuario.html')
    
    elif cod_rol == 2 or 'administrador' in rol_text or 'admin' in rol_text:
        return render_template('ayuda/manual_admin.html')
    
    else:
        return render_template('ayuda/manual_cliente.html')