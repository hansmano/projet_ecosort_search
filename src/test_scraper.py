"""
test_scraper.py
================
Tests unitaires du module jumia_scraper.py — ne nécessitent AUCUNE connexion
internet : le HTML est simulé localement pour vérifier que le parsing (et le
fallback) fonctionnent correctement.

Lancer avec :
    python -m unittest test_scraper.py -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

import jumia_scraper as js

# Extrait HTML simulé, reproduisant la structure standard d'une carte produit
# Jumia (article.prd > a.core > ... ) telle qu'observée sur jumia.ci.
SAMPLE_HTML = """
<div class="row -gs0 -mhpi -pvs js-catalog-listing">
  <article class="prd _fb col c-prd">
    <a class="core" href="/faux-smartphone-test-12345.html" title="Faux Smartphone Test 128Go">
      <div class="img-c">
        <img class="img" data-src="https://ci.jumia.is/unsafe/fit-in/300x300/product/00/000000/1.jpg" src="placeholder.jpg" />
      </div>
      <div class="info">
        <h3 class="name">Faux Smartphone Test 128Go</h3>
        <div class="prc">19,900 FCFA</div>
        <div class="old">29,900 FCFA</div>
        <div class="rev">4.2 out of 5 (321)</div>
      </div>
    </a>
  </article>
  <article class="prd _fb col c-prd">
    <a class="core" href="/faux-mixeur-sans-nom.html">
      <div class="info">
        <h3 class="name"></h3>
      </div>
    </a>
  </article>
</div>
"""


class TestParseProductCard(unittest.TestCase):
    def setUp(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        self.cards = soup.select(js.SELECTOR_CARD)

    def test_finds_two_cards(self):
        self.assertEqual(len(self.cards), 2)

    def test_parses_complete_card_correctly(self):
        produit = js._parse_product_card(self.cards[0])
        self.assertIsNotNone(produit)
        self.assertEqual(produit.nom, "Faux Smartphone Test 128Go")
        self.assertEqual(produit.prix, "19,900 FCFA")
        self.assertEqual(produit.prix_barre, "29,900 FCFA")
        self.assertTrue(produit.lien.startswith(js.BASE_URL))
        self.assertIn("1.jpg", produit.image_url)
        self.assertIn("4.2", produit.note)

    def test_incomplete_card_returns_none_without_crashing(self):
        # La 2e carte n'a pas de nom exploitable -> doit être ignorée proprement,
        # pas lever d'exception.
        produit = js._parse_product_card(self.cards[1])
        self.assertIsNone(produit)


class TestFallback(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.fallback_path = Path(self.tmpdir.name) / "jumia_fallback.json"
        data = {
            "_comment": "ceci ne doit jamais être traité comme une liste de produits",
            "telephone": [
                {"nom": "Produit Fallback Téléphone", "prix": "10,000 FCFA",
                 "prix_barre": None, "image_url": None,
                 "lien": "https://www.jumia.ci/exemple.html", "note": None}
            ],
            "_default": [
                {"nom": "Produit Fallback Défaut", "prix": "5,000 FCFA",
                 "prix_barre": None, "image_url": None,
                 "lien": "https://www.jumia.ci/exemple2.html", "note": None}
            ],
        }
        self.fallback_path.write_text(json.dumps(data), encoding="utf-8")
        self._original_path = js.FALLBACK_FILE
        js.FALLBACK_FILE = self.fallback_path

    def tearDown(self):
        js.FALLBACK_FILE = self._original_path
        self.tmpdir.cleanup()

    def test_matches_keyword(self):
        resultats = js._load_fallback("un telephone pas cher", max_results=5)
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].nom, "Produit Fallback Téléphone")

    def test_falls_back_to_default_when_no_keyword_match(self):
        resultats = js._load_fallback("mot-cle-inconnu-xyz", max_results=5)
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].nom, "Produit Fallback Défaut")

    def test_ignores_comment_key_safely(self):
        # Ne doit jamais planter à cause de la clé "_comment"
        resultats = js._load_fallback("_comment", max_results=5)
        self.assertIsInstance(resultats, list)


if __name__ == "__main__":
    unittest.main()
