"""
Jalon 2 — Scraping Jumia.

Interroge le moteur de recherche de Jumia à partir d'un mot-clé et renvoie
une liste de 3 à 5 produits pertinents (titre, prix, URL image, URL produit).

Méthode : requests + BeautifulSoup (parsing HTML du rendu serveur de Jumia).
Le domaine est configurable (Côte d'Ivoire par défaut) car la structure des
pages est identique d'un pays Jumia à l'autre.
"""
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.jumia.ci"
SEARCH_URL = BASE_URL + "/catalog/?q={query}"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def search_products(query, max_results=5, timeout=15):
    """Retourne une liste de dicts : {title, price, image, url}."""
    url = SEARCH_URL.format(query=requests.utils.quote(query))
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

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
    q = sys.argv[1] if len(sys.argv) > 1 else "bouteille eau"
    for i, p in enumerate(search_products(q), 1):
        print(f"{i}. {p['title']} | {p['price']} | {p['image'][:60]}")
