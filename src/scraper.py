
from __future__ import annotations

import requests

try:
    from . import jumia_scraper
except ImportError:  # exécution directe hors package
    import jumia_scraper


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
    produits = jumia_scraper.scrape_jumia(query, max_results=max_results)
    return [
        {
            "title": p.nom,
            "price": p.prix or "",
            "image": p.image_url or "",
            "url": p.lien or "",
        }
        for p in produits
    ]


def download_image(image_url, timeout=15):
    """Télécharge une image produit et renvoie les bytes (ou None)."""
    if not image_url:
        return None
    try:
        r = requests.get(image_url, headers=jumia_scraper.HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.content
    except requests.RequestException:
        return None


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "bouteille eau"
    for i, p in enumerate(search_products(q), 1):
        print(f"{i}. {p['title']} | {p['price']} | {p['image'][:60]}")
