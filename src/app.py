"""Application Flask EcoSort-Search."""
from __future__ import annotations

import os

from flask import Flask, flash, redirect, render_template, request, url_for

try:
    from . import predict, scraper
except ImportError:  # Permet aussi l'execution directe : python src/app.py
    import predict
    import scraper


def create_app() -> Flask:
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ecosort-dev-key")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/search")
    def search():
        query = request.form.get("query", "").strip()
        if not query:
            flash("Veuillez saisir un nom de produit.")
            return redirect(url_for("index"))

        try:
            products = scraper.search_products(query, max_results=5)
        except Exception as exc:
            flash(f"Recherche Jumia indisponible : {exc}")
            products = []

        if not products:
            flash("Aucun produit trouve pour cette recherche.")

        return render_template("results.html", query=query, products=products)

    @app.post("/predict")
    def predict_product():
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()
        image = request.form.get("image", "").strip()
        product_url = request.form.get("url", "").strip()
        product = {"title": title, "price": price, "image": image, "url": product_url}

        image_bytes = scraper.download_image(image)
        if image_bytes is None:
            flash("Impossible de recuperer l'image du produit selectionne.")
            return render_template("prediction.html", product=product, verdict=None)

        verdict = predict.predict(image_bytes, title)
        return render_template("prediction.html", product=product, verdict=verdict)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "ecosort-search"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=True)
