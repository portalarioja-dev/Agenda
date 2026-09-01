"""
Extrae los eventos "Destacados" de https://agenda.larioja.com/
y genera un archivo JSON con: titulo, categoria, enlace y fuente.

Uso:
    python extraer_destacados.py [ruta_html_opcional] [num_eventos]

Si no se pasa una ruta, descarga la página en vivo.
"""
import sys
import json
import re
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None

from bs4 import BeautifulSoup

URL_BASE = "https://agenda.larioja.com"
URL_AGENDA = "https://agenda.larioja.com/"
FUENTE = "larioja.com"


def obtener_html(ruta_local=None):
    if ruta_local:
        with open(ruta_local, "r", encoding="utf-8") as f:
            return f.read()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortalLaRiojaBot/1.0)"}
    resp = requests.get(URL_AGENDA, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def extraer_destacados(html, max_eventos=5):
    soup = BeautifulSoup(html, "lxml")

    # Localizamos el título "Destacados" (hay varios h3 con la misma clase,
    # así que filtramos por el texto exacto)
    titulo_destacados = None
    for h3 in soup.find_all("h3", class_="voc-agenda-destacados"):
        if h3.get_text(strip=True).lower() == "destacados":
            titulo_destacados = h3
            break

    if titulo_destacados is None:
        raise ValueError("No se encontró la sección 'Destacados' en la página")

    seccion = titulo_destacados.find_parent("section")
    if seccion is None:
        raise ValueError("No se pudo determinar el contenedor de 'Destacados'")

    eventos = []
    for article in seccion.find_all("article"):
        h2 = article.find("h2", class_="voc-agenda-titulo")
        if not h2:
            continue
        enlace_tag = h2.find("a")
        if not enlace_tag or not enlace_tag.get("href"):
            continue

        titulo = enlace_tag.get_text(strip=True)
        href = enlace_tag["href"]
        enlace = href if href.startswith("http") else URL_BASE + href

        categoria_tag = article.find("div", class_="voc-agenda-antetitulo")
        categoria = categoria_tag.get_text(strip=True) if categoria_tag else ""

        eventos.append({
            "titulo": titulo,
            "categoria": categoria,
            "enlace": enlace,
            "fuente": FUENTE,
        })

        if len(eventos) >= max_eventos:
            break

    return eventos


def main():
    ruta_local = sys.argv[1] if len(sys.argv) > 1 else None
    max_eventos = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    html = obtener_html(ruta_local)
    eventos = extraer_destacados(html, max_eventos=max_eventos)

    salida = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "fuente": FUENTE,
        "eventos": eventos,
    }

    with open("destacados.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Se han extraído {len(eventos)} eventos destacados:")
    for e in eventos:
        print(f" - [{e['categoria']}] {e['titulo']} -> {e['enlace']}")


if __name__ == "__main__":
    main()
