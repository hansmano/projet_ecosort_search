"""
Jalon 2 — Scraping Jumia.

Adaptateur au-dessus de jumia_scraper.py : convertit les objets `Produit`
(nom, prix, image_url, lien) en dicts {title, price, image, url}, format
attendu par app.py et les templates.

Le scraping lui-même (retry, fallback local, parsing HTML) est implémenté
dans jumia_scraper.py — voir ce module pour la robustesse et les tests
(src/test_scraper.py).
"""
from __future__ import annotations

import requests

try:
    from . import jumia_scraper
except ImportError:  # exécution directe hors package
    import jumia_scraper


def search_products(query, max_results=5, use_fallback_on_error=True):
    """Retourne une liste de dicts : {title, price, image, url}."""
    produits = jumia_scraper.scrape_jumia(
        query, max_results=max_results, use_fallback_on_error=use_fallback_on_error
    )
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
