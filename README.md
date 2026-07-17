# ♻️ EcoSort Search

Application web Flask d'aide au tri sélectif. L'utilisateur recherche un
produit, choisit un résultat Jumia, puis l'application analyse le produit
(via un modèle de Deep Learning) et affiche la consigne de tri adaptée,
avec la couleur de la poubelle correspondante.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Les 5 poubelles](#les-5-poubelles)
- [Structure du projet](#structure-du-projet)
- [Répartition de l'équipe](#répartition-de-léquipe)
- [Prérequis](#prérequis)
- [Lancement](#lancement)
  - [Avec Docker](#avec-docker)
  - [Avec Docker Compose](#avec-docker-compose)
  - [En local sans Docker](#en-local-sans-docker)
- [Mode démo](#mode-démo)
- [Routes de l'application](#routes-de-lapplication)
- [Modèle IA (Jalon 1)](#modèle-ia-jalon-1)
- [Scraping Jumia (Jalon 2)](#scraping-jumia-jalon-2)
- [Configuration](#configuration)
- [Bonnes pratiques Git](#bonnes-pratiques-git)

## Fonctionnalités

- Recherche de produits via Jumia.
- Sélection d'un produit à analyser.
- Prédiction de la catégorie de tri par un modèle de Deep Learning.
- Détection des D3E (déchets électroniques) par mots-clés dans le titre.
- Interface Flask responsive avec hero animé (plusieurs images de fond).
- Page « À propos » expliquant les 5 catégories.
- Mode démo avec produits pré-remplis (fonctionne même sans accès à Jumia).
- Historique récent stocké dans la session du navigateur.
- Lancement via Docker ou Docker Compose.

## Les 5 poubelles

| Poubelle | Couleur | Matières / Produits |
| :-- | :-- | :-- |
| **JAUNE** | 🟡 `#F4C20D` | Emballages légers : `plastic`, `metal`, `cardboard` |
| **VERTE** | 🟢 `#2E9E4F` | Verre d'emballage : `glass` |
| **BLEUE** | 🔵 `#2465C4` | Papiers graphiques : `paper` |
| **D3E (Gris)** | ⚫ `#6B7280` | Électronique / batterie (détecté par mots-clés du titre) |
| **MARRON** | 🟤 `#5B3A1E` | Déchets résiduels : `trash` |

Le mapping classe du modèle → poubelle et la liste des mots-clés D3E sont
définis dans [`src/config.py`](src/config.py).

## Structure du projet

```text
src/
  app.py          # Application Flask (routes, session, historique)
  scraper.py      # Recherche Jumia (requests + BeautifulSoup)
  predict.py      # Prédiction IA + règle D3E
  config.py       # Classes, poubelles, couleurs, mots-clés D3E
  train.py        # Entraînement MobileNetV2 (Jalon 1)

templates/
  base.html
  index.html
  results.html
  prediction.html
  about.html

static/
  css/style.css
  images/
    ecosort-hero.png
    ecosort-hero-ai.png
    ecosort-hero-civic.png

models/
  modele_eco_sort.h5   # modèle entraîné (livrable, versionné)
  labels.json           # ordre des classes

Dockerfile
docker-compose.yml
requirements.txt
```

## Répartition de l'équipe

| Membre | Branche | Responsabilités |
| :-- | :-- | :-- |
| Mano | `feature/jalon1-model-ia` | Dataset Kaggle, entraînement du modèle IA, `models/modele_eco_sort.h5` |
| JOREXE | `feature/jalon2-scraping` | Scraping Jumia, extraction titre/prix/image/lien |
| DROH | `feature/webapp-docker` | Interface Flask, templates HTML/CSS, mode démo, Dockerfile / Docker Compose |

## Prérequis

- Python 3.10 (recommandé — voir [`Dockerfile`](Dockerfile))
- pip
- Docker et Docker Compose (optionnel, pour le lancement conteneurisé)

## Lancement

### Avec Docker

Depuis la racine du projet :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Puis ouvrir : <http://localhost:8501>

### Avec Docker Compose

```bash
docker compose up -d --build
```

Puis ouvrir : <http://localhost:8501>

Pour arrêter :

```bash
docker compose down
```

### En local sans Docker

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src/app.py
```

Puis ouvrir : <http://127.0.0.1:8501>

## Mode démo

Le mode démo permet de présenter l'application même si Jumia ne répond pas.
Il utilise des produits pré-remplis et ne dépend pas du scraping.

URL : <http://localhost:8501/demo>

## Routes de l'application

| Route | Méthode | Description |
| :-- | :-- | :-- |
| `/` | GET | Page d'accueil / recherche |
| `/about` | GET | Page « À propos » des 5 catégories |
| `/demo` | GET | Mode démo (produits pré-remplis) |
| `/search` | GET/POST | Recherche de produits sur Jumia |
| `/predict` | POST | Prédiction de la catégorie de tri pour un produit |
| `/health` | GET | Endpoint de health check (utilisé par Docker) |

## Modèle IA (Jalon 1)

- **Architecture :** Transfer Learning avec **MobileNetV2** (base ImageNet
  gelée, puis tête de classification adaptée au tri).
- **Dataset :** Garbage Classification / TrashNet (Kaggle
  `asdasdasasdas/garbage-classification`, ~2500 images / 6 classes).
- **Classes apprises :** `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.
- **Résultat actuel :** ~83-87 % d'accuracy en validation après 12 epochs
  (entraînement CPU).
- **Fichiers attendus :**
  - `models/modele_eco_sort.h5`
  - `models/labels.json`

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

Le dossier `data/` ne doit **jamais** être poussé sur GitHub (voir `.gitignore`).

## Scraping Jumia (Jalon 2)

Le module [`src/scraper.py`](src/scraper.py) interroge le moteur de
recherche Jumia (`requests` + `BeautifulSoup`) et renvoie jusqu'à 5 produits
contenant :

- `title`
- `price`
- `image`
- `url`

L'interface Flask utilise ces données pour afficher les cartes produits.

## Configuration

- `BASE_URL` (dans `src/scraper.py`) : domaine Jumia interrogé, `https://www.jumia.ci`
  par défaut (Côte d'Ivoire) — à adapter selon le pays cible.
- `D3E_KEYWORDS` (dans `src/config.py`) : liste de mots-clés utilisés pour
  forcer la poubelle D3E quand le titre du produit correspond à un appareil
  électronique (le dataset Kaggle ne contient pas de classe électronique).

## Bonnes pratiques Git

- 3 branches (`feature/jalon1-model-ia`, `feature/jalon2-scraping`,
  `feature/webapp-docker`), **zéro push direct sur `main`**, merges via Pull
  Request relue et approuvée par au moins un autre membre.
- Le dataset (`data/`) et les environnements virtuels ne sont **jamais**
  poussés (voir `.gitignore`). Le modèle `.h5` est versionné (livrable).

Chaque membre travaille sur sa branche, par exemple :

```bash
git checkout feature/webapp-docker
```

Cycle recommandé :

```bash
git status
git add <fichiers>
git commit -m "Message clair"
git push origin feature/webapp-docker
```

Ensuite, ouvrir une Pull Request vers `main`.
