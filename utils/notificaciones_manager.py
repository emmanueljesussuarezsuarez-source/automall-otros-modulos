import json
import os
import uuid
import threading
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
FILE_PATH = os.path.join(DATA_DIR, 'notificaciones.json')

_lock = threading.Lock()

class NotificacionManager:
    @staticmethod
    def _asegurar_archivo():
        """Crea la carpeta data y el archivo json si no existen."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    @staticmethod
    def _cargar_todas():
        """Lee todas las notificaciones del archivo JSON."""
        NotificacionManager._asegurar_archivo()
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    @staticmethod
    def _guardar_todas(notificaciones):
        """Guarda la lista completa de notificaciones en el JSON."""
        NotificacionManager._asegurar_archivo()
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(notificaciones, f, ensure_ascii=False, indent=4)

    @staticmethod
    def crear(titulo, mensaje, url_destino=None, tipo_destino='TODOS', cod_rol=None, id_cliente=None, roles=None, modulo=None):
        """
        Crea una nueva notificación.
        - tipo_destino: 'TODOS', 'ROL', 'CLIENTE'
        - roles: Lista de códigos de rol si aplica (ej: [1, 3])
        - cod_rol: Código de rol único (ej: 3)
        """
        with _lock:
            notificaciones = NotificacionManager._cargar_todas()
            
            roles_dest = []
            if roles:
                roles_dest = [int(r) for r in roles]
            elif cod_rol is not None:
                roles_dest = [int(cod_rol)]

            nueva = {
                "id": str(uuid.uuid4()),
                "titulo": str(titulo),
                "mensaje": str(mensaje),
                "url_destino": url_destino or "#",
                "tipo_destino": tipo_destino,
                "roles": roles_dest,
                "id_cliente": str(id_cliente) if id_cliente is not None else None,
                "modulo": modulo,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "leido_por": []  # Lista de id_usuario o id_cliente que han leído la notificación
            }
            
            # Insertar al inicio para mantener orden cronológico descendente
            notificaciones.insert(0, nueva)
            
            # Opcional: Limitar historial máximo a 200 notificaciones
            if len(notificaciones) > 200:
                notificaciones = notificaciones[:200]

            NotificacionManager._guardar_todas(notificaciones)
            return nueva

    @staticmethod
    def crear_multiple(notificacion_cliente=None, notificacion_staff=None):
        """Helper conveniente para enviar notificaciones simultáneas al cliente y al staff/roles."""
        if notificacion_cliente:
            NotificacionManager.crear(
                titulo=notificacion_cliente.get('titulo'),
                mensaje=notificacion_cliente.get('mensaje'),
                url_destino=notificacion_cliente.get('url_destino'),
                tipo_destino='CLIENTE',
                id_cliente=notificacion_cliente.get('id_cliente'),
                modulo=notificacion_cliente.get('modulo', 'citas')
            )
        
        if notificacion_staff:
            NotificacionManager.crear(
                titulo=notificacion_staff.get('titulo'),
                mensaje=notificacion_staff.get('mensaje'),
                url_destino=notificacion_staff.get('url_destino'),
                tipo_destino='ROL',
                roles=notificacion_staff.get('roles', [1, 3]),
                modulo=notificacion_staff.get('modulo', 'citas')
            )

    @staticmethod
    def obtener_no_leidas_usuario(id_usuario, cod_rol=None, id_cliente=None):
        """
        Retorna las notificaciones no leídas relevantes para el usuario actual.
        """
        with _lock:
            notificaciones = NotificacionManager._cargar_todas()
            id_usuario_str = str(id_usuario) if id_usuario is not None else ""
            id_cliente_str = str(id_cliente) if id_cliente is not None else ""
            cod_rol_int = int(cod_rol) if cod_rol is not None else None

            resultado = []
            for n in notificaciones:
                # Comprobar si este usuario/cliente ya la leyó
                leido_por = [str(uid) for uid in n.get('leido_por', [])]
                if id_usuario_str in leido_por or (id_cliente_str and id_cliente_str in leido_por):
                    continue

                tipo = n.get('tipo_destino', 'TODOS')
                roles_dest = n.get('roles', [])

                # Super Usuario (Rol 1) recibe notificaciones de ROL y TODOS
                es_superusuario = (cod_rol_int == 1)

                es_destinatario = False

                if tipo == 'TODOS':
                    es_destinatario = True
                elif tipo == 'CLIENTE':
                    if id_cliente_str and str(n.get('id_cliente')) == id_cliente_str:
                        es_destinatario = True
                    elif id_usuario_str and str(n.get('id_cliente')) == id_usuario_str:
                        es_destinatario = True
                elif tipo == 'ROL':
                    if cod_rol_int is not None and (cod_rol_int in roles_dest or es_superusuario):
                        es_destinatario = True

                if es_destinatario:
                    resultado.append(n)

            return resultado

    @staticmethod
    def obtener_historial_usuario(id_usuario, cod_rol=None, id_cliente=None):
        """
        Retorna la lista completa de notificaciones (leídas y no leídas) pertenecientes al usuario.
        """
        with _lock:
            notificaciones = NotificacionManager._cargar_todas()
            id_usuario_str = str(id_usuario) if id_usuario is not None else ""
            id_cliente_str = str(id_cliente) if id_cliente is not None else ""
            cod_rol_int = int(cod_rol) if cod_rol is not None else None

            resultado = []
            for n in notificaciones:
                leido_por = [str(uid) for uid in n.get('leido_por', [])]
                esta_leida = (id_usuario_str in leido_por) or (bool(id_cliente_str) and id_cliente_str in leido_por)

                tipo = n.get('tipo_destino', 'TODOS')
                roles_dest = n.get('roles', [])
                es_superusuario = (cod_rol_int == 1)

                es_destinatario = False
                if tipo == 'TODOS':
                    es_destinatario = True
                elif tipo == 'CLIENTE':
                    if id_cliente_str and str(n.get('id_cliente')) == id_cliente_str:
                        es_destinatario = True
                    elif id_usuario_str and str(n.get('id_cliente')) == id_usuario_str:
                        es_destinatario = True
                elif tipo == 'ROL':
                    if cod_rol_int is not None and (cod_rol_int in roles_dest or es_superusuario):
                        es_destinatario = True

                if es_destinatario:
                    n_copia = dict(n)
                    n_copia['leida'] = esta_leida
                    resultado.append(n_copia)

            return resultado


    @staticmethod
    def marcar_como_leida(id_notificacion, id_usuario):
        """Marca una notificación como leída para el id_usuario dado."""
        with _lock:
            notificaciones = NotificacionManager._cargar_todas()
            id_usuario_str = str(id_usuario)
            modificado = False

            for n in notificaciones:
                if n.get('id') == id_notificacion:
                    leido_por = [str(uid) for uid in n.get('leido_por', [])]
                    if id_usuario_str not in leido_por:
                        n.setdefault('leido_por', []).append(id_usuario_str)
                        modificado = True
                    break

            if modificado:
                NotificacionManager._guardar_todas(notificaciones)
            return modificado

    @staticmethod
    def marcar_todas_leidas(id_usuario, cod_rol=None, id_cliente=None):
        """Marca todas las notificaciones pendientes del usuario como leídas."""
        with _lock:
            notificaciones = NotificacionManager._cargar_todas()
            id_usuario_str = str(id_usuario)
            id_cliente_str = str(id_cliente) if id_cliente is not None else ""
            cod_rol_int = int(cod_rol) if cod_rol is not None else None

            modificado = False
            for n in notificaciones:
                leido_por = [str(uid) for uid in n.get('leido_por', [])]
                
                # Si no la ha leído
                if id_usuario_str not in leido_por and (not id_cliente_str or id_cliente_str not in leido_por):
                    tipo = n.get('tipo_destino', 'TODOS')
                    roles_dest = n.get('roles', [])
                    es_superusuario = (cod_rol_int == 1)

                    es_destinatario = False
                    if tipo == 'TODOS':
                        es_destinatario = True
                    elif tipo == 'CLIENTE' and (str(n.get('id_cliente')) in [id_cliente_str, id_usuario_str]):
                        es_destinatario = True
                    elif tipo == 'ROL' and (cod_rol_int is not None and (cod_rol_int in roles_dest or es_superusuario)):
                        es_destinatario = True

                    if es_destinatario:
                        n.setdefault('leido_por', []).append(id_usuario_str)
                        modificado = True

            if modificado:
                NotificacionManager._guardar_todas(notificaciones)
            return modificado
