"""Application Flask EcoSort-Search."""
from __future__ import annotations

import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

try:
    from . import predict, scraper
except ImportError:  # Permet aussi l'execution directe : python src/app.py
    import predict
    import scraper


DEMO_PRODUCTS = [
    {
        "title": "Bouteille d'eau vide en plastique",
        "price": "Mode démo",
        "image": "images/ecosort-hero-civic.png",
        "url": "",
        "demo_bin": "JAUNE",
        "demo_material": "plastic",
        "demo_reason": "Produit de démonstration : une bouteille plastique vide va dans la poubelle jaune.",
    },
    {
        "title": "Bocal de confiture en verre",
        "price": "Mode démo",
        "image": "images/ecosort-hero.png",
        "url": "",
        "demo_bin": "VERTE",
        "demo_material": "glass",
        "demo_reason": "Produit de démonstration : les emballages en verre vont dans la poubelle verte.",
    },
    {
        "title": "Cahier et feuilles propres",
        "price": "Mode démo",
        "image": "images/ecosort-hero-ai.png",
        "url": "",
        "demo_bin": "BLEUE",
        "demo_material": "paper",
        "demo_reason": "Produit de démonstration : les papiers propres vont dans la poubelle bleue.",
    },
    {
        "title": "Chargeur de téléphone usagé",
        "price": "Mode démo",
        "image": "images/ecosort-hero-ai.png",
        "url": "",
        "demo_bin": "GRIS",
        "demo_material": "électronique (D3E)",
        "demo_reason": "Produit de démonstration : un appareil électrique ou accessoire à prise va dans le bac D3E.",
    },
    {
        "title": "Sachet plastique souple sale",
        "price": "Mode démo",
        "image": "images/ecosort-hero-civic.png",
        "url": "",
        "demo_bin": "MARRON",
        "demo_material": "trash",
        "demo_reason": "Produit de démonstration : un déchet résiduel non recyclable va dans la poubelle marron ou noire.",
    },
]


def _recent_history():
    return session.get("recent_history", [])


def _add_history(label, detail, bin_label=None):
    history = _recent_history()
    item = {"label": label, "detail": detail, "bin_label": bin_label}
    history = [item] + [entry for entry in history if entry != item]
    session["recent_history"] = history[:5]


def _demo_verdict(bin_key, material, reason):
    try:
        from . import config
    except ImportError:
        import config

    return {
        "bin": bin_key,
        "bin_info": config.BINS[bin_key],
        "material": material,
        "confidence": 1.0,
        "reason": reason,
    }


def create_app() -> Flask:
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ecosort-dev-key")

    @app.get("/")
    def index():
        return render_template("index.html", recent_history=_recent_history())

    @app.get("/about")
    def about():
        try:
            from . import config
        except ImportError:
            import config

        return render_template("about.html", bins=config.BINS)

    @app.get("/demo")
    def demo():
        products = [
            {**product, "image": url_for("static", filename=product["image"])}
            for product in DEMO_PRODUCTS
        ]
        _add_history("Mode démo", "Produits préremplis", "Démo")
        return render_template(
            "results.html",
            query="Mode démo",
            products=products,
            is_demo=True,
            fallback_available=False,
        )

    @app.post("/search")
    def search():
        query = request.form.get("query", "").strip()
        if not query:
            flash("Veuillez saisir un nom de produit.")
            return redirect(url_for("index"))

        error_message = ""
        fallback_available = False
        try:
            products = scraper.search_products(query, max_results=5)
        except Exception as exc:
            error_message = (
                "Jumia ne répond pas pour le moment. Vous pouvez réessayer ou utiliser "
                "le mode démo pour présenter le parcours complet."
            )
            flash(error_message)
            products = []
            fallback_available = True

        if not products:
            flash("Aucun produit trouvé pour cette recherche.")
        else:
            _add_history("Recherche", query, f"{len(products)} résultat(s)")

        return render_template(
            "results.html",
            query=query,
            products=products,
            is_demo=False,
            error_message=error_message,
            fallback_available=fallback_available,
        )

    @app.post("/predict")
    def predict_product():
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()
        image = request.form.get("image", "").strip()
        product_url = request.form.get("url", "").strip()
        demo_bin = request.form.get("demo_bin", "").strip()
        demo_material = request.form.get("demo_material", "").strip()
        demo_reason = request.form.get("demo_reason", "").strip()
        product = {"title": title, "price": price, "image": image, "url": product_url}

        if demo_bin:
            verdict = _demo_verdict(demo_bin, demo_material, demo_reason)
            _add_history("Produit classé", title, verdict["bin_info"]["label"])
            return render_template("prediction.html", product=product, verdict=verdict)

        image_bytes = scraper.download_image(image)
        if image_bytes is None:
            flash(
                "Impossible de récupérer l'image du produit sélectionné. "
                "Essayez un autre résultat ou utilisez le mode démo."
            )
            return render_template("prediction.html", product=product, verdict=None)

        verdict = predict.predict(image_bytes, title)
        _add_history("Produit classé", title, verdict["bin_info"]["label"])
        return render_template("prediction.html", product=product, verdict=verdict)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "ecosort-search"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=True)
