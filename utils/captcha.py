# CAPTCHA DAVID
import io
import time
import random
from flask import session
from PIL import Image, ImageDraw, ImageFont

CARACTERES_PERMITIDOS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
DURACION_CAPTCHA_SEGUNDOS = 300


def _obtener_fuente(tamanio=30):
    try:
        return ImageFont.truetype("arial.ttf", tamanio)
    except Exception:
        try:
            return ImageFont.load_default(size=tamanio)
        except Exception:
            return ImageFont.load_default()


def crear_captcha_imagen(longitud=5, ancho=200, alto=55):
    codigo = "".join(random.choice(CARACTERES_PERMITIDOS) for _ in range(longitud))

    bg_color = (
        random.randint(235, 250),
        random.randint(235, 250),
        random.randint(235, 250)
    )
    imagen = Image.new("RGB", (ancho, alto), color=bg_color)
    dibujo = ImageDraw.Draw(imagen)

    for _ in range(70):
        punto_x = random.randint(0, ancho - 1)
        punto_y = random.randint(0, alto - 1)
        color_punto = (
            random.randint(150, 210),
            random.randint(150, 210),
            random.randint(150, 210)
        )
        dibujo.point((punto_x, punto_y), fill=color_punto)

    for _ in range(4):
        linea_inicio = (random.randint(0, ancho // 3), random.randint(0, alto))
        linea_fin = (random.randint(ancho // 2, ancho), random.randint(0, alto))
        color_linea = (
            random.randint(130, 190),
            random.randint(130, 190),
            random.randint(130, 190)
        )
        dibujo.line([linea_inicio, linea_fin], fill=color_linea, width=random.randint(1, 2))

    fuente = _obtener_fuente(30)
    espaciado = ancho // (longitud + 1)
    
    colores_texto = [
        (13, 110, 253),
        (33, 37, 41),
        (102, 16, 242),
        (13, 148, 136),
        (220, 53, 69),
        (11, 94, 215)
    ]

    for i, char in enumerate(codigo):
        x = int((i + 0.5) * espaciado + random.randint(-4, 4))
        y = random.randint(8, 16)
        color = random.choice(colores_texto)
        dibujo.text((x, y), char, font=fuente, fill=color)

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    return codigo, buffer.getvalue()


def generar_captcha_sesion():
    codigo, bytes_png = crear_captcha_imagen()
    session['captcha_codigo'] = codigo
    session['captcha_tiempo'] = time.time()
    return bytes_png


def validar_captcha(codigo_usuario):
    codigo_guardado = session.pop('captcha_codigo', None)
    tiempo_guardado = session.pop('captcha_tiempo', None)

    if not codigo_guardado or not tiempo_guardado:
        return False, "El código de seguridad no se encontró o ha expirado. Por favor, recarga el código."

    if (time.time() - float(tiempo_guardado)) > DURACION_CAPTCHA_SEGUNDOS:
        return False, "El código de seguridad ha expirado. Por favor, genera uno nuevo."

    if not codigo_usuario or not isinstance(codigo_usuario, str):
        return False, "Debes ingresar el código de seguridad."

    if codigo_guardado.strip().upper() != codigo_usuario.strip().upper():
        return False, "El código de seguridad (CAPTCHA) es incorrecto."

    return True, "Validación exitosa."
