"""Extrae datos visibles de un perfil público de TikTok usando Selenium (sin API).

Uso:
    python tiktok_perfil_selenium.py
    python tiktok_perfil_selenium.py --username mi_usuario --scrolls 2
"""
import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


SCRIPT_IDS = ("__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE")


def find_user_info(scripts, username):
    """Busca los datos del perfil solo en scripts JSON, sin llamadas de red extra."""
    for script_id, data in scripts.items():
        if script_id == "__UNIVERSAL_DATA_FOR_REHYDRATION__":
            scope = data.get("__DEFAULT_SCOPE__", {})
            detail = scope.get("webapp.user-detail", {})
            info = detail.get("userInfo", {})
            if isinstance(info, dict) and isinstance(info.get("user"), dict):
                return info.get("user", {}), info.get("stats", {}), info.get("statsV2", {}), script_id
        elif script_id == "SIGI_STATE":
            users = data.get("UserModule", {}).get("users", {})
            stats_map = data.get("UserModule", {}).get("stats", {})
            if isinstance(users, dict):
                matching = next(
                    ((key, user) for key, user in users.items()
                     if isinstance(user, dict)
                     and str(user.get("uniqueId", key)).lower() == username.lower()),
                    None,
                )
                if matching:
                    key, user = matching
                    return user, stats_map.get(key, {}), {}, script_id
    return {}, {}, {}, None


def extract_html(html, username, page_url):
    soup = BeautifulSoup(html, "html.parser")

    def meta(name):
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        return tag.get("content", "").strip() if tag else ""

    scripts = {}
    for script_id in SCRIPT_IDS:
        tag = soup.find("script", id=script_id)
        if tag and tag.string:
            try:
                scripts[script_id] = json.loads(tag.string)
            except json.JSONDecodeError:
                pass

    user, stats, stats_v2, source = find_user_info(scripts, username)
    if not user:
        # Solo metadatos accesibles, no se atribuyen erróneamente a la biografía.
        user = {
            "uniqueId": username,
            "pageTitle": soup.title.get_text(" ", strip=True) if soup.title else "",
            "metaDescription": meta("og:description") or meta("description"),
            "metaTitle": meta("og:title"),
            "avatarMeta": meta("og:image"),
        }
        source = "metadatos HTML (extracción parcial)"

    links = set()
    for tag in soup.select('a[href*="/video/"]'):
        href = tag.get("href", "")
        m = re.search(r"https?://(?:www\.)?tiktok\.com/@[^/\s?#]+/video/(\d+)", href)
        if not m and href.startswith("/@"):
            m = re.search(r"/@[^/\s?#]+/video/(\d+)", href)
            if m:
                links.add("https://www.tiktok.com" + m.group(0))
        elif m:
            links.add(m.group(0))

    page_info = {
        "requested_username": username,
        "requested_url": page_url,
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "page_title": soup.title.get_text(" ", strip=True) if soup.title else "",
        "meta_description": meta("og:description") or meta("description"),
        "meta_image": meta("og:image"),
    }
    return {
        "pagina": page_info,
        "usuario": user,
        "estadisticas": stats,
        "estadisticas_v2": stats_v2,
        "videos_visibles": [{"url": link} for link in sorted(links)],
    }


def flat_rows(prefix, data):
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}"
        if isinstance(value, dict):
            result.update(flat_rows(full_key, value))
        elif isinstance(value, list):
            result[full_key] = json.dumps(value, ensure_ascii=False)
        else:
            result[full_key] = value
    return result


def save_csv(path, rows):
    if not rows:
        return
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def scrape(username, scrolls):
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    url = f"https://www.tiktok.com/@{quote(username)}"
    try:
        driver.get(url)
        WebDriverWait(driver, 25).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Permite que TikTok renderice datos dinámicos; no intenta sortear bloqueos.
        for _ in range(12):
            html = driver.page_source
            if ("__UNIVERSAL_DATA_FOR_REHYDRATION__" in html
                    or 'SIGI_STATE' in html
                    or 'og:title' in html):
                break
            time.sleep(1)
        for _ in range(scrolls):
            driver.execute_script("window.scrollBy(0, 700)")
            time.sleep(2)
        return extract_html(driver.page_source, username, driver.current_url)
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Extrae información visible de perfiles de TikTok")
    parser.add_argument("--username", help="Usuario con o sin @")
    parser.add_argument("--scrolls", type=int, default=0, help="Desplazamientos suaves (0 a 3)")
    args = parser.parse_args()

    username = (args.username or input("Username de TikTok: ")).strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._]{1,24}", username):
        parser.error("Username inválido: utiliza letras, números, puntos o guiones bajos (máx. 24)")
    if not 0 <= args.scrolls <= 3:
        parser.error("--scrolls debe estar entre 0 y 3")

    result = scrape(username, args.scrolls)
    output = Path("resultados") / username
    output.mkdir(parents=True, exist_ok=True)
    (output / "perfil_completo.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    values = {}
    for key in ("pagina", "usuario", "estadisticas", "estadisticas_v2"):
        values.update(flat_rows(key, result[key]))
    save_csv(output / "perfil.csv", [values])
    save_csv(output / "videos_visibles.csv", result["videos_visibles"])

    print("\nFuente:", result["pagina"]["source"])
    for label, value in [
        ("Username", result["usuario"].get("uniqueId")),
        ("Nombre", result["usuario"].get("nickname")),
        ("Biografía", result["usuario"].get("signature")),
        ("Seguidores", result["estadisticas"].get("followerCount")),
        ("Siguiendo", result["estadisticas"].get("followingCount")),
        ("Me gusta", result["estadisticas"].get("heartCount")),
        ("Cantidad de videos", result["estadisticas"].get("videoCount")),
        ("Enlaces de videos visibles", len(result["videos_visibles"])),
    ]:
        print(f"{label}: {value if value is not None else 'No disponible'}")
    print("Archivos guardados en:", output.resolve())
    if result["pagina"]["source"].startswith("metadatos"):
        print("AVISO: TikTok no proporcionó JSON del perfil; los datos son parciales.")


if __name__ == "__main__":
    main()
