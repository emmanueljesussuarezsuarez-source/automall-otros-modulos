import os

_ES_TESTING = os.getenv("FLASK_ENV", "").lower() == "testing"


class Config:
    # Base de datos principal (Vehículos, Ventas, Clientes)
    DB_NEGOCIO = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),  # nosec B105
        'database': os.getenv('DB_NEGOCIO_NAME', 'automall_test' if _ES_TESTING else 'automall')
    }

    # Base de datos de seguridad (Usuarios, Permisos, Bitácora)
    DB_SEGURIDAD = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),  # nosec B105
        'database': os.getenv('DB_SEGURIDAD_NAME', 'seguridad_test' if _ES_TESTING else 'seguridad')
    }
