# utils/session_store.py
import secrets
import threading
import time

# Almacén en memoria del servidor: { token: (cedula_usuario, expira_en) }
_SESIONES_ACTIVAS = {}
_LOCK = threading.Lock()
SESSION_TTL_SECONDS = 8 * 3600  # 8 horas


def _limpiar_expiradas(ahora: float) -> None:
    expirados = [t for t, (_, exp) in _SESIONES_ACTIVAS.items() if exp <= ahora]
    for t in expirados:
        del _SESIONES_ACTIVAS[t]


def crear_sesion(cedula_usuario: str) -> str:
    """Genera un token único, lo registra en memoria y lo retorna."""
    token = secrets.token_hex(32)
    ahora = time.time()
    with _LOCK:
        _limpiar_expiradas(ahora)
        _SESIONES_ACTIVAS[token] = (str(cedula_usuario), ahora + SESSION_TTL_SECONDS)
    return token


def sesion_valida(token: str, cedula_usuario: str) -> bool:
    """Verifica que el token exista en memoria, no haya expirado y pertenezca al usuario."""
    if not token or not cedula_usuario:
        return False
    ahora = time.time()
    with _LOCK:
        entrada = _SESIONES_ACTIVAS.get(token)
        if not entrada:
            return False
        cedula_guardada, expira_en = entrada
        if expira_en <= ahora:
            del _SESIONES_ACTIVAS[token]
            return False
        return cedula_guardada == str(cedula_usuario)


def invalidar_sesion(token: str) -> None:
    """Elimina un token específico de las sesiones activas (logout)."""
    if not token:
        return
    with _LOCK:
        _SESIONES_ACTIVAS.pop(token, None)


def invalidar_sesiones_usuario(cedula_usuario: str) -> None:
    """Elimina todas las sesiones activas de un usuario (por ejemplo al eliminarlo)."""
    if not cedula_usuario:
        return
    cedula_str = str(cedula_usuario)
    with _LOCK:
        tokens = [t for t, (ced, _) in _SESIONES_ACTIVAS.items() if ced == cedula_str]
        for t in tokens:
            del _SESIONES_ACTIVAS[t]
