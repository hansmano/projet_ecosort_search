"""
Configuration centrale du projet EcoSort-Search.
Définit : classes du modèle, mapping vers les 5 poubelles officielles,
couleurs UI et mots-clés de détection des D3E (déchets électroniques).
"""

# --- Classes apprises par le modèle (ordre = ordre alphabétique des dossiers) ---
# Cet ordre doit correspondre à celui produit par image_dataset_from_directory.
CLASS_NAMES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

IMG_SIZE = (224, 224)  # taille d'entrée MobileNetV2

# --- Les 5 poubelles officielles ---
# key -> (libellé, couleur hex, couleur de texte lisible)
BINS = {
    "JAUNE":  {"label": "Poubelle JAUNE",         "color": "#F4C20D", "text": "#1a1a1a",
               "desc": "Emballages ménagers légers (plastique, métal, carton)"},
    "VERTE":  {"label": "Poubelle VERTE",          "color": "#2E9E4F", "text": "#ffffff",
               "desc": "Verre d'emballage uniquement"},
    "BLEUE":  {"label": "Poubelle BLEUE",          "color": "#2465C4", "text": "#ffffff",
               "desc": "Papiers graphiques propres"},
    "GRIS":   {"label": "Bac Électronique (D3E)",  "color": "#6B7280", "text": "#ffffff",
               "desc": "Produits électriques / à batterie"},
    "MARRON": {"label": "Poubelle MARRON / NOIRE", "color": "#5B3A1E", "text": "#ffffff",
               "desc": "Déchets résiduels non recyclables"},
}

# --- Mapping classe du modèle -> poubelle ---
CLASS_TO_BIN = {
    "plastic":   "JAUNE",
    "metal":     "JAUNE",
    "cardboard": "JAUNE",
    "glass":     "VERTE",
    "paper":     "BLEUE",
    "trash":     "MARRON",
}

# --- Détection D3E par mots-clés dans le nom du produit ---
# Si l'un de ces mots apparaît dans le titre Jumia, on force la poubelle GRIS
# (le dataset Kaggle ne contient pas de classe électronique).
D3E_KEYWORDS = [
    "smartphone", "telephone", "téléphone", "phone", "iphone", "samsung", "tecno",
    "ecouteur", "écouteur", "earphone", "earbud", "airpod", "casque", "headphone",
    "chargeur", "charger", "cable usb", "câble", "adaptateur", "powerbank", "power bank",
    "batterie", "battery", "pile", "montre connect", "smartwatch", "watch",
    "mixeur", "blender", "robot cuisine", "ordinateur", "laptop", "pc portable", "tablette",
    "tablet", "television", "télévision", "tv led", "clavier", "souris", "manette",
    "console", "enceinte", "speaker bluetooth", "ampli", "ventilateur", "rasoir electrique",
    "seche cheveux", "sèche-cheveux", "fer a repasser", "camera", "caméra", "webcam",
    "routeur", "modem", "disque dur", "cle usb", "clé usb", "ssd", "carte memoire",
]

MODEL_PATH = "models/modele_eco_sort.h5"
