"""
Jalon 2 — Scraping Jumia.

Interroge le moteur de recherche de Jumia à partir d'un mot-clé et renvoie
une liste de 3 à 5 produits pertinents (titre, prix, URL image, URL produit).

Méthode : requests + BeautifulSoup (parsing HTML du rendu serveur de Jumia).
Le domaine est configurable (Côte d'Ivoire par défaut) car la structure des
pages est identique d'un pays Jumia à l'autre.

Robustesse :
- Retente automatiquement en cas d'erreur réseau (jusqu'à 3 fois, avec backoff).
- Si le scraping en direct échoue malgré les tentatives (site down, structure
  HTML changée, blocage anti-bot...), bascule sur un jeu de données local
  (jumia_fallback.json) pour ne jamais bloquer la démo/l'application.
"""
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.jumia.ci"
SEARCH_URL = BASE_URL + "/catalog/?q={query}"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

FALLBACK_FILE = Path(__file__).parent / "jumia_fallback.json"
MAX_RETRIES = 3
DELAY_BETWEEN_RETRIES = 1.5  # secondes, multiplié par le numéro de tentative


def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def _fetch_html(url, timeout):
    """Récupère le HTML avec plusieurs tentatives (réseau instable / anti-bot)."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Tentative %s/%s échouée pour %s : %s", attempt, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(DELAY_BETWEEN_RETRIES * attempt)
    raise last_error


def _load_fallback(query, max_results):
    """Charge des résultats de secours depuis jumia_fallback.json si le scraping échoue."""
    if not FALLBACK_FILE.exists():
        return []
    try:
        data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.error("jumia_fallback.json est mal formé, impossible de l'utiliser.")
        return []

    query_lc = query.lower()
    matches = []
    for key, products in data.items():
        if key.startswith("_"):
            continue  # ignore les clés techniques comme "_default"
        if key in query_lc:
            matches.extend(products)
    if not matches:
        matches = data.get("_default", [])
    return matches[:max_results]


def save_as_fallback(query, products):
    """
    Enregistre une recherche réussie dans jumia_fallback.json, sous la clé `query`.
    À lancer manuellement (ex: python src/scraper.py "telephone" --save-fallback)
    quand la connexion est bonne, pour préparer un filet de sécurité avant une
    démo/soutenance avec de vraies données (y compris de vraies images).
    """
    data = {}
    if FALLBACK_FILE.exists():
        try:
            data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data[query.lower()] = products
    FALLBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Fallback mis à jour pour '%s' (%s produit(s)) dans %s", query, len(products), FALLBACK_FILE)


def search_products(query, max_results=5, timeout=15, use_fallback_on_error=True):
    """Retourne une liste de dicts : {title, price, image, url}."""
    url = SEARCH_URL.format(query=requests.utils.quote(query))

    try:
        html = _fetch_html(url, timeout)
    except requests.RequestException:
        logger.error("Échec du scraping en direct pour '%s'.", query)
        if use_fallback_on_error:
            fallback = _load_fallback(query, max_results)
            if fallback:
                logger.warning("Bascule sur le fallback local (%s résultat(s)).", len(fallback))
                return fallback
        raise

    soup = BeautifulSoup(html, "html.parser")

    products = []
    # Chaque carte produit Jumia = <article class="prd _fb col c-prd">
    for card in soup.select("article.prd"):
        a = card.select_one("a.core")
        if not a:
            continue

        # Titre
        name_el = card.select_one(".name")
        title = _clean(name_el.get_text()) if name_el else _clean(a.get("data-ga4-item_name"))
        if not title:
            continue

        # Image : Jumia utilise le lazy-load -> data-src
        img_el = card.select_one("img")
        image = ""
        if img_el:
            image = img_el.get("data-src") or img_el.get("src") or ""

        # Prix
        price_el = card.select_one(".prc")
        price = _clean(price_el.get_text()) if price_el else ""

        # Lien produit
        href = a.get("href", "")
        product_url = href if href.startswith("http") else BASE_URL + href

        products.append({
            "title": title,
            "price": price,
            "image": image,
            "url": product_url,
        })
        if len(products) >= max_results:
            break

    if not products and use_fallback_on_error:
        fallback = _load_fallback(query, max_results)
        if fallback:
            logger.warning("Aucun produit extrait en direct, bascule sur le fallback local "
                           "(%s résultat(s)).", len(fallback))
            return fallback

    return products


def download_image(image_url, timeout=15):
    """Télécharge une image produit et renvoie les bytes (ou None)."""
    if not image_url:
        return None
    try:
        r = requests.get(image_url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.content
    except requests.RequestException:
        return None


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    save_flag = "--save-fallback" in args
    args = [a for a in args if a != "--save-fallback"]
    q = args[0] if args else "bouteille eau"

    results = search_products(q, use_fallback_on_error=not save_flag)
    for i, p in enumerate(results, 1):
        print(f"{i}. {p['title']} | {p['price']} | {p['image'][:60]}")

    if save_flag:
        save_as_fallback(q, results)
