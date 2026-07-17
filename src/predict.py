"""
Inférence EcoSort-Search : image (+ titre produit) -> poubelle.

Combine :
  1) La prédiction du modèle CNN (matière de l'emballage).
  2) Une règle métier : si le titre du produit contient un mot-clé D3E
     (électronique / batterie), on force la poubelle GRIS, car le dataset
     ne comporte pas de classe électronique.
"""
import io
import json
import os

import numpy as np
from PIL import Image

try:
    from . import config
except ImportError:  # Permet aussi l'execution directe hors package.
    import config

_model = None
_labels = None
_input_size = None


def _load():
    global _model, _labels, _input_size
    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(config.MODEL_PATH)
        # Taille d'entrée lue depuis le modèle (robuste au CNN d'amorçage 128px
        # comme au MobileNetV2 224px).
        shape = _model.input_shape  # (None, H, W, 3)
        _input_size = (shape[1], shape[2]) if shape[1] else config.IMG_SIZE
        labels_path = "models/labels.json"
        if os.path.exists(labels_path):
            with open(labels_path, encoding="utf-8") as f:
                _labels = json.load(f)
        else:
            _labels = config.CLASS_NAMES
    return _model, _labels, _input_size


def is_d3e(product_title):
    t = (product_title or "").lower()
    return any(kw in t for kw in config.D3E_KEYWORDS)


def predict(image_bytes, product_title=""):
    """Retourne un dict : {bin, bin_info, material, confidence, reason}."""
    # Règle D3E prioritaire (basée sur le nom du produit)
    if is_d3e(product_title):
        return {
            "bin": "GRIS",
            "bin_info": config.BINS["GRIS"],
            "material": "électronique (D3E)",
            "confidence": 1.0,
            "reason": "Produit détecté comme électronique via son intitulé.",
        }

    # Prédiction du modèle sur l'image
    model, labels, input_size = _load()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize(input_size)
    arr = np.expand_dims(np.array(img, dtype=np.float32), axis=0)
    probs = model.predict(arr, verbose=0)[0]
    idx = int(np.argmax(probs))
    material = labels[idx]
    bin_key = config.CLASS_TO_BIN.get(material, "MARRON")

    return {
        "bin": bin_key,
        "bin_info": config.BINS[bin_key],
        "material": material,
        "confidence": float(probs[idx]),
        "reason": f"Matière prédite par le modèle : {material}.",
    }
