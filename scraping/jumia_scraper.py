"""
jumia_scraper.py
=================
Module de scraping du moteur de recherche de Jumia Côte d'Ivoire (jumia.ci)
pour le projet EcoSort-Search — Jalon .

Ce module expose une seule fonction publique à utiliser par l'application web
(Streamlit / Flask) construite par le reste de l'équipe :

    from jumia_scraper import scrape_jumia
    resultats = scrape_jumia("telephone", max_results=5)

Elle renvoie une liste d'objets `Produit` (nom, prix, prix barré, image, lien,
note), prêts à être affichés puis transmis au modèle de deep learning une fois
que l'utilisateur en a choisi un.

Robustesse :
- Retente automatiquement en cas d'erreur réseau (jusqu'à 3 fois).
- Si le scraping en direct échoue complètement (site down, structure HTML
  changée, blocage anti-bot...), bascule automatiquement sur un jeu de
  données local (`jumia_fallback.json`) pour que la démo ne soit jamais
  bloquée par une panne du site distant.
- Chaque carte produit est parsée individuellement : une carte cassée est
  ignorée plutôt que de faire planter tout le scraping.

Si Jumia change son HTML et que le scraping casse, voir la section
"Que faire si le scraping casse" dans README_scraping.md.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jumia_scraper")

# ---------------------------------------------------------------------------
# Configuration — à ajuster ici en un seul endroit si Jumia change son site
# ---------------------------------------------------------------------------

BASE_URL = "https://www.jumia.ci"
SEARCH_URL_TEMPLATE = BASE_URL + "/catalog/?q={query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Sélecteurs CSS de la structure standard des pages Jumia (Afrique).
# S'ils ne fonctionnent plus, inspecte le HTML réel (touche F12 dans le
# navigateur) et remplace uniquement les valeurs ci-dessous.
SELECTOR_CARD = "article.prd"
SELECTOR_LINK = "a.core"
SELECTOR_NAME = "h3.name"
SELECTOR_PRICE = "div.prc"
SELECTOR_OLD_PRICE = "div.old"
SELECTOR_IMAGE = "img.img"
SELECTOR_RATING = "div.rev"

FALLBACK_FILE = Path(__file__).parent / "jumia_fallback.json"

REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
DELAY_BETWEEN_RETRIES = 1.5  # secondes, multiplié par le numéro de tentative


# ---------------------------------------------------------------------------
# Modèle de données
# ---------------------------------------------------------------------------


@dataclass
class Produit:
    """Représente un produit tel qu'affiché dans les résultats de recherche Jumia."""

    nom: str
    prix: Optional[str] = None
    prix_barre: Optional[str] = None
    image_url: Optional[str] = None
    lien: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> dict:
        """Pratique pour l'intégration Streamlit / JSON / API."""
        return asdict(self)


class JumiaScraperError(Exception):
    """Erreur levée quand le scraping en direct échoue (réseau ou structure HTML)."""


# ---------------------------------------------------------------------------
# Fonctions internes
# ---------------------------------------------------------------------------


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _fetch_html(url: str, session: requests.Session) -> str:
    """Récupère le HTML d'une page avec 3 tentatives et un backoff simple."""
    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Tentative %s/%s échouée pour %s : %s", attempt, MAX_RETRIES, url, exc)
            time.sleep(DELAY_BETWEEN_RETRIES * attempt)
    raise JumiaScraperError(f"Impossible de récupérer {url} après {MAX_RETRIES} tentatives : {last_error}")


def _clean_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def _parse_product_card(card) -> Optional[Produit]:
    """Extrait un `Produit` depuis une carte HTML. Renvoie None si illisible."""
    try:
        link_tag = card.select_one(SELECTOR_LINK)
        if link_tag is None:
            return None

        lien = link_tag.get("href", "")
        if lien and lien.startswith("/"):
            lien = BASE_URL + lien

        nom_tag = card.select_one(SELECTOR_NAME)
        nom = _clean_text((nom_tag.get("title") if nom_tag else None) or (nom_tag.get_text() if nom_tag else None))
        if not nom:
            nom = _clean_text(link_tag.get("title") or link_tag.get_text())

        prix_tag = card.select_one(SELECTOR_PRICE)
        prix = _clean_text(prix_tag.get_text()) if prix_tag else None

        prix_barre_tag = card.select_one(SELECTOR_OLD_PRICE)
        prix_barre = _clean_text(prix_barre_tag.get_text()) if prix_barre_tag else None

        img_tag = card.select_one(SELECTOR_IMAGE)
        image_url = None
        if img_tag is not None:
            image_url = img_tag.get("data-src") or img_tag.get("src")

        note_tag = card.select_one(SELECTOR_RATING)
        note = _clean_text(note_tag.get_text()) if note_tag else None

        if not nom or not lien:
            return None

        return Produit(nom=nom, prix=prix, prix_barre=prix_barre, image_url=image_url, lien=lien, note=note)

    except Exception as exc:  # une carte cassée ne doit jamais faire planter tout le scraping
        logger.debug("Carte produit ignorée (erreur de parsing) : %s", exc)
        return None


def save_as_fallback(keyword: str, produits: List[Produit]) -> None:
    """
    Enregistre une recherche réussie dans jumia_fallback.json, sous la clé `keyword`.
    À lancer manuellement (voir CLI plus bas) quand tu as une bonne connexion, pour
    préparer un filet de sécurité AVANT la soutenance/démo, avec de vraies données
    (y compris de vraies image_url), au cas où le scraping en direct échoue ce jour-là.
    """
    data = {}
    if FALLBACK_FILE.exists():
        try:
            data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data[keyword.lower()] = [p.to_dict() for p in produits]
    FALLBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Fallback mis à jour pour '%s' (%s produit(s)) dans %s", keyword, len(produits), FALLBACK_FILE)


def _load_fallback(keyword: str, max_results: int) -> List[Produit]:
    """Charge des résultats de secours depuis jumia_fallback.json si le scraping échoue."""
    if not FALLBACK_FILE.exists():
        return []
    try:
        data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.error("jumia_fallback.json est mal formé, impossible de l'utiliser.")
        return []

    keyword_lc = keyword.lower()
    matches: List[dict] = []
    for cle, produits in data.items():
        if cle.startswith("_"):
            continue  # ignore les clés techniques comme "_comment" ou "_default"
        if cle in keyword_lc:
            matches.extend(produits)

    if not matches:
        matches = data.get("_default", [])

    return [Produit(**p) for p in matches[:max_results]]


# ---------------------------------------------------------------------------
# Fonction publique
# ---------------------------------------------------------------------------


def scrape_jumia(keyword: str, max_results: int = 5, use_fallback_on_error: bool = True) -> List[Produit]:
    """
    Recherche `keyword` sur Jumia CI et renvoie une liste de 3 à `max_results` Produit.

    Args:
        keyword: mot-clé saisi par l'utilisateur dans l'application.
        max_results: nombre maximum de résultats à renvoyer (le sujet demande 3 à 5).
        use_fallback_on_error: si True (par défaut), bascule sur jumia_fallback.json
            en cas d'échec du scraping en direct, pour ne jamais bloquer l'application.

    Raises:
        ValueError: si `keyword` est vide.
        JumiaScraperError: si le scraping échoue ET qu'aucun fallback n'est disponible.
    """
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("Le mot-clé de recherche ne peut pas être vide.")

    url = SEARCH_URL_TEMPLATE.format(query=quote(keyword))
    session = _get_session()

    try:
        html = _fetch_html(url, session)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(SELECTOR_CARD)

        if not cards:
            raise JumiaScraperError(
                f"Aucune carte produit trouvée avec le sélecteur '{SELECTOR_CARD}'. "
                "La structure HTML de Jumia a probablement changé — voir README_scraping.md."
            )

        produits: List[Produit] = []
        for card in cards:
            produit = _parse_product_card(card)
            if produit:
                produits.append(produit)
            if len(produits) >= max_results:
                break

        if not produits:
            raise JumiaScraperError("Cartes produit trouvées mais aucune n'a pu être correctement extraite.")

        logger.info("%s produit(s) récupéré(s) pour '%s'.", len(produits), keyword)
        return produits

    except (JumiaScraperError, requests.RequestException) as exc:
        logger.error("Échec du scraping en direct pour '%s' : %s", keyword, exc)
        if use_fallback_on_error:
            fallback = _load_fallback(keyword, max_results)
            if fallback:
                logger.warning("Bascule sur le fallback local (%s résultat(s)).", len(fallback))
                return fallback
        raise


# ---------------------------------------------------------------------------
# Exécution en ligne de commande, pour tester le module seul :
#   python jumia_scraper.py "telephone"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    save_flag = "--save-fallback" in args
    args = [a for a in args if a != "--save-fallback"]
    query = args[0] if args else "telephone"

    print(f"Recherche Jumia CI pour : '{query}'\n")
    resultats = scrape_jumia(query, use_fallback_on_error=not save_flag)
    for i, produit in enumerate(resultats, start=1):
        print(f"{i}. {produit.nom}")
        print(f"   Prix     : {produit.prix} (avant : {produit.prix_barre})")
        print(f"   Note     : {produit.note}")
        print(f"   Image    : {produit.image_url}")
        print(f"   Lien     : {produit.lien}\n")

    if save_flag:
        save_as_fallback(query, resultats)
