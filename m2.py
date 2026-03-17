#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Respuesta Automática a Comentarios en TikTok Ads
VERSIÓN CORREGIDA - Usa el endpoint que SÍ funciona
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional
import requests

# ============================================================================
# IMPORTACIONES DESDE m.py
# ============================================================================
try:
    from m import CARPETA_COOKIES, CUENTAS_AADVID
    print("✅ Constantes importadas desde m.py")
except ImportError:
    print("⚠️ No se pudo importar desde m.py, usando valores por defecto")
    CARPETA_COOKIES = "cuentas"
    CUENTAS_AADVID = {
        "Tik Tok - Paul": "7356312590324154385",
        "Tik Tok - Manuel": "7380485662258266113",
        "Tik Tok - Raul": "7380190667118641168",
        "Tik Tok - Marketing 1": "7534576963865051137",
        "Tik Tok - Marketing 2": "7527435094408593425"
    }

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

MENSAJE_RESPUESTA = "👋 ¡Hola! Contamos con diferentes promociones y realizamos envíos diarios a todo Perú. Para más información, haz clic en el botón del video o visita nuestro perfil ✨"
TIEMPO_ESPERA = 3

# ============================================================================
# FUNCIONES CORREGIDAS
# ============================================================================

def cargar_cookies(archivo_cookies: str) -> Dict[str, str]:
    """Carga cookies desde archivo JSON."""
    try:
        with open(archivo_cookies, 'r', encoding='utf-8') as f:
            datos_cookies = json.load(f)
        return {c['name']: c['value'] for c in datos_cookies if 'name' in c and 'value' in c}
    except Exception as e:
        print(f"   ❌ Error cargando cookies: {e}")
        return {}


def obtener_identidad_corregido(archivo_cookies: str, aadvid: str, item_id: str) -> Optional[Dict]:
    """
    Obtiene la identidad usando el endpoint que SÍ funciona.
    Basado en el curl exitoso.
    """
    print(f"   🔑 Obteniendo identidad para item_id: {item_id}")
    
    cookies = cargar_cookies(archivo_cookies)
    if not cookies:
        return None
    
    # ENDPOINT CORRECTO - EL QUE SÍ FUNCIONA
    url = "https://ads.tiktok.com/api/v3/i18n/identity/user_info/"
    params = {
        "aadvid": aadvid,
        "item_id": item_id,
        "is_spark_ads": "true",
        "msToken": cookies.get("msToken", "")
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-csrftoken": cookies.get("csrftoken", cookies.get("x-creative-csrf-token", "")),
        "referer": f"https://ads.tiktok.com/i18n/material/comment/list?aadvid={aadvid}&is_refresh_page=true"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=30)
        
        if response.status_code != 200:
            print(f"   ⚠️ Error HTTP: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
            return None
        
        data = response.json()
        print(f"   Respuesta completa: {json.dumps(data, indent=2)[:500]}...")  # Debug
        
        if data.get('code') != 0:
            print(f"   ⚠️ API Error: {data.get('msg')}")
            return None
        
        # La estructura puede ser diferente, exploramos
        if 'data' in data:
            # Buscar identity_list o similar
            if 'user_infos' in data['data'] and data['data']['user_infos']:
                identidad = data['data']['user_infos'][0]  # Tomamos el primer elemento
                print(f"   ✅ Identidad obtenida: {identidad.get('identity_id')} (tipo: {identidad.get('identity_type')})")
                return identidad
        
    except Exception as e:
        print(f"   ❌ Error en petición: {e}")
        return None


def obtener_comentarios(archivo_cookies: str, aadvid: str, identidad: Dict, item_id: str) -> List[Dict]:
    """Obtiene comentarios usando la identidad (VERSIÓN GET)"""
    print(f"   📥 Obteniendo comentarios...")
    
    cookies = cargar_cookies(archivo_cookies)
    if not cookies:
        return []
    
    url = "https://ads.tiktok.com/api/v3/i18n/common_word/query/"
    params = {
        "aadvid": aadvid,
        "msToken": cookies.get("msToken", ""),
        # Los parámetros de la identidad van en la URL, no en el body
        "identity_type": identidad.get('identity_type'),
        "identity_id": identidad.get('identity_id'),
        "item_id": item_id,
        "need_comment_word": "true",
        "cursor": "0",
        "limit": "50"
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-csrftoken": cookies.get("csrftoken", cookies.get("x-creative-csrf-token", "")),
        "referer": f"https://ads.tiktok.com/i18n/material/comment/list?aadvid={aadvid}&is_refresh_page=true"
    }
    
    try:
        # CAMBIO IMPORTANTE: Usamos GET en lugar de POST
        response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=30)
        
        if response.status_code != 200:
            print(f"   ⚠️ Error HTTP: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
            return []
        
        data = response.json()
        if data.get('code') != 0:
            print(f"   ⚠️ API Error: {data.get('msg')}")
            return []
        
        if 'data' in data and 'comments' in data['data']:
            comentarios = data['data']['comments']
            print(f"   ✅ {len(comentarios)} comentarios obtenidos")
            return comentarios
        else:
            print("   ⚠️ No se encontraron comentarios en la respuesta")
            print(f"   Estructura: {list(data['data'].keys()) if 'data' in data else 'sin data'}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error en petición: {e}")
        return []


def responder_comentario(archivo_cookies: str, aadvid: str, identidad: Dict, comentario: Dict) -> bool:
    """Responde a un comentario."""
    print(f"   💬 Respondiendo a comentario ID: {comentario.get('comment_id')}")
    
    cookies = cargar_cookies(archivo_cookies)
    if not cookies:
        return False
    
    url = "https://ads.tiktok.com/api/v3/i18n/comment/reply/"
    params = {
        "aadvid": aadvid,
        "msToken": cookies.get("msToken", "")
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "content-type": "application/json",
        "origin": "https://ads.tiktok.com",
        "referer": f"https://ads.tiktok.com/i18n/material/comment/list?aadvid={aadvid}&is_refresh_page=true",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-csrftoken": cookies.get("csrftoken", cookies.get("x-creative-csrf-token", "")),
        "trace-log-adv-id": aadvid
    }
    
    payload = {
        "identity_type": identidad.get('identity_type'),
        "identity_id": identidad.get('identity_id'),
        "item_id": comentario.get('item_id', item_id_global),
        "text": MENSAJE_RESPUESTA,
        "comment_type": comentario.get('comment_type', 2),
        "comment_id": comentario.get('comment_id'),
        "creative_id": comentario.get('creative_id', item_id_global)
    }
    
    try:
        response = requests.post(url, params=params, headers=headers, cookies=cookies, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"      ⚠️ Error HTTP: {response.status_code}")
            return False
        
        data = response.json()
        if data.get('code') == 0:
            print(f"      ✅ Respuesta enviada! ID: {data.get('data', {}).get('comment_id')}")
            return True
        else:
            print(f"      ⚠️ API Error: {data.get('msg')} (código: {data.get('code')})")
            return False
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False


def filtrar_pendientes(comentarios: List[Dict]) -> List[Dict]:
    """Filtra comentarios sin respuesta."""
    return [c for c in comentarios if c.get('reply_comment_total', 0) == 0]


def procesar_item_id(archivo_cookies: str, nombre_cuenta: str, aadvid: str, item_id: str, modo_prueba: bool) -> int:
    """Procesa un item_id completo."""
    global item_id_global
    item_id_global = item_id
    
    print(f"\n   📌 Procesando item_id: {item_id}")
    
    # PASO 1: Obtener identidad (VERSIÓN CORREGIDA)
    identidad = obtener_identidad_corregido(archivo_cookies, aadvid, item_id)
    if not identidad:
        print("   ⚠️ No se pudo obtener identidad. Abortando este item.")
        return 0
    
    # PASO 2: Obtener comentarios
    comentarios = obtener_comentarios(archivo_cookies, aadvid, identidad, item_id)
    if not comentarios:
        return 0
    
    # PASO 3: Filtrar pendientes
    pendientes = filtrar_pendientes(comentarios)
    print(f"   📊 {len(pendientes)}/{len(comentarios)} comentarios pendientes")
    
    if not pendientes:
        return 0
    
    # PASO 4: Responder (o simular)
    respondidos = 0
    for i, comentario in enumerate(pendientes, 1):
        print(f"\n   📝 Comentario #{i} de {len(pendientes)}")
        print(f"      Usuario: {comentario.get('user_display_name', 'Desconocido')}")
        print(f"      Texto: {comentario.get('text', '')[:100]}...")
        
        if modo_prueba:
            print(f"      [PRUEBA] Se enviaría: {MENSAJE_RESPUESTA[:100]}...")
            respondidos += 1
        else:
            if responder_comentario(archivo_cookies, aadvid, identidad, comentario):
                respondidos += 1
                time.sleep(TIEMPO_ESPERA)
    
    return respondidos


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Responder automáticamente a comentarios')
    parser.add_argument('--items', '-i', nargs='+', required=True, help='item_ids a procesar')
    parser.add_argument('--cuentas', '-c', nargs='+', help='Cuentas a procesar')
    parser.add_argument('--modo-prueba', '-p', action='store_true', help='Modo prueba')
    parser.add_argument('--espera', '-e', type=int, default=3, help='Segundos entre respuestas')
    
    args = parser.parse_args()
    
    global TIEMPO_ESPERA
    TIEMPO_ESPERA = args.espera
    
    cuentas_procesar = args.cuentas or list(CUENTAS_AADVID.keys())
    
    print("="*80)
    print("🤖 RESPUESTA AUTOMÁTICA A COMENTARIOS - TIKTOK ADS (VERSIÓN CORREGIDA)")
    print("="*80)
    print(f"📱 Items: {', '.join(args.items)}")
    print(f"👥 Cuentas: {', '.join(cuentas_procesar)}")
    print(f"⏱️  Espera: {TIEMPO_ESPERA}s")
    print(f"🎯 Modo prueba: {'SÍ' if args.modo_prueba else 'NO'}")
    print("="*80)
    
    if not os.path.exists(CARPETA_COOKIES):
        print(f"❌ No existe carpeta: {CARPETA_COOKIES}")
        return
    
    total_respondidos = 0
    
    for nombre_cuenta in cuentas_procesar:
        if nombre_cuenta not in CUENTAS_AADVID:
            print(f"\n⚠️ Cuenta '{nombre_cuenta}' no encontrada")
            continue
        
        aadvid = CUENTAS_AADVID[nombre_cuenta]
        archivo_cookies = os.path.join(CARPETA_COOKIES, f"{nombre_cuenta}.json")
        
        if not os.path.exists(archivo_cookies):
            print(f"\n⚠️ No existe {archivo_cookies}")
            continue
        
        print(f"\n{'='*60}")
        print(f"📋 PROCESANDO: {nombre_cuenta}")
        print(f"{'='*60}")
        
        for item_id in args.items:
            respondidos = procesar_item_id(archivo_cookies, nombre_cuenta, aadvid, item_id, args.modo_prueba)
            total_respondidos += respondidos
    
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"✅ Items procesados: {len(args.items)}")
    print(f"✅ Cuentas: {len(set(cuentas_procesar) & set(CUENTAS_AADVID.keys()))}")
    if args.modo_prueba:
        print(f"✅ Respuestas simuladas: {total_respondidos} (MODO PRUEBA)")
    else:
        print(f"✅ Respuestas enviadas: {total_respondidos}")
    print("="*80)


if __name__ == "__main__":
    main()