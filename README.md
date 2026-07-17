# EcoSort Search

Application web Flask d'aide au tri selectif.

L'utilisateur recherche un produit, choisit un resultat Jumia, puis l'application affiche la consigne de tri adaptee avec la couleur de la poubelle correspondante.

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

## Structure utile

```text
src/
  app.py          # Application Flask
  scraper.py      # Recherche Jumia
  predict.py      # Prediction IA
  config.py       # Categories, couleurs et mapping

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
