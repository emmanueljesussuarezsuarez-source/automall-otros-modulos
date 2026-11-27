from models.db import ConexionBD


class Bitacora:
    @staticmethod
    def registrar(cedula_usuario, cod_accion, cod_modulo):
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor()
        
        sql = """
            INSERT INTO t_bitacora (cedula_usuario, cod_accion, cod_modulo) 
            VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(sql, (cedula_usuario, cod_accion, cod_modulo))
            conexion.commit()
        except Exception as e:
            print(f"Error al registrar en bitácora: {e}")
        finally:
            cursor.close()
            conexion.close()


    @staticmethod
    def obtener_todas():
        conexion = ConexionBD.obtener_conexion_seguridad()
        cursor = conexion.cursor(dictionary=True)
        
        sql = """
            SELECT 
                b.fecha, 
                b.cedula_usuario, 
                u.nombre,
                u.apellido,
                r.nombre_rol AS rol,
                a.nom_accion AS accion,
                m.nombre_modulo AS modulo
            FROM t_bitacora b
            LEFT JOIN t_usuario u ON u.cedula_usuario = b.cedula_usuario
            LEFT JOIN t_rol r ON r.cod_rol = u.cod_rol
            LEFT JOIN t_acciones a ON b.cod_accion = a.cod_accion
            LEFT JOIN t_modulo m ON b.cod_modulo = m.cod_modulo
            ORDER BY b.fecha DESC
        """
        try:
            cursor.execute(sql)
            logs = cursor.fetchall()
            return logs if logs else []
        except Exception as e:
            print(f"Error al obtener bitácora: {e}")
            return []
        finally:
            cursor.close()
            conexion.close()