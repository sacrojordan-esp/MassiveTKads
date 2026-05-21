#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para reporte de campañas TikTok Ads.

Uso:
  python m.py                # Reporte de ayer
  python m.py 2026-03-27     # Reporte para una fecha específica
"""

import json
import os
import re
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN DESDE .env
# ============================================================================

load_dotenv()

CARPETA_COOKIES = os.getenv("CARPETA_COOKIES", "cuentas")
CORRECCION_FILE = os.getenv("CORRECCION_FILE", "correccion.json")

CUENTAS_AADVID = json.loads(os.getenv("CUENTAS_AADVID", "{}"))

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_cookies(archivo_cookies: str) -> Dict[str, str]:
    try:
        with open(archivo_cookies, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return {c['name']: c['value'] for c in datos if 'name' in c and 'value' in c}
    except Exception as e:
        print(f"   ❌ Error cargando cookies: {e}")
        return {}

def cargar_correcciones(archivo: str) -> Dict[str, str]:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error cargando correcciones: {e}")
        return {}

def limpiar_nombre_campaña(nombre_original: str, mapa_correcciones: Dict[str, str]) -> str:
    if not nombre_original or nombre_original == 'Unknown':
        return nombre_original

    producto = nombre_original
    patron1 = r'\d{2}/\d{2}/\d{2}\s*\|\s*C\s*\|\s*(.*?)\s*\|\s*SMART\s*\d+'
    match = re.search(patron1, nombre_original, re.IGNORECASE)
    if not match:
        patron2 = r'\d{2}/\d{2}/\d{2}\s*\|\s*(.*?)\s*\|\s*SMART\s*\d+'
        match = re.search(patron2, nombre_original, re.IGNORECASE)

    if match:
        producto = match.group(1).strip()
    else:
        producto = nombre_original

    for patron, correccion in mapa_correcciones.items():
        if patron.upper() in producto.upper():
            return correccion
    return producto

def consultar_api_tiktok(archivo_cookies: str, nombre_cuenta: str, aadvid: str, fecha: str) -> Optional[Dict]:
    print(f"\n📁 Procesando cuenta: {nombre_cuenta} (AADVID: {aadvid})")
    cookies = cargar_cookies(archivo_cookies)
    if not cookies:
        return None

    url = "https://ads.tiktok.com/api/v4/i18n/statistics/op/ad/list/"
    params = {
        "aadvid": aadvid,
        "scene": "campaign_list_v2",
        "req_src": "bidding",
        "msToken": cookies.get("msToken", "")
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "content-type": "application/json",
        "origin": "https://ads.tiktok.com",
        "referer": f"https://ads.tiktok.com/i18n/manage/ad?advid={aadvid}&st={fecha}&et={fecha}",
        "user-agent": "Mozilla/5.0",
        "x-csrftoken": cookies.get("csrftoken", "")
    }
    payload = {
        "common_req": {
            "st": fecha,
            "et": fecha,
            "page": 1,
            "sort_stat": "create_time",
            "sort_order": 1,
            "metrics": ["stat_cost", "time_attr_san_convert_cnt"],
            "dimensions": ["creative_id"],
            "filters": [
                {"field": "show_cnt", "in_field_values": ["0"], "filter_type": 6},
                {"field": "creative_status", "filter_type": 0, "in_field_values": ["no_delete"]}
            ],
            "page_size": 50
        },
        "extra": {
            "scene": "campaign_list_v2",
            "list_version": "v2",
            "preload": "creative"
        }
    }

    try:
        resp = requests.post(url, params=params, headers=headers, cookies=cookies, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"   ⚠️ HTTP {resp.status_code}")
            return None
        data = resp.json()
        if data.get('code') != 0:
            print(f"   ⚠️ API error: {data.get('msg')} (código {data.get('code')})")
            return None
        return data
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def procesar_respuesta_api(respuesta_api: Dict, mapa_correcciones: Dict[str, str], nombre_cuenta: str, fecha: str) -> List[Dict]:
    campañas = []
    if not respuesta_api or 'data' not in respuesta_api:
        return campañas

    datos = respuesta_api['data']
    if 'table' in datos:
        for item in datos['table']:
            nombre_original = item.get('campaign_name', 'Desconocido')
            nombre_corregido = limpiar_nombre_campaña(nombre_original, mapa_correcciones)
            stat_cost = '0'
            conversiones = '0'
            if 'row_data' in item:
                row_data = item['row_data']
                stat_cost = row_data.get('stat_cost', '0')
                conversiones = row_data.get('time_attr_san_convert_cnt', '0')
            if float(stat_cost) > 0:
                campañas.append({
                    'fecha': fecha,
                    'nombre_campaña': nombre_corregido,
                    'cuenta': nombre_cuenta,
                    'inversion_pen': float(stat_cost),
                    'conversiones': int(conversiones) if conversiones != '0' else 0,
                    'estado': 'Activa' if 'delivery_ok' in str(item.get('campaign_primary_status', '')) else 'En pausa',
                    'nombre_original': nombre_original,
                    'creative_id': item.get('creative_id', '')
                })
    return campañas

def exportar_reporte_excel(todas_campañas: List[Dict], archivo_salida: str):
    if not todas_campañas:
        print("❌ No hay datos para exportar")
        return

    df = pd.DataFrame(todas_campañas)
    columnas = ['fecha', 'nombre_campaña', 'cuenta', 'inversion_pen', 'conversiones', 'creative_id']
    df = df[columnas].rename(columns={
        'fecha': 'Fecha',
        'nombre_campaña': 'Nombre de campaña',
        'cuenta': 'Cuenta',
        'inversion_pen': 'Inversión (PEN)',
        'conversiones': 'Conversiones',
        'creative_id': 'Creative ID'
    })

    # Mostrar decimales con coma (como texto para que se vea directamente)
    df['Inversión (PEN)'] = df['Inversión (PEN)'].apply(lambda x: f"{x:.2f}".replace('.', ','))

    with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Campañas')
        # Opcional: ajustar ancho de columnas
        workbook = writer.book
        worksheet = writer.sheets['Campañas']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"\n✅ Excel generado: {archivo_salida}")
    print(f"   Filas: {len(df)}")
    print(f"   Cuentas: {df['Cuenta'].nunique()}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Reporte de campañas TikTok Ads')
    parser.add_argument('fecha', nargs='?', help='Fecha en formato YYYY-MM-DD (por defecto ayer)')
    parser.add_argument('--output', '-o', help='Archivo Excel de salida (opcional)')
    parser.add_argument('--cuentas', '-c', nargs='+', help='Lista de nombres de cuenta (por defecto todas)')
    args = parser.parse_args()

    if args.fecha:
        try:
            datetime.strptime(args.fecha, "%Y-%m-%d")
            fecha = args.fecha
        except ValueError:
            print(f"❌ Fecha inválida: {args.fecha}. Use formato YYYY-MM-DD")
            return
    else:
        fecha = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 No se especificó fecha, usando ayer: {fecha}")

    cuentas = args.cuentas or list(CUENTAS_AADVID.keys())
    output = args.output or f"reporte_multicuentas_{fecha}.xlsx"

    print("=" * 80)
    print(f"📊 REPORTE DE CAMPAÑAS TIKTOK ADS - {fecha}")
    print("=" * 80)

    mapa_correcciones = cargar_correcciones(CORRECCION_FILE)

    if not os.path.exists(CARPETA_COOKIES):
        print(f"❌ No existe la carpeta: {CARPETA_COOKIES}")
        return

    todas_campañas = []
    for nombre_cuenta in cuentas:
        if nombre_cuenta not in CUENTAS_AADVID:
            print(f"⚠️ Cuenta '{nombre_cuenta}' no encontrada")
            continue
        aadvid = CUENTAS_AADVID[nombre_cuenta]
        archivo_cookies = os.path.join(CARPETA_COOKIES, f"{nombre_cuenta}.json")
        if not os.path.exists(archivo_cookies):
            print(f"⚠️ No existe {archivo_cookies}")
            continue

        respuesta = consultar_api_tiktok(archivo_cookies, nombre_cuenta, aadvid, fecha)
        if respuesta:
            campañas = procesar_respuesta_api(respuesta, mapa_correcciones, nombre_cuenta, fecha)
            todas_campañas.extend(campañas)
            print(f"   ✅ {len(campañas)} campañas encontradas")

    if todas_campañas:
        exportar_reporte_excel(todas_campañas, output)
        total_inv = sum(c['inversion_pen'] for c in todas_campañas)
        total_conv = sum(c['conversiones'] for c in todas_campañas)
        print(f"\n📈 TOTAL: {len(todas_campañas)} campañas | Inversión: {total_inv:.2f} PEN | Conversiones: {total_conv}")
    else:
        print("❌ No se encontraron campañas con inversión > 0")

if __name__ == '__main__':
    main()