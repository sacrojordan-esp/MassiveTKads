import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import os
import re

# ============================================================================
# CONFIGURACIÓN - Constantes principales
# ============================================================================
CARPETA_COOKIES = "cuentas"
CORRECCION_FILE = "correccion.json"

MES = "03"
DIA = "16"
FECHA_API = f"2026-{MES}-{DIA}"
FECHA_EN_NOMBRES = f"{DIA}/{MES}/26"
OUTPUT_EXCEL = f"reporte_multicuentas_{DIA}-{MES}-2026.xlsx"

# ============================================================================
# DICCIONARIO DE IDENTIFICADORES DE CUENTAS
# ============================================================================
CUENTAS_AADVID = {
    "Tik Tok - Paul": "7356312590324154385",
    "Tik Tok - Manuel": "7380485662258266113",  # ← Reemplaza con IDs reales
    "Tik Tok - Raul": "7380190667118641168",      # ← Reemplaza con IDs reales
    "Tik Tok - Marketing 1": "7534576963865051137",     # ← Reemplaza con IDs reales
    "Tik Tok - Marketing 2": "7527435094408593425"     # ← Reemplaza con IDs reales
}

# ============================================================================
# FUNCIÓN: Cargar correcciones (sin cambios)
# ============================================================================
def cargar_correcciones(archivo: str) -> Dict[str, str]:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            correcciones = json.load(f)
        print(f"✅ Correcciones cargadas: {len(correcciones)} patrones")
        return correcciones
    except Exception as e:
        print(f"⚠️ Error cargando correcciones: {e}")
        return {}

# ============================================================================
# FUNCIÓN: Limpiar nombre de campaña (sin cambios)
# ============================================================================
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

# ============================================================================
# FUNCIÓN: Consultar API para UNA cuenta específica (MODIFICADA)
# ============================================================================
def consultar_api_tiktok(archivo_cookies: str, nombre_cuenta: str, aadvid: str) -> List[Dict]:
    """
    Consulta la API para una cuenta específica y devuelve sus campañas.
    """
    print(f"\n📁 Procesando cuenta: {nombre_cuenta} (AADVID: {aadvid})")
    
    # Cargar cookies del archivo
    try:
        with open(archivo_cookies, 'r', encoding='utf-8') as f:
            datos_cookies = json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encuentra el archivo: {archivo_cookies}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error en archivo de cookies: {e}")
        return []
    
    # Convertir cookies a diccionario
    cookies = {}
    for cookie in datos_cookies:
        if 'name' in cookie and 'value' in cookie:
            cookies[cookie['name']] = cookie['value']
    
    print(f"   Cookies cargadas: {len(cookies)}")
    
    # Configurar petición
    url = "https://ads.tiktok.com/api/v4/i18n/statistics/op/ad/list/"
    
    params = {
        "aadvid": aadvid,  # Usar el AADVID del diccionario
        "scene": "campaign_list_v2",
        "req_src": "bidding",
        "msToken": cookies.get("msToken", "")
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "content-type": "application/json",
        "origin": "https://ads.tiktok.com",
        "referer": f"https://ads.tiktok.com/i18n/manage/ad?advid={aadvid}&st={FECHA_API}&et={FECHA_API}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-csrftoken": cookies.get("csrftoken", "")
    }
    
    payload = {
        "common_req": {
            "st": FECHA_API,
            "et": FECHA_API,
            "page": 1,
            "sort_stat": "create_time",
            "sort_order": 1,
            "metrics": [
                "stat_cost",
                "time_attr_san_convert_cnt"
            ],
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
        respuesta = requests.post(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            json=payload,
            timeout=30
        )
        
        print(f"   Código HTTP: {respuesta.status_code}")
        
        if respuesta.status_code != 200:
            print(f"   ⚠️ Error en cuenta {nombre_cuenta}")
            return []
        
        data = respuesta.json()
        
        if data.get('code') != 0:
            print(f"   ⚠️ API Error {data.get('code')}: {data.get('msg')}")
            return []
        
        return data
        
    except Exception as e:
        print(f"❌ Error en petición para {nombre_cuenta}: {e}")
        return []

# ============================================================================
# FUNCIÓN: Procesar respuesta de la API (MODIFICADA para incluir cuenta)
# ============================================================================
def procesar_respuesta_api(respuesta_api: Dict, mapa_correcciones: Dict[str, str], nombre_cuenta: str) -> List[Dict]:
    """
    Extrae y procesa los datos, incluyendo el nombre de la cuenta.
    """
    campañas = []
    
    if not respuesta_api or 'data' not in respuesta_api:
        return campañas
    
    datos = respuesta_api['data']
    
    if 'table' in datos:
        for item in datos['table']:
            nombre_original = item.get('campaign_name', 'Desconocido')
            
            # APLICAR LIMPIEZA AL NOMBRE
            nombre_corregido = limpiar_nombre_campaña(nombre_original, mapa_correcciones)
            
            # Extraer métricas
            stat_cost = '0'
            conversiones = '0'
            
            if 'row_data' in item:
                row_data = item['row_data']
                stat_cost = row_data.get('stat_cost', '0')
                conversiones = row_data.get('time_attr_san_convert_cnt', '0')
            
            # Solo incluir si tiene inversión > 0
            if float(stat_cost) > 0:
                campañas.append({
                    'fecha': FECHA_API,
                    'nombre_campaña': nombre_corregido,
                    'cuenta': nombre_cuenta,
                    'inversion_pen': float(stat_cost),
                    'conversiones': int(conversiones) if conversiones != '0' else 0,
                    'estado': 'Activa' if 'delivery_ok' in str(item.get('campaign_primary_status', '')) else 'En pausa',
                    'nombre_original': nombre_original,
                    'creative_id': item.get('creative_id', '')  # ← NUEVO CAMPO
                })
    
    return campañas

# ============================================================================
# FUNCIÓN: Exportar a Excel (MODIFICADA para incluir cuenta)
# ============================================================================
def exportar_a_excel(todas_campañas: List[Dict], archivo_salida: str):
    """
    Exporta a Excel con el formato:
    Fecha | Nombre de campaña | Cuenta | Inversión | Conversiones
    """
    if not todas_campañas:
        print("❌ No hay datos para exportar")
        return
    
    # Crear DataFrame
    datos_excel = []
    for camp in todas_campañas:
        datos_excel.append({
            'Fecha': camp['fecha'],
            'Nombre de campaña': camp['nombre_campaña'],
            'Cuenta': camp['cuenta'],
            'Inversión (PEN)': camp['inversion_pen'],
            'Conversiones': camp['conversiones'],
            'Creative ID': camp.get('creative_id', '')  # ← NUEVA COLUMNA
        })
    
    df = pd.DataFrame(datos_excel)
    
    # Guardar a Excel
    try:
        nombre_hoja = f'Campañas_{FECHA_API.replace("-", "")}'
        df.to_excel(archivo_salida, index=False, sheet_name=nombre_hoja[:31])
        
        print(f"\n✅ Excel generado: {archivo_salida}")
        print(f"   Formato: Fecha | Nombre | Cuenta | Inversión | Conversiones")
        print(f"   Filas: {len(datos_excel)}")
        print(f"   Cuentas procesadas: {df['Cuenta'].nunique()}")
        
        # Mostrar resumen por cuenta
        print("\n📊 RESUMEN POR CUENTA:")
        for cuenta in df['Cuenta'].unique():
            df_cuenta = df[df['Cuenta'] == cuenta]
            print(f"   {cuenta}: {len(df_cuenta)} campañas, {df_cuenta['Inversión (PEN)'].sum():.2f} PEN")
        
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")


# ============================================================================
# FUNCIÓN PRINCIPAL (MODIFICADA)
# ============================================================================
def main():
    print("=" * 80)
    print(f"🚀 SCRIPT MULTICUENTAS TIKTOK ADS - {FECHA_API}")
    print("=" * 80)
    
    # PASO 1: Cargar correcciones
    print("\n[PASO 1] Cargando mapa de correcciones...")
    mapa_correcciones = cargar_correcciones(CORRECCION_FILE)
    
    # PASO 2: Verificar carpeta de cuentas
    if not os.path.exists(CARPETA_COOKIES):
        print(f"❌ No existe la carpeta: {CARPETA_COOKIES}")
        return
    
    # PASO 3: Procesar cada cuenta
    print("\n[PASO 2] Procesando cuentas...")
    todas_campañas = []
    
    for nombre_cuenta, aadvid in CUENTAS_AADVID.items():
        archivo_cookies = os.path.join(CARPETA_COOKIES, f"{nombre_cuenta}.json")
        
        if not os.path.exists(archivo_cookies):
            print(f"⚠️ No se encuentra {archivo_cookies}, saltando...")
            continue
        
        # Consultar API para esta cuenta
        respuesta = consultar_api_tiktok(archivo_cookies, nombre_cuenta, aadvid)
        
        if respuesta:
            # Procesar campañas de esta cuenta
            campañas_cuenta = procesar_respuesta_api(respuesta, mapa_correcciones, nombre_cuenta)
            todas_campañas.extend(campañas_cuenta)
            print(f"   ✅ {len(campañas_cuenta)} campañas encontradas")
    
    # PASO 4: Mostrar resumen
    print("\n[PASO 3] Mostrando resultados...")
    if todas_campañas:
        print(f"\n📊 TOTAL: {len(todas_campañas)} campañas encontradas en todas las cuentas")
        
        # Mostrar campañas individuales
        for i, camp in enumerate(todas_campañas, 1):
            print(f"\n📌 Campaña #{i}")
            print(f"   📋 Cuenta: {camp['cuenta']}")
            print(f"   📋 Producto: {camp['nombre_campaña']}")
            print(f"   💰 Inversión: {camp['inversion_pen']:.2f} PEN")
            print(f"   🔄 Conversiones: {camp['conversiones']}")
    else:
        print("❌ No se encontraron campañas en ninguna cuenta")
    
    # PASO 5: Exportar a Excel
    print("\n[PASO 4] Exportando a Excel...")
    exportar_a_excel(todas_campañas, OUTPUT_EXCEL)

if __name__ == "__main__":
    main()