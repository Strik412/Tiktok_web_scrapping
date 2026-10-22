
import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


# Configuración
BASE_URL = "https://www.tiktok.com"
SCRIPT_IDS = (
    "__UNIVERSAL_DATA_FOR_REHYDRATION__",
    "SIGI_STATE",
)

POST_PATTERN = re.compile(
    r"^/@([A-Za-z0-9._]+)/(video|photo)/(\d+)/?$"
)

POST_FIELDS = [
    "id", "tipo", "url", "descripcion",
    "fecha_publicacion_utc", "visualizaciones",
    "likes", "comentarios", "compartidos",
    "guardados", "duracion_segundos",
    "hashtags", "musica", "portada"
]


def leer_json(soup):
    """Busca datos JSON insertados en el HTML."""
    resultado = {}

    for script_id in SCRIPT_IDS:
        elemento = soup.find("script", id=script_id)

        if elemento:
            try:
                contenido = elemento.string or elemento.get_text()
                resultado[script_id] = json.loads(contenido)
            except (ValueError, TypeError):
                pass

    return resultado


def leer_meta(soup, nombre):
    """Obtiene metadatos públicos del HTML."""
    etiqueta = (
        soup.find("meta", attrs={"property": nombre})
        or soup.find("meta", attrs={"name": nombre})
    )

    return etiqueta.get("content", "") if etiqueta else ""


def obtener_perfil(soup, username):
    """Extrae información básica y estadísticas del perfil."""
    scripts = leer_json(soup)

    data = scripts.get(
        "__UNIVERSAL_DATA_FOR_REHYDRATION__", {}
    )

    scope = data.get("__DEFAULT_SCOPE__", {})
    detalle = scope.get("webapp.user-detail", {})
    info = detalle.get("userInfo", {})

    usuario = info.get("user", {}) or {}
    stats = info.get("stats", {}) or {}

    # Estructura antigua utilizada como alternativa.
    if not usuario:
        legacy = scripts.get("SIGI_STATE", {})
        modulo = legacy.get("UserModule", {})
        usuarios = modulo.get("users", {})

        if isinstance(usuarios, dict):
            for clave, item in usuarios.items():
                if (
                    isinstance(item, dict)
                    and item.get("uniqueId", clave).lower()
                    == username.lower()
                ):
                    usuario = item
                    stats = modulo.get("stats", {}).get(clave, {})
                    break

    return {
        "username": usuario.get("uniqueId", username),
        "nombre": usuario.get(
            "nickname", leer_meta(soup, "og:title")
        ),
        "biografia": usuario.get(
            "signature", leer_meta(soup, "og:description")
        ),
        "avatar": usuario.get(
            "avatarLarger", leer_meta(soup, "og:image")
        ),
        "verificado": usuario.get("verified"),
        "privado": usuario.get("privateAccount"),
        "seguidores": stats.get("followerCount"),
        "siguiendo": stats.get("followingCount"),
        "likes": stats.get("heartCount"),
        "videos": stats.get("videoCount"),
        "url": f"{BASE_URL}/@{username}"
    }


def obtener_enlaces(soup, username):
    """Busca enlaces de videos y publicaciones del perfil."""
    enlaces = set()

    for etiqueta in soup.select("a[href]"):
        href = etiqueta.get("href", "")

        if href.startswith("/"):
            href = BASE_URL + href

        partes = urlsplit(href)

        if partes.hostname not in (
            "www.tiktok.com", "tiktok.com"
        ):
            continue

        coincidencia = POST_PATTERN.fullmatch(partes.path)

        if not coincidencia:
            continue

        autor, tipo, identificador = coincidencia.groups()

        if autor.lower() != username.lower():
            continue

        enlaces.add(
            f"{BASE_URL}/@{autor}/{tipo}/{identificador}"
        )

    return enlaces


def esperar_pagina(driver):
    """Espera a que el navegador cargue el documento."""
    WebDriverWait(driver, 25).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )


def recopilar_enlaces(driver, username, scrolls):
    """Carga el perfil y recopila enlaces visibles."""
    url = f"{BASE_URL}/@{username}"

    driver.get(url)
    esperar_pagina(driver)
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    perfil = obtener_perfil(soup, username)
    enlaces = obtener_enlaces(soup, username)

    for _ in range(scrolls):
        driver.execute_script(
            "window.scrollBy(0, 900)"
        )
        time.sleep(2)

        sopa_actual = BeautifulSoup(
            driver.page_source, "html.parser"
        )

        enlaces.update(
            obtener_enlaces(sopa_actual, username)
        )

    return perfil, sorted(enlaces)


def encontrar_item(soup, post_id):
    """Busca metadatos de una publicación en JSON."""
    scripts = leer_json(soup)

    data = scripts.get(
        "__UNIVERSAL_DATA_FOR_REHYDRATION__", {}
    )

    scope = data.get("__DEFAULT_SCOPE__", {})
    detalle = scope.get("webapp.video-detail", {})

    item = detalle.get("itemInfo", {}).get(
        "itemStruct", {}
    )

    if (
        isinstance(item, dict)
        and str(item.get("id")) == post_id
    ):
        return item

    legacy = scripts.get("SIGI_STATE", {})
    modulo = legacy.get("ItemModule", {})

    if isinstance(modulo, dict):
        encontrado = modulo.get(post_id, {})
        if isinstance(encontrado, dict):
            return encontrado

    return {}


def fecha_utc(timestamp):
    """Convierte una fecha Unix a formato legible."""
    try:
        return datetime.fromtimestamp(
            int(timestamp), tz=timezone.utc
        ).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def extraer_post(driver, url):
    """Visita una publicación y obtiene sus datos."""
    driver.get(url)
    esperar_pagina(driver)
    time.sleep(2)

    soup = BeautifulSoup(
        driver.page_source, "html.parser"
    )

    post_id = urlsplit(url).path.rstrip("/").split("/")[-1]
    item = encontrar_item(soup, post_id)

    stats = item.get("stats", {}) or {}
    video = item.get("video", {}) or {}
    musica = item.get("music", {}) or {}

    hashtags = []

    for tag in item.get("textExtra", []) or []:
        nombre = tag.get("hashtagName")
        if nombre:
            hashtags.append(nombre)

    descripcion = item.get("desc")

    if descripcion is None:
        descripcion = leer_meta(soup, "og:description")

    if not hashtags and descripcion:
        hashtags = re.findall(
            r"(?<!\w)#([\w.]+)", descripcion
        )

    timestamp = item.get("createTime")

    tipo = urlsplit(url).path.split("/")[-2]

    return {
        "id": post_id,
        "tipo": tipo,
        "url": url,
        "descripcion": descripcion or "",
        "fecha_publicacion_utc": fecha_utc(timestamp),
        "visualizaciones": stats.get("playCount"),
        "likes": stats.get("diggCount"),
        "comentarios": stats.get("commentCount"),
        "compartidos": stats.get("shareCount"),
        "guardados": stats.get("collectCount"),
        "duracion_segundos": video.get("duration"),
        "hashtags": ", ".join(dict.fromkeys(hashtags)),
        "musica": musica.get("title"),
        "portada": video.get("cover")
    }


def guardar_csv(ruta, registros, campos):
    """Guarda una lista de diccionarios en formato CSV."""
    with open(
        ruta, "w", newline="", encoding="utf-8-sig"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=campos,
            extrasaction="ignore"
        )

        escritor.writeheader()
        escritor.writerows(registros)


def guardar_resultados(username, perfil, posts):
    """Genera archivos JSON y CSV."""
    carpeta = Path("resultados") / username
    carpeta.mkdir(parents=True, exist_ok=True)

    with open(
        carpeta / "perfil_completo.json",
        "w", encoding="utf-8"
    ) as archivo:
        json.dump(
            perfil, archivo,
            indent=2, ensure_ascii=False
        )

    with open(
        carpeta / "ultimos_10_posts.json",
        "w", encoding="utf-8"
    ) as archivo:
        json.dump(
            posts, archivo,
            indent=2, ensure_ascii=False
        )

    guardar_csv(
        carpeta / "perfil.csv",
        [perfil],
        list(perfil.keys())
    )

    guardar_csv(
        carpeta / "ultimos_10_posts.csv",
        posts,
        POST_FIELDS
    )

    print(f"\nArchivos guardados en: {carpeta.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Extraer perfil y publicaciones de TikTok"
    )

    parser.add_argument(
        "--username",
        help="Nombre de usuario de TikTok"
    )

    parser.add_argument(
        "--posts", type=int, default=10
    )

    parser.add_argument(
        "--scrolls", type=int, default=6
    )

    parser.add_argument(
        "--candidatos", type=int, default=25
    )

    args = parser.parse_args()

    username = (
        args.username or input("Username de TikTok: ")
    ).strip().lstrip("@")

    if not re.fullmatch(r"[A-Za-z0-9._]{1,24}", username):
        parser.error("Username inválido")

    if args.posts < 1 or args.scrolls < 0 or args.candidatos < 1:
        parser.error("Parámetros numéricos inválidos")

    opciones = webdriver.ChromeOptions()
    opciones.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=opciones)

    posts = []

    try:
        print(f"\nConsultando perfil: @{username}")

        perfil, enlaces = recopilar_enlaces(
            driver, username, args.scrolls
        )

        print(f"Enlaces encontrados: {len(enlaces)}")

        # Los enlaces pueden estar desordenados o fijados.
        # Se inspeccionan candidatos para conocer sus fechas.
        enlaces = enlaces[:args.candidatos]

        for numero, enlace in enumerate(enlaces, start=1):
            print(
                f"Analizando publicación "
                f"{numero}/{len(enlaces)}"
            )

            try:
                post = extraer_post(driver, enlace)
                posts.append(post)

            except Exception as error:
                print(f"No se pudo analizar: {error}")

        # Ordenar únicamente por fechas verificadas.
        posts_con_fecha = [
            p for p in posts
            if p["fecha_publicacion_utc"]
        ]

        posts_sin_fecha = [
            p for p in posts
            if not p["fecha_publicacion_utc"]
        ]

        posts_con_fecha.sort(
            key=lambda p: p["fecha_publicacion_utc"],
            reverse=True
        )

        if posts_sin_fecha:
            print(
                "Advertencia: algunas publicaciones "
                "no tienen fecha verificable."
            )

        seleccionados = (
            posts_con_fecha + posts_sin_fecha
        )[:args.posts]

        guardar_resultados(
            username, perfil, seleccionados
        )

        print(f"Publicaciones guardadas: {len(seleccionados)}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
