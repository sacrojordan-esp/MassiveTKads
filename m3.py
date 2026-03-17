# ver_comentarios.py
import json
import os
import requests
from m import CARPETA_COOKIES, CUENTAS_AADVID

def cargar_cookies(archivo):
    with open(archivo, 'r') as f:
        datos = json.load(f)
    return {c['name']: c['value'] for c in datos if 'name' in c and 'value' in c}

def verificar_comentarios(archivo_cookies, aadvid, item_id, nombre):
    cookies = cargar_cookies(archivo_cookies)
    
    # Primero obtener identidad
    url_identidad = "https://ads.tiktok.com/api/v3/i18n/identity/user_info/"
    params_identidad = {
        "aadvid": aadvid,
        "item_id": item_id,
        "is_spark_ads": "true",
        "msToken": cookies.get("msToken", "")
    }
    headers = {
        "accept": "application/json",
        "x-csrftoken": cookies.get("csrftoken", ""),
        "user-agent": "Mozilla/5.0"
    }
    
    try:
        r = requests.get(url_identidad, params=params_identidad, headers=headers, cookies=cookies)
        data = r.json()
        if 'user_infos' in data.get('data', {}):
            identidad = data['data']['user_infos'][0]
            
            # Obtener comentarios
            url_comentarios = "https://ads.tiktok.com/api/v3/i18n/common_word/query/"
            params_comentarios = {
                "aadvid": aadvid,
                "msToken": cookies.get("msToken", ""),
                "identity_type": identidad['identity_type'],
                "identity_id": identidad['identity_id'],
                "item_id": item_id,
                "need_comment_word": "true",
                "cursor": "0",
                "limit": "50"
            }
            
            r2 = requests.get(url_comentarios, params=params_comentarios, headers=headers, cookies=cookies)
            data2 = r2.json()
            total = data2.get('data', {}).get('total_count', 0)
            print(f"   {nombre}: {total} comentarios")
            return total
    except Exception as e:
        print(f"   Error con {nombre}: {e}")
        return 0

# Lista de anuncios a verificar
anuncios = [
    ("Tik Tok - Paul", "7356312590324154385", "1859582886016114", "Adaptador Taladro"),
    ("Tik Tok - Paul", "7356312590324154385", "1859572451025985", "Lámpara Solar"),
    ("Tik Tok - Manuel", "7380485662258266113", "1859487598083234", "Libro Pre-escolar"),
    ("Tik Tok - Manuel", "7380485662258266113", "1859380270134321", "Libros Caligrafía"),
    ("Tik Tok - Marketing 2", "7527435094408593425", "1858948178333713", "Destornillador")
]

print("🔍 VERIFICANDO COMENTARIOS EN ANUNCIOS")
print("="*60)

for cuenta, aadvid, item_id, nombre in anuncios:
    archivo = os.path.join(CARPETA_COOKIES, f"{cuenta}.json")
    if os.path.exists(archivo):
        print(f"\n📁 {cuenta} - {nombre}:")
        verificar_comentarios(archivo, aadvid, item_id, nombre)
    else:
        print(f"\n⚠️ No existe archivo para {cuenta}")