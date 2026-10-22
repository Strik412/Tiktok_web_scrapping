import argparse
import csv
import json
import time
import re
import random
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

POST_FIELDS = [
    "id", "url", "descripcion", "fecha_publicacion_utc",
    "visualizaciones", "likes", "comentarios", "compartidos", "guardados"
]

def guardar_csv(ruta, registros, campos):
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(registros)

def guardar_resultados(username, perfil, posts):
    carpeta = Path("resultados") / username
    carpeta.mkdir(parents=True, exist_ok=True)
    
    (carpeta / "perfil.json").write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")
    (carpeta / "ultimos_posts.json").write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    guardar_csv(carpeta / "perfil.csv", [perfil], list(perfil.keys()))
    guardar_csv(carpeta / "ultimos_posts.csv", posts, POST_FIELDS)
    print(f"\n[OK] ¡ÉXITO! Resultados guardados en: {carpeta.resolve()}")

def extraer_json_tiktok(html):
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")
    if not script_tag: return {}
    try: return json.loads(script_tag.string)
    except: return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--posts", type=int, default=10)
    args = parser.parse_args()
    
    username = args.username.strip().lstrip("@")
    
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    ruta_perfil = Path("Perfil_TikTok").resolve()
    options.add_argument(f"--user-data-dir={ruta_perfil}")

    print("[*] Abriendo navegador...")
    try:
        driver = uc.Chrome(options=options, version_main=155)
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    try:
        url_perfil = f"https://www.tiktok.com/@{username}"
        driver.get(url_perfil)
        
        print("\n" + "="*50)
        print("ACCIÓN MANUAL REQUERIDA EN EL NAVEGADOR:")
        print("1. Si aparece un Captcha, resuélvelo.")
        print("2. HAZ SCROLL HACIA ABAJO en la página hasta que veas las miniaturas de los videos.")
        print("3. Vuelve a esta terminal y presiona ENTER.")
        print("="*50)
        input("Presiona ENTER aquí cuando los videos estén en pantalla... ")
        
        # --- 1. EXTRAER PERFIL ---
        html = driver.page_source
        datos = extraer_json_tiktok(html)
        scope = datos.get("__DEFAULT_SCOPE__", {})
        detalle = scope.get("webapp.user-detail", {})
        user_info = detalle.get("userInfo", {}).get("user", {})
        stats_info = detalle.get("userInfo", {}).get("stats", {})

        perfil = {
            "username": user_info.get("uniqueId", username),
            "nombre": user_info.get("nickname", ""),
            "biografia": user_info.get("signature", ""),
            "seguidores": stats_info.get("followerCount", 0),
            "siguiendo": stats_info.get("followingCount", 0),
            "likes": stats_info.get("heartCount", 0),
            "videos": stats_info.get("videoCount", 0),
            "url": url_perfil
        }
        print(f"\n[DEBUG] Perfil capturado: {perfil.get('nombre')}")

        # --- 2. OBTENER ENLACES (LINKS) ---
        soup = BeautifulSoup(html, "html.parser")
        enlaces = []
        patron = re.compile(rf"/@{username}/video/(\d+)", re.IGNORECASE)
        
        for tag in soup.select("a[href]"):
            href = tag.get("href", "")
            if patron.search(href):
                link_completo = f"https://www.tiktok.com/@{username}/video/{patron.search(href).group(1)}"
                if link_completo not in enlaces:
                    enlaces.append(link_completo)

        if not enlaces:
            print("[ERROR] No se detectaron videos. Asegúrate de hacer scroll hacia abajo antes de presionar ENTER.")
            return

        posts_procesados = []
        enlaces_a_procesar = enlaces[:args.posts]
        
        print("\n[*] Extrayendo estadísticas (Navegación silenciosa anti-403)...")
        
        for i, url_video in enumerate(enlaces_a_procesar, 1):
            print(f"\n -> Procesando video {i}/{len(enlaces_a_procesar)}")
            
            # TRUCO ANTI-403: Navegar mediante JS mantiene el Referrer y simula un clic orgánico
            driver.execute_script(f"window.location.href = '{url_video}';")
            
            # Pausa aleatoria natural
            tiempo_espera = random.uniform(6.5, 9.5)
            print(f"    [Esperando {tiempo_espera:.1f}s...]")
            time.sleep(tiempo_espera)
            
            vid_html = driver.page_source
            
            # Si aparece un 403 o Captcha visual
            if "HTTP ERROR 403" in vid_html or "Se denegó el acceso" in vid_html:
                print("    [!] ERROR 403 DETECTADO. TikTok bloqueó esta petición.")
                print("    [!] Deteniendo el proceso. Por favor, renueva tu IP (Modo Avión) antes de reintentar.")
                break

            vid_datos = extraer_json_tiktok(vid_html)
            
            if not vid_datos:
                print("    [!] ALERTA: TikTok ocultó los datos de este video.")
                print("    [!] Revisa Chrome. Si hay un Captcha o Login, ciérralo o resuélvelo.")
                input("    [!] Presiona ENTER aquí SOLAMENTE cuando estés viendo el video normal... ")
                time.sleep(2) 
                vid_html = driver.page_source
                vid_datos = extraer_json_tiktok(vid_html)

            vid_scope = vid_datos.get("__DEFAULT_SCOPE__", {})
            vid_detalle = vid_scope.get("webapp.video-detail", {})
            item = vid_detalle.get("itemInfo", {}).get("itemStruct", {})
            
            if item:
                stats = item.get("statsV2") or item.get("stats") or {}
                fecha_ts = int(item.get("createTime", 0))
                
                posts_procesados.append({
                    "id": item.get("id"),
                    "url": url_video,
                    "descripcion": item.get("desc", ""),
                    "fecha_publicacion_utc": datetime.fromtimestamp(fecha_ts, tz=timezone.utc).isoformat() if fecha_ts else "",
                    "visualizaciones": stats.get("playCount", 0),
                    "likes": stats.get("diggCount", 0),
                    "comentarios": stats.get("commentCount", 0),
                    "compartidos": stats.get("shareCount", 0),
                    "guardados": stats.get("collectCount", 0)
                })
                print(f"    [OK] Datos capturados. Likes: {stats.get('diggCount', 0)}")
            else:
                print("    [ERROR] No se pudo extraer la info de este video.")

        if posts_procesados:
            guardar_resultados(username, perfil, posts_procesados)
        else:
            print("\n[!] No se guardó nada porque no se pudo procesar ningún video.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

import argparse
import csv
import json
import time
import re
import random
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

POST_FIELDS = [
    "id", "url", "descripcion", "fecha_publicacion_utc",
    "visualizaciones", "likes", "comentarios", "compartidos", "guardados"
]

def guardar_csv(ruta, registros, campos):
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(registros)

def guardar_resultados(username, perfil, posts):
    carpeta = Path("resultados") / username
    carpeta.mkdir(parents=True, exist_ok=True)
    
    (carpeta / "perfil.json").write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")
    (carpeta / "ultimos_posts.json").write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    guardar_csv(carpeta / "perfil.csv", [perfil], list(perfil.keys()))
    guardar_csv(carpeta / "ultimos_posts.csv", posts, POST_FIELDS)
    print(f"\n[OK] ¡ÉXITO! Resultados guardados en: {carpeta.resolve()}")

def extraer_json_tiktok(html):
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")
    if not script_tag: return {}
    try: return json.loads(script_tag.string)
    except: return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--posts", type=int, default=10)
    args = parser.parse_args()
    
    username = args.username.strip().lstrip("@")
    
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    ruta_perfil = Path("Perfil_TikTok").resolve()
    options.add_argument(f"--user-data-dir={ruta_perfil}")

    print("[*] Abriendo navegador...")
    try:
        driver = uc.Chrome(options=options, version_main=155)
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    try:
        url_perfil = f"https://www.tiktok.com/@{username}"
        driver.get(url_perfil)
        
        print("\n" + "="*50)
        print("ACCIÓN MANUAL REQUERIDA EN EL NAVEGADOR:")
        print("1. Si aparece un Captcha, resuélvelo.")
        print("2. HAZ SCROLL HACIA ABAJO en la página hasta que veas las miniaturas de los videos.")
        print("3. Vuelve a esta terminal y presiona ENTER.")
        print("="*50)
        input("Presiona ENTER aquí cuando los videos estén en pantalla... ")
        
        # --- 1. EXTRAER PERFIL ---
        html = driver.page_source
        datos = extraer_json_tiktok(html)
        scope = datos.get("__DEFAULT_SCOPE__", {})
        detalle = scope.get("webapp.user-detail", {})
        user_info = detalle.get("userInfo", {}).get("user", {})
        stats_info = detalle.get("userInfo", {}).get("stats", {})

        perfil = {
            "username": user_info.get("uniqueId", username),
            "nombre": user_info.get("nickname", ""),
            "biografia": user_info.get("signature", ""),
            "seguidores": stats_info.get("followerCount", 0),
            "siguiendo": stats_info.get("followingCount", 0),
            "likes": stats_info.get("heartCount", 0),
            "videos": stats_info.get("videoCount", 0),
            "url": url_perfil
        }
        print(f"\n[DEBUG] Perfil capturado: {perfil.get('nombre')}")

        # --- 2. OBTENER ENLACES (LINKS) ---
        soup = BeautifulSoup(html, "html.parser")
        enlaces = []
        patron = re.compile(rf"/@{username}/video/(\d+)", re.IGNORECASE)
        
        for tag in soup.select("a[href]"):
            href = tag.get("href", "")
            if patron.search(href):
                link_completo = f"https://www.tiktok.com/@{username}/video/{patron.search(href).group(1)}"
                if link_completo not in enlaces:
                    enlaces.append(link_completo)

        if not enlaces:
            print("[ERROR] No se detectaron videos. Asegúrate de hacer scroll hacia abajo antes de presionar ENTER.")
            return

        posts_procesados = []
        enlaces_a_procesar = enlaces[:args.posts]
        
        print("\n[*] Extrayendo estadísticas (Navegación silenciosa anti-403)...")
        
        for i, url_video in enumerate(enlaces_a_procesar, 1):
            print(f"\n -> Procesando video {i}/{len(enlaces_a_procesar)}")
            
            # TRUCO ANTI-403: Navegar mediante JS mantiene el Referrer y simula un clic orgánico
            driver.execute_script(f"window.location.href = '{url_video}';")
            
            # Pausa aleatoria natural
            tiempo_espera = random.uniform(6.5, 9.5)
            print(f"    [Esperando {tiempo_espera:.1f}s...]")
            time.sleep(tiempo_espera)
            
            vid_html = driver.page_source
            
            # Si aparece un 403 o Captcha visual
            if "HTTP ERROR 403" in vid_html or "Se denegó el acceso" in vid_html:
                print("    [!] ERROR 403 DETECTADO. TikTok bloqueó esta petición.")
                print("    [!] Deteniendo el proceso. Por favor, renueva tu IP (Modo Avión) antes de reintentar.")
                break

            vid_datos = extraer_json_tiktok(vid_html)
            
            if not vid_datos:
                print("    [!] ALERTA: TikTok ocultó los datos de este video.")
                print("    [!] Revisa Chrome. Si hay un Captcha o Login, ciérralo o resuélvelo.")
                input("    [!] Presiona ENTER aquí SOLAMENTE cuando estés viendo el video normal... ")
                time.sleep(2) 
                vid_html = driver.page_source
                vid_datos = extraer_json_tiktok(vid_html)

            vid_scope = vid_datos.get("__DEFAULT_SCOPE__", {})
            vid_detalle = vid_scope.get("webapp.video-detail", {})
            item = vid_detalle.get("itemInfo", {}).get("itemStruct", {})
            
            if item:
                stats = item.get("statsV2") or item.get("stats") or {}
                fecha_ts = int(item.get("createTime", 0))
                
                posts_procesados.append({
                    "id": item.get("id"),
                    "url": url_video,
                    "descripcion": item.get("desc", ""),
                    "fecha_publicacion_utc": datetime.fromtimestamp(fecha_ts, tz=timezone.utc).isoformat() if fecha_ts else "",
                    "visualizaciones": stats.get("playCount", 0),
                    "likes": stats.get("diggCount", 0),
                    "comentarios": stats.get("commentCount", 0),
                    "compartidos": stats.get("shareCount", 0),
                    "guardados": stats.get("collectCount", 0)
                })
                print(f"    [OK] Datos capturados. Likes: {stats.get('diggCount', 0)}")
            else:
                print("    [ERROR] No se pudo extraer la info de este video.")

        if posts_procesados:
            guardar_resultados(username, perfil, posts_procesados)
        else:
            print("\n[!] No se guardó nada porque no se pudo procesar ningún video.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()