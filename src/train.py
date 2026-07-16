"""
Jalon 1 — Entraînement du modèle EcoSort-Search.

Réseau : Transfer Learning avec MobileNetV2 (base ImageNet gelée) + tête
de classification personnalisée, pour classer une image de déchet parmi
les 6 classes du dataset Garbage Classification / TrashNet :
    cardboard, glass, metal, paper, plastic, trash

Usage :
    python src/train.py --data_dir data/dataset --epochs 12

Le dataset attendu est un dossier contenant un sous-dossier par classe :
    data/dataset/cardboard/*.jpg
    data/dataset/glass/*.jpg
    ...

Téléchargement du dataset (au choix) :
  - Kaggle : https://www.kaggle.com/code/muhammedabdulazeem/garbage-classification
  - ou TrashNet : git clone https://github.com/garythung/trashnet
                  puis unzip data/dataset-resized.zip

Livrable : models/modele_eco_sort.h5
"""
import argparse
import os
import json

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

import config


def build_datasets(data_dir, img_size, batch_size, seed=123):
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=seed,
        image_size=img_size, batch_size=batch_size, label_mode="categorical",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=seed,
        image_size=img_size, batch_size=batch_size, label_mode="categorical",
    )
    class_names = train_ds.class_names
    print("Classes détectées :", class_names)

    # Augmentation légère (le dataset est petit)
    aug = tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
    ])

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.map(lambda x, y: (aug(x, training=True), y),
                            num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    val_ds = val_ds.prefetch(AUTOTUNE)
    return train_ds, val_ds, class_names


def build_model(num_classes, img_size):
    base = MobileNetV2(input_shape=img_size + (3,), include_top=False,
                       weights="imagenet")
    base.trainable = False  # base gelée : entraînement rapide

    inputs = layers.Input(shape=img_size + (3,))
    x = layers.Lambda(preprocess_input)(inputs)   # normalisation MobileNetV2
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data_dir", default="data/dataset")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--out", default=config.MODEL_PATH)
    args = p.parse_args()

    tf.random.set_seed(123)
    train_ds, val_ds, class_names = build_datasets(
        args.data_dir, config.IMG_SIZE, args.batch_size)

    model = build_model(len(class_names), config.IMG_SIZE)
    model.summary()

    ckpt = tf.keras.callbacks.ModelCheckpoint(
        args.out, save_best_only=True, monitor="val_accuracy", mode="max")
    early = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=4, restore_best_weights=True)

    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
              callbacks=[ckpt, early])

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    model.save(args.out)

    # Sauvegarde de l'ordre des classes (utilisé à l'inférence)
    with open("models/labels.json", "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Modèle sauvegardé : {args.out}")
    print(f"✅ Ordre des classes : models/labels.json")


if __name__ == "__main__":
    main()
