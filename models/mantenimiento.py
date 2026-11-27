import os
import subprocess  
import tempfile
from models.bitacora import Bitacora

class Mantenimiento:
    
    DB_USER = "root"
    DB_PASS = ""  
    DATABASES = ["seguridad", "automall"]

    @classmethod
    def _obtener_ruta_ejecutable(cls, ejecutable):
        bin_path = os.environ.get('MYSQL_BIN_PATH', '')
        
        if not bin_path:
            rutas_comunes = [
                r"C:\xampp\mysql\bin",
                r"C:\wamp64\bin\mysql\mysql8.0.26\bin",
                r"/usr/bin",
                r"/usr/local/mysql/bin"
            ]
            for ruta in rutas_comunes:
                if os.path.exists(os.path.join(ruta, ejecutable)) or os.path.exists(os.path.join(ruta, f"{ejecutable}.exe")):
                    bin_path = ruta
                    break

        return os.path.join(bin_path, ejecutable)

    @classmethod
    def generar_respaldo(cls, db_name, cedula):
        if db_name not in cls.DATABASES:
            return {"status": False, "message": "Base de datos no válida", "code": 400}

        filename = f"backup_{db_name}.sql"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        mysqldump_exe = cls._obtener_ruta_ejecutable("mysqldump")

        try:
            args = [mysqldump_exe, "-u", cls.DB_USER]
            if cls.DB_PASS:
                args.append(f"-p{cls.DB_PASS}")
            args.append(db_name)

            with open(filepath, 'w', encoding='utf-8') as out_file:
                subprocess.run(args, stdout=out_file, check=True, shell=False) 

            # Registro en bitácora (Acción 9: Respaldar, Módulo 19: Mantenimiento)
            Bitacora.registrar(cedula, cod_accion=9, cod_modulo=19)

            return {"status": True, "filepath": filepath, "filename": filename}

        except FileNotFoundError:
            return {
                "status": False, 
                "message": f"No se encontró el ejecutable '{mysqldump_exe}'. Asegúrate de configurar la variable de entorno MYSQL_BIN_PATH.", 
                "code": 500
            }
        except subprocess.CalledProcessError as e:
            return {"status": False, "message": f"Error del motor MySQL al respaldar: {str(e)}", "code": 500}

    @classmethod
    def restaurar_respaldo(cls, db_name, file_storage, cedula):
        if db_name not in cls.DATABASES:
            return {"status": False, "message": "Base de datos no válida", "code": 400}

        filepath = os.path.join(tempfile.gettempdir(), f"restore_{db_name}.sql")
        file_storage.save(filepath)
        mysql_exe = cls._obtener_ruta_ejecutable("mysql")

        try:
            args = [mysql_exe, "-u", cls.DB_USER]
            if cls.DB_PASS:
                args.append(f"-p{cls.DB_PASS}")
            args.append(db_name)

            with open(filepath, 'r', encoding='utf-8') as in_file:
                subprocess.run(args, stdin=in_file, check=True, shell=False, stderr=subprocess.PIPE)

           
            if os.path.exists(filepath):
                os.remove(filepath)

          
            Bitacora.registrar(cedula, cod_accion=10, cod_modulo=19)

            return {"status": True, "message": f"Base de datos '{db_name}' restaurada exitosamente."}

        except FileNotFoundError:
            return {
                "status": False, 
                "message": f"No se encontró el ejecutable '{mysql_exe}'. Verifica las rutas de XAMPP.", 
                "code": 500
            }
        except subprocess.CalledProcessError as e:
            error_real = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return {"status": False, "message": f"Error de MySQL: {error_real}", "code": 500}