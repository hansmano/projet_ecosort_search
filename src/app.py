"""
EcoSort-Search — Interface Streamlit.

Flux : l'utilisateur saisit un nom de produit -> scraping Jumia en direct ->
sélection d'un produit -> le modèle attribue la consigne de tri et l'écran
se colore aux couleurs de la poubelle correspondante.
"""
import streamlit as st

import config
import scraper
import predict

st.set_page_config(page_title="EcoSort-Search", page_icon="♻️", layout="wide")


def paint_screen(bin_info):
    """Colore le fond de l'écran aux couleurs de la poubelle."""
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {bin_info['color']}; }}
        .ecosort-card {{
            background: rgba(0,0,0,0.15); color: {bin_info['text']};
            padding: 2rem; border-radius: 16px; text-align: center;
        }}
        h1, h2, h3, p, label {{ color: {bin_info['text']} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- État ---
if "results" not in st.session_state:
    st.session_state.results = []
if "verdict" not in st.session_state:
    st.session_state.verdict = None

# Si un verdict existe, colorer l'écran
if st.session_state.verdict:
    paint_screen(st.session_state.verdict["bin_info"])

st.title("♻️ EcoSort-Search")
st.caption("Tapez le nom d'un produit — l'IA vous indique la bonne poubelle.")

# --- Recherche ---
with st.form("search"):
    query = st.text_input("Nom du produit", placeholder="ex : bouteille d'eau, chargeur, journal…")
    submitted = st.form_submit_button("🔍 Rechercher sur Jumia")

if submitted and query.strip():
    st.session_state.verdict = None
    with st.spinner("Recherche sur Jumia…"):
        try:
            st.session_state.results = scraper.search_products(query.strip(), max_results=5)
        except Exception as e:
            st.session_state.results = []
            st.error(f"Échec du scraping Jumia : {e}")

# --- Résultats ---
results = st.session_state.results
if results:
    st.subheader("Résultats — choisissez un produit")
    cols = st.columns(len(results))
    for i, (col, prod) in enumerate(zip(cols, results)):
        with col:
            if prod["image"]:
                st.image(prod["image"], use_container_width=True)
            st.write(f"**{prod['title'][:70]}**")
            if prod["price"]:
                st.write(prod["price"])
            if st.button("Analyser", key=f"pick_{i}"):
                with st.spinner("Analyse par l'IA…"):
                    img_bytes = scraper.download_image(prod["image"])
                    if img_bytes is None:
                        st.error("Image du produit indisponible.")
                    else:
                        st.session_state.verdict = predict.predict(img_bytes, prod["title"])
                        st.rerun()

# --- Verdict ---
v = st.session_state.verdict
if v:
    info = v["bin_info"]
    st.markdown(
        f"""
        <div class="ecosort-card">
            <h1>{info['label']}</h1>
            <h3>{info['desc']}</h3>
            <p>{v['reason']}</p>
            <p>Confiance : {v['confidence']*100:.0f}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
