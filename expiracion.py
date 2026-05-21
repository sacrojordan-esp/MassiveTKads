#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar la expiración de cookies de TikTok Ads.
Muestra solo las cookies que expiran en los próximos 15 días.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

# Cookies que consideramos importantes para el funcionamiento
COOKIES_IMPORTANTES = json.loads(os.getenv("COOKIES_IMPORTANTES", "{}"))

UMBRAL_DIAS = int(os.getenv("UMBRAL_DIAS", "5"))


def cargar_cookies(archivo: str) -> List[Dict]:
    """
    Carga el archivo JSON de cookies.
    Retorna lista de cookies o lista vacía si hay error.
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encuentra el archivo: {archivo}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error de formato JSON en {archivo}: {e}")
        return []


def obtener_estado_expiracion(expiration_timestamp: Optional[float]) -> Tuple[str, str, int]:
    """
    Calcula el estado de una cookie basado en su timestamp de expiración.
    Retorna: (estado_emoji, descripción, días_restantes)
    """
    if not expiration_timestamp:
        return "❓", "Sin fecha", 0

    try:
        fecha_expiracion = datetime.fromtimestamp(expiration_timestamp)
        hoy = datetime.now()
        dias_restantes = (fecha_expiracion - hoy).days

        if dias_restantes > 30:
            return "✅", "Válida (largo plazo)", dias_restantes
        elif dias_restantes > 7:
            return "✅", "Válida", dias_restantes
        elif dias_restantes > 3:
            return "⚠️", "Próxima a expirar", dias_restantes
        elif dias_restantes > 0:
            return "🔴", "Expira pronto", dias_restantes
        elif dias_restantes == 0:
            return "🔴", "Expira hoy", dias_restantes
        else:
            return "❌", "Expirada", dias_restantes
    except (ValueError, OverflowError):
        return "⚠️", "Fecha inválida", 0


def formatear_fecha(timestamp: Optional[float]) -> str:
    """Convierte timestamp a string de fecha o devuelve 'N/A'."""
    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return 'Inválida'
    return 'N/A'


def analizar_cookies_archivo(archivo: str) -> Dict[str, Dict]:
    """
    Analiza un archivo de cookies y devuelve un diccionario
    con la información de las cookies importantes.
    """
    cookies = cargar_cookies(archivo)
    if not cookies:
        return {}

    cookie_map = {}
    for cookie in cookies:
        nombre = cookie.get('name')
        if nombre in COOKIES_IMPORTANTES:
            cookie_map[nombre] = {
                'nombre': nombre,
                'descripcion': COOKIES_IMPORTANTES[nombre],
                'expira': cookie.get('expirationDate'),
                'dominio': cookie.get('domain', 'N/A'),
                'http_only': cookie.get('httpOnly', False)
            }
    return cookie_map


def mostrar_resumen_cuenta(nombre_cuenta: str, info_cookies: Dict[str, Dict]) -> None:
    """
    Muestra un resumen de las cookies que expiran en <= UMBRAL_DIAS días.
    Si ninguna cookie cumple, no muestra nada.
    """
    if not info_cookies:
        return

    # Filtrar cookies que expiran en <= umbral
    cookies_a_mostrar = []
    for nombre, cookie in info_cookies.items():
        expira = cookie['expira']
        if expira:
            try:
                fecha_expiracion = datetime.fromtimestamp(expira)
                dias_restantes = (fecha_expiracion - datetime.now()).days
                if dias_restantes <= UMBRAL_DIAS:
                    cookies_a_mostrar.append((nombre, cookie, dias_restantes))
            except:
                # Si hay error al calcular, no mostrar
                pass

    if not cookies_a_mostrar:
        return

    print(f"\n🔍 {nombre_cuenta}:")
    # Ordenar por días restantes (de menor a mayor)
    for nombre, cookie, dias in sorted(cookies_a_mostrar, key=lambda x: x[2]):
        emoji, estado, _ = obtener_estado_expiracion(cookie['expira'])
        fecha = formatear_fecha(cookie['expira'])
        print(f"   {emoji} {nombre:15} | {fecha} | {dias:2} días | {cookie['descripcion']}")


def verificar_expiracion(archivo_cookies: str, nombre_mostrar: str = None) -> None:
    """
    Función principal para verificar un archivo de cookies.
    Si nombre_mostrar es None, usa el nombre del archivo.
    """
    if nombre_mostrar is None:
        nombre_mostrar = os.path.basename(archivo_cookies).replace('.json', '')

    info = analizar_cookies_archivo(archivo_cookies)
    mostrar_resumen_cuenta(nombre_mostrar, info)


def main():
    """Función principal que recorre las ubicaciones típicas de cookies."""
    print(f"🔐 COOKIES QUE EXPIRAN EN ≤ {UMBRAL_DIAS} DÍAS")

    # Verificar archivo en la raíz
    archivo_raiz = "cookies_tiktok.json"
    if os.path.exists(archivo_raiz):
        verificar_expiracion(archivo_raiz, "Raíz (cookies_tiktok.json)")
    else:
        print("\nℹ️  No hay cookies_tiktok.json en la raíz")

    # Verificar carpeta cuentas
    if os.path.exists("cuentas") and os.path.isdir("cuentas"):
        archivos = [f for f in os.listdir("cuentas") if f.endswith('.json')]
        if archivos:
            print("\n📁 COOKIES EN CARPETA 'cuentas/':")
            for archivo in sorted(archivos):
                ruta = os.path.join("cuentas", archivo)
                nombre = archivo.replace('.json', '')
                verificar_expiracion(ruta, nombre)
        else:
            print("\nℹ️  La carpeta 'cuentas' no contiene archivos .json")
    else:
        print("\nℹ️  No existe la carpeta 'cuentas'")



if __name__ == "__main__":
    main()