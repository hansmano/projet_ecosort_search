# EcoSort Search

Application web Flask d'aide au tri selectif.

L'utilisateur recherche un produit, choisit un resultat Jumia, puis l'application affiche la consigne de tri adaptee avec la couleur de la poubelle correspondante.

## Les 5 poubelles

| Poubelle | Couleur | Matieres / Produits |
| :-- | :-- | :-- |
| **JAUNE** | Jaune | Emballages legers : `plastic`, `metal`, `cardboard` |
| **VERTE** | Verte | Verre d'emballage : `glass` |
| **BLEUE** | Bleue | Papiers graphiques : `paper` |
| **D3E (Gris)** | Grise | Electronique / batterie (detecte par mots-cles du titre) |
| **MARRON** | Marron | Dechets residuels : `trash` |

## Fonctionnalites

- Recherche de produits via Jumia.
- Selection d'un produit a analyser.
- Prediction de la categorie de tri.
- Interface Flask responsive.
- Hero anime avec plusieurs images de fond.
- Page A propos expliquant les 5 categories.
- Mode demo avec produits pre-remplis.
- Historique recent stocke dans la session du navigateur.
- Lancement via Docker ou Docker Compose.

## Repartition de l'equipe

- Mano : `feature/jalon1-model-ia`
  - Dataset Kaggle.
  - Entrainement du modele IA.
  - Sauvegarde du modele `models/modele_eco_sort.h5`.

- JOREXE : `feature/jalon2-scraping`
  - Scraping Jumia.
  - Extraction des produits : titre, prix, image, lien.

- DROH : `feature/webapp-docker`
  - Interface Flask.
  - Templates HTML/CSS.
  - Mode demo.
  - Dockerfile et Docker Compose.

## Modele IA (Jalon 1)

- Architecture : Transfer Learning avec MobileNetV2 (base ImageNet gelee, puis tete de classification adaptee au tri).
- Dataset : Garbage Classification / TrashNet (Kaggle `asdasdasasdas/garbage-classification`, ~2500 images / 6 classes).
- Classes apprises : `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.
- Resultat actuel : ~83-87% d'accuracy en validation apres 12 epochs (entrainement CPU).
- Fichiers attendus :
  - `models/modele_eco_sort.h5`
  - `models/labels.json`

### Reentrainer le modele

1. Telecharger le dataset Kaggle et le placer dans `data/dataset/<classe>/*.jpg` :

   ```bash
   pip install kaggle
   # placer kaggle.json (API token, kaggle.com/settings) dans ~/.kaggle/
   kaggle datasets download -d asdasdasasdas/garbage-classification -p data --unzip
   # le zip s'extrait en "data/Garbage classification/Garbage classification/<classe>/"
   # -> deplacer/renommer en data/dataset/<classe>/
   ```

2. Lancer l'entrainement :

   ```bash
   pip install -r requirements.txt
   python src/train.py --data_dir data/dataset --epochs 12
   ```

Le dossier `data/` ne doit pas etre pousse sur GitHub.

## Scraping Jumia

Le module `src/scraper.py` interroge Jumia avec `requests` et `BeautifulSoup`.

Il renvoie une liste de produits contenant :

- `title`
- `price`
- `image`
- `url`

L'interface Flask utilise ces donnees pour afficher les cartes produits.

## Structure utile

```text
src/
  app.py          # Application Flask
  scraper.py      # Recherche Jumia
  predict.py      # Prediction IA
  config.py       # Categories, couleurs et mapping
  train.py        # Entrainement MobileNetV2

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
  modele_eco_sort.h5
  labels.json
```

## Voir les images chez les autres membres

Les images de l'interface sont dans :

```text
static/images/
```

Elles sont versionnees avec Git. Les autres membres les recuperent automatiquement avec :

```bash
git pull
```

ou, s'ils veulent tester directement ta branche :

```bash
git fetch origin
git checkout feature/webapp-docker
git pull origin feature/webapp-docker
```

Dans Docker, elles sont copiees grace a cette ligne du `Dockerfile` :

```dockerfile
COPY static/ ./static/
```

Il faut reconstruire l'image Docker apres une modification d'image ou de CSS.

## Lancer avec Docker

Depuis la racine du projet :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Puis ouvrir :

```text
http://localhost:8501
```

## Lancer avec Docker Compose

```bash
docker compose up -d --build
```

Puis ouvrir :

```text
http://localhost:8501
```

Pour arreter :

```bash
docker compose down
```

## Lancer en local sans Docker

Recommande seulement avec Python 3.10.

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src/app.py
```

Puis ouvrir :

```text
http://127.0.0.1:8501
```

## Mode demo

Le mode demo permet de presenter l'application meme si Jumia ne repond pas.

URL :

```text
http://localhost:8501/demo
```

Il utilise des produits pre-remplis et ne depend pas du scraping.

## Bonnes pratiques Git

- 3 branches (`feature/jalon1-model-ia`, `feature/jalon2-scraping`, `feature/webapp-docker`), zero push direct sur `main`, merges via Pull Request relue et approuvee par au moins un autre membre.
- Le dataset (`data/`) et les environnements virtuels ne sont jamais pousses (voir `.gitignore`). Le modele `.h5` est versionne (livrable).

Chaque membre travaille sur sa branche :

```bash
git checkout feature/webapp-docker
```

Cycle recommande :

```bash
git status
git add <fichiers>
git commit -m "Message clair"
git push origin feature/webapp-docker
```

Ensuite ouvrir une Pull Request vers `main`.
