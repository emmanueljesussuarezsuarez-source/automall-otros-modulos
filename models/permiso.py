from models.db import ConexionBD
from models.bitacora import Bitacora

class Permiso:
    @staticmethod
    def obtener_roles():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_rol WHERE estatus = 1 ORDER BY cod_rol ASC")
        roles = cursor.fetchall()
        cursor.close()
        conexion.close()
        return roles

    @staticmethod
    def obtener_modulos_activos():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_modulo WHERE estatus = 1 ORDER BY nombre_modulo ASC")
        modulos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return modulos

    @staticmethod
    def obtener_acciones_activas():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM t_acciones WHERE estatus = 1 ORDER BY nom_accion ASC")
        acciones = cursor.fetchall()
        cursor.close()
        conexion.close()
        return acciones

    @staticmethod
    def obtener_permisos_asignados_rol(cod_rol):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT m.cod_modulo, a.cod_accion
            FROM t_rol_permiso rp
            INNER JOIN t_permiso p ON rp.cod_permiso = p.cod_permiso
            INNER JOIN t_modulo m ON p.cod_modulo = m.cod_modulo
            INNER JOIN t_acciones a ON p.cod_accion = a.cod_accion
            WHERE rp.cod_rol = %s
        """
        try:
            cursor.execute(sql, (cod_rol,))
            resultados = cursor.fetchall()
            return [f"{r['cod_modulo']}-{r['cod_accion']}" for r in resultados]
        except Exception as e:
            print(f"Error al obtener permisos asignados: {e}")
            return []
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def sincronizar_permisos(cod_rol, lista_mod_acc, cedula):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        try:
           
            cursor.execute("DELETE FROM t_rol_permiso WHERE cod_rol = %s", (cod_rol,))
            
          
            if lista_mod_acc:
                for item in lista_mod_acc:
                
                    mod, acc = item.split('-')
                    
                   
                    cursor.execute("SELECT cod_permiso FROM t_permiso WHERE cod_modulo = %s AND cod_accion = %s", (mod, acc))
                    permiso_existente = cursor.fetchone()
                    
                    if permiso_existente:
                        cod_permiso = permiso_existente['cod_permiso']
                    else:
                       
                        cursor.execute("INSERT INTO t_permiso (cod_modulo, cod_accion) VALUES (%s, %s)", (mod, acc))
                        cod_permiso = cursor.lastrowid
                    
                   
                    cursor.execute("INSERT INTO t_rol_permiso (cod_rol, cod_permiso) VALUES (%s, %s)", (cod_rol, cod_permiso))

           
            Bitacora.registrar(cedula, cod_accion=3, cod_modulo=23) 

            conexion.commit()
            return {"status": True}
        except Exception as e:
            conexion.rollback()
            print(f"Error crítico al sincronizar los permisos del rol {cod_rol}: {e}")
            return {"status": False, "error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def verificar_acceso(cod_rol, modulo, tipo_permiso):
        
        mapeo_acciones = {
            'p_crear': 'CREAR',
            'p_leer': 'LEER',
            'p_actualizar': 'ACTUALIZAR',
            'p_eliminar': 'ELIMINAR'
        }
        
        accion_real = mapeo_acciones.get(tipo_permiso)
        if not accion_real:
            return False

        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """
            SELECT COUNT(*) AS autorizado
            FROM t_rol_permiso rp
            INNER JOIN t_permiso p ON rp.cod_permiso = p.cod_permiso
            INNER JOIN t_modulo m ON p.cod_modulo = m.cod_modulo
            INNER JOIN t_acciones a ON p.cod_accion = a.cod_accion
            WHERE rp.cod_rol = %s AND m.nombre_modulo = %s AND a.nom_accion = %s
        """
        try:
            cursor.execute(sql, (cod_rol, modulo, accion_real))
            res = cursor.fetchone()
            return True if res and res['autorizado'] > 0 else False
        except Exception as e:
            return False
        finally:
            cursor.close()
            conexion.close()