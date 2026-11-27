from models.db import ConexionBD
from datetime import datetime

class Tasa:
    @staticmethod
    def get_tasa():
        conexion = ConexionBD.obtener_conexion()
       
        cursor = conexion.cursor(dictionary=True) 
        
        
        cursor.execute("SELECT * FROM tasa_cambio ORDER BY id DESC LIMIT 1")
        resultado = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        return resultado

    @staticmethod
    def guardar_nueva_tasa(valor):
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor()
        
        fecha_actual = datetime.now().date()
        
        cursor.execute(
            "INSERT INTO tasa_cambio (valor, fecha) VALUES (%s, %s)", 
            (valor, fecha_actual)
        )
        
        conexion.commit()
        cursor.close()
        conexion.close()