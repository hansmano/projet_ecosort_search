# ♻️ Projet de Fin de Module : EcoSort-Search
> **Pipeline de Collecte Libre, Deep Learning Multiclass et Déploiement Docker**

---

## 🎯 Objectif Général
L'objectif de ce projet est de concevoir et de déployer une application Web containerisée d'aide au tri sélectif pour les citoyens. 

L'utilisateur saisit simplement le **nom d'un produit** de consommation courante. L'application interroge en direct la plateforme e-commerce **Jumia** via une méthode de scraping de votre choix, puis propose les résultats correspondants à l'utilisateur. Une fois le produit sélectionné par l'utilisateur, une **Intelligence Artificielle (Deep Learning)** prend le relais pour analyser le produit et lui attribuer sa consigne de tri exacte en colorant l'écran aux couleurs de la poubelle correspondante.

---

## 🏷️ Définition Officielle des Catégories de Tri

Pour garantir la cohérence du modèle et de l'interface, le système devra classifier chaque produit dans l'une des 5 catégories strictes suivantes :

| Catégorie de Tri | Couleur UI | Types d'emballages & Produits cibles | Matières associées (Dataset) |
| :--- | :--- | :--- | :--- |
| **Poubelle JAUNE** | 🟡 Jaune | Tous les emballages ménagers légers : bouteilles de soda/eau, canettes de boisson, boîtes de conserve, briques de lait, flacons de shampooing, cartons de colis. | `plastic`, `metal`, `cardboard` |
| **Poubelle VERTE** | 🟢 Vert | Uniquement les verres d'emballage : bouteilles de jus ou de vin en verre, pots de confiture, bocaux de conserve. *(Vaisselle cassée interdite).* | `glass` |
| **Poubelle BLEUE** | 🔵 Bleu | Tous les papiers graphiques propres : prospectus publicitaires, journaux, magazines, cahiers, livres, enveloppes. | `paper` |
| **Bac Électronique (D3E)** | 🎛️ Gris | Tout produit fonctionnant avec des piles, une batterie ou une prise électrique : smartphones, écouteurs, chargeurs, mixeurs, montres. | *À cartographier par classe dédiée ou mots-clés* |
| **Poubelle MARRON / NOIRE** | ⚫ Marron | Déchets résiduels non recyclables : restes alimentaires, emballages plastiques souples (sachets, films), produits d'hygiène, objets multicouches. | `trash` |

---

## 🏗️ Architecture et Jalons Techniques

Le projet simule le flux de travail d'une équipe d'ingénieurs IA en entreprise et se divise en deux jalons principaux :

### Jalon 1 : Entraînement de l'IA (Recherche & Labo)
Pour être capable de comprendre la matière d'un emballage, le modèle a besoin d'apprendre sur une base de données stable.
* **Données d'entraînement :** Vous devez utiliser le dataset de référence <a href='https://www.kaggle.com/code/muhammedabdulazeem/garbage-classification'>Garbage Classification</a> disponible sur **Kaggle** (regroupant les classes fondamentales : *glass, paper, cardboard, plastic, metal, trash*).
* **La mission IA :** Développer un réseau de neurones convolutif (**CNN custom**) ou exploiter du **Transfer Learning** (ex: `MobileNetV2` ou `ResNet` via Keras/TensorFlow) pour réaliser une classification multi-classes alignée sur les catégories officielles.
* **Livrable :** Un script d'entraînement reproductible et le fichier du modèle sauvegardé (ex: `modele_eco_sort.h5`).

### Jalon 2 : Collecte Libre & Déploiement (Production)
* **Scraping autonome :** L'équipe doit concevoir sa propre solution de scraping (ex: `BeautifulSoup`, `Requests`, `Selenuim`, etc.) pour interroger le moteur de recherche de Jumia à partir du mot-clé saisi par l'utilisateur et en extraire une liste de 3 à 5 choix pertinents.
* **Interface & Containerisation :** L'application finale sera une application web sous **Streamlit** ou du web classique avec **flask/fastapi/django** au choix. Elle devra charger le modèle entraîné au Jalon 1 et exécuter le script de scraping à la volée. L'ensemble du projet doit être packagé dans un **`Dockerfile`**.

---

## 👥 Collaboration sur Git et Rôles dans l'Équipe

1. Le projet est à réaliser par groupes de **3 étudiants**. Pour garantir une répartition équitable du travail, le dépôt GitHub devra obligatoirement afficher un historique de commits fluide réparti sur trois branches distinctes.
2. **Zéro push direct sur la branche `main` :** La branche principale doit rester propre et stable. Tout ajout de code doit faire l'objet d'une **Pull Request (PR)** sur GitHub, relue, commentée et validée par au moins un autre membre de l'équipe.
3. **Hygiène du dépôt (.gitignore) :** Le dataset de Kaggle (plusieurs Mo/Go) ainsi que vos environnements virtuels Python (`.venv/`, `__pycache__/`) ne doivent **jamais** être poussés sur GitHub. Un fichier `.gitignore` correct est exigé dès le premier jour.
4. **Le livrable Docker :** L'enseignant doit pouvoir évaluer le projet en clonant le dépôt et en exécutant uniquement les deux commandes suivantes dans son terminal :
   ```bash
   docker build -t ecosort .
   docker run -p 8501:8501 ecosort
   ```
    ou 
    ```bash
    docker-compose up -d --build
    ```
5. La contribution de chaque étudiant dans le groupe sera appréciée, il peut donc avoir dans un groupe des notes différentes par étudiant.
6. La date butoir est fixée au 25/07/2026 à 23h59 59 secondes. 
   - Des points de bonus seront accordés aux groupes ayant envoyés leur travail avant la date butoir à raison d'un point (0.5) par jour avec un un nombre de point maximum capé à 5.
   - Si un etudiant a au total plus de 20, les points additionnel seront rajoutés à sa note de participation.
   - 2 points par jour de penalité seront appliqués aux groupes qui rendront leurs travail après la date butoir.

---

## Notes d'equipe - Execution et interface

### Branches de travail

- `feature/jalon1-model-ia` : dataset et entrainement du modele IA.
- `feature/jalon2-scraping` : scraper Jumia.
- `feature/webapp-docker` : interface Flask, mode demo, page A propos et Docker.

### Interface Flask

La partie web est implementee avec Flask. Elle contient :

- une page de recherche produit ;
- une page de resultats ;
- une page de prediction ;
- une page A propos expliquant les 5 categories de tri ;
- un mode demo avec produits pre-remplis ;
- un historique recent stocke uniquement dans la session du navigateur ;
- plusieurs images d'arriere-plan dans `static/images/`.

### Images de l'interface

Les images utilisees par l'interface sont stockees dans :

```text
static/images/
```

Elles sont incluses dans le depot Git. Les autres membres les verront apres :

```bash
git pull
```

ou apres recuperation de la branche :

```bash
git fetch origin
git checkout feature/webapp-docker
git pull origin feature/webapp-docker
```

Dans Docker, elles sont copiees avec :

```dockerfile
COPY static/ ./static/
```

Il faut donc reconstruire l'image Docker apres une modification du CSS ou des images.

### Execution avec Docker

Depuis la racine du projet :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Puis ouvrir :

```text
http://localhost:8501
```

### Execution avec Docker Compose

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
