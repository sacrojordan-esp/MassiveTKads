import json
from datetime import datetime
import os  # ← Agrega esto al inicio

def verificar_expiracion_cookies(archivo_cookies):
    """
    Lee el archivo de cookies y muestra cuándo expira cada una.
    """
    try:
        with open(archivo_cookies, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encuentra el archivo: {archivo_cookies}")
        return
    
    print("\n📅 FECHAS DE EXPIRACIÓN DE COOKIES:")
    print("-" * 60)
    
    cookies_importantes = ['sessionid', 'sessionid_ads', 'sid_tt', 'sid_tt_ads', 'csrftoken', 'msToken']
    
    for cookie in cookies:
        if cookie.get('name') in cookies_importantes:
            nombre = cookie['name']
            expiracion = cookie.get('expirationDate')
            
            if expiracion:
                fecha = datetime.fromtimestamp(expiracion)
                hoy = datetime.now()
                dias_restantes = (fecha - hoy).days
                
                if dias_restantes > 7:
                    estado = "✅ VÁLIDA"
                elif dias_restantes > 3:
                    estado = "⚠️ PRONTO A EXPIRAR"
                elif dias_restantes > 0:
                    estado = "🔴 EXPIRA PRONTO"
                else:
                    estado = "❌ EXPIRADA"
                
                print(f"{nombre:15} | {fecha.strftime('%Y-%m-%d')} | {dias_restantes:3} días | {estado}")

# ============================================================================
# USO - CORREGIDO CON RUTAS CORRECTAS
# ============================================================================
if __name__ == "__main__":
    # Mostrar la carpeta actual para debug
    print(f"📂 Carpeta actual: {os.getcwd()}")
    print(f"📂 Archivos en carpeta: {os.listdir('.')}")
    
    # Verificar la cookie principal (si existe en la raíz)
    if os.path.exists("cookies_tiktok.json"):
        verificar_expiracion_cookies("cookies_tiktok.json")
    else:
        print("\n⚠️ No hay cookies_tiktok.json en la raíz")
    
    # Verificar cookies en la carpeta cuentas/
    if os.path.exists("cuentas"):
        print("\n📁 VERIFICANDO COOKIES EN CARPETA 'cuentas/':")
        archivos = os.listdir("cuentas")
        
        if not archivos:
            print("   📂 La carpeta 'cuentas' está vacía")
        else:
            for archivo in archivos:
                if archivo.endswith('.json'):
                    ruta_completa = os.path.join("cuentas", archivo)
                    print(f"\n🔍 {archivo.replace('.json', '')}:")
                    verificar_expiracion_cookies(ruta_completa)
    else:
        print("\n📁 No existe la carpeta 'cuentas'")