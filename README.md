# ♻️ EcoSort-Search

Application web d'aide au tri sélectif. L'utilisateur saisit le nom d'un produit,
l'app interroge **Jumia** en direct, puis une IA (Deep Learning) analyse le produit
choisi et affiche la **consigne de tri** en colorant l'écran aux couleurs de la
poubelle correspondante.

## 🗂️ Les 5 poubelles

| Poubelle | Couleur | Matières / Produits |
| :-- | :-- | :-- |
| **JAUNE** | 🟡 | Emballages légers : `plastic`, `metal`, `cardboard` |
| **VERTE** | 🟢 | Verre d'emballage : `glass` |
| **BLEUE** | 🔵 | Papiers graphiques : `paper` |
| **D3E (Gris)** | ⚫ | Électronique / batterie (détecté par mots-clés du titre) |
| **MARRON** | 🟤 | Déchets résiduels : `trash` |

## 🚀 Lancement (Docker)

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

ou :

```bash
docker-compose up -d --build
```

Puis ouvrir **http://localhost:8501**.

## 🧠 Modèle (Jalon 1)

- **Architecture :** Transfer Learning **MobileNetV2** (base ImageNet gelée) +
  tête de classification, sur le dataset **Garbage Classification / TrashNet**
  (6 classes : `cardboard, glass, metal, paper, plastic, trash`).
- **Livrable :** `models/modele_eco_sort.h5` (+ `models/labels.json` = ordre des classes).
- **Résultat actuel :** ~83-87% d'accuracy en validation après 12 epochs (base
  MobileNetV2 gelée, entraînement CPU sur le dataset Kaggle
  `asdasdasasdas/garbage-classification`, ~2500 images / 6 classes).

### Réentraîner le modèle

1. Télécharger le dataset Kaggle et le placer dans `data/dataset/<classe>/*.jpg` :

   ```bash
   pip install kaggle
   # placer kaggle.json (API token, kaggle.com/settings) dans ~/.kaggle/
   kaggle datasets download -d asdasdasasdas/garbage-classification -p data --unzip
   # le zip s'extrait en "data/Garbage classification/Garbage classification/<classe>/"
   # -> déplacer/renommer en data/dataset/<classe>/
   ```

2. Lancer l'entraînement :

   ```bash
   pip install -r requirements.txt
   python src/train.py --data_dir data/dataset --epochs 12
   ```

## 🕸️ Scraping Jumia (Jalon 2)

`src/scraper.py` interroge le moteur de recherche Jumia (`requests` +
`BeautifulSoup`) et renvoie 3 à 5 produits (titre, prix, image, URL).
Domaine configurable via `BASE_URL` (Côte d'Ivoire par défaut).

## 📁 Structure

```
projet_ml/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
├── models/
│   ├── modele_eco_sort.h5     # modèle entraîné (livrable)
│   └── labels.json            # ordre des classes
└── src/
    ├── config.py              # classes, mapping poubelles, couleurs, mots-clés D3E
    ├── train.py               # Jalon 1 : entraînement MobileNetV2
    ├── scraper.py             # Jalon 2 : scraping Jumia
    ├── predict.py             # inférence image + règle D3E
    └── app.py                 # interface Streamlit
```

## 🌱 Lancement en local (sans Docker)

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## 👥 Git — organisation d'équipe

- 3 branches (`feature/jalon1-model-ia`, `feature/jalon2-scraping`,
  `feature/webapp-docker`), **zéro push direct sur `main`**, merges via Pull
  Request relue et approuvée par au moins un autre membre.
- Le dataset (`data/`) et les environnements virtuels ne sont **jamais** poussés
  (voir `.gitignore`). Le modèle `.h5` est versionné (livrable).
