import mysql.connector
from config import Config

class ConexionBD:
    @staticmethod
    def obtener_conexion():
       
        return mysql.connector.connect(**Config.DB_NEGOCIO)

    @staticmethod
    def obtener_conexion_seguridad():
        
        return mysql.connector.connect(**Config.DB_SEGURIDAD)