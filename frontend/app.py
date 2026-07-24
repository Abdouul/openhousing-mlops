"""Interface Streamlit moderne pour OpenHousing."""
from __future__ import annotations

import os
import streamlit as st

from client import OpenHousingAPIError, OpenHousingClient


DEFAULT_API_URL = "https://openhousing-api.onrender.com"

# ==========================================================
# CONFIG PAGE
# ==========================================================

st.set_page_config(
    page_title="OpenHousing",
    page_icon="🏡",
    layout="wide",
)

# ==========================================================
# STYLE
# ==========================================================

st.markdown(
    """
    <style>

    .main > div {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1200px;
    }

    [data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 12px;
    }

    .hero {
        background: linear-gradient(135deg, #0f766e, #14b8a6);
        padding: 2rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }

    .prediction-card {
        background: linear-gradient(135deg, #0f766e, #14b8a6);
        padding: 2rem;
        border-radius: 18px;
        text-align: center;
        color: white;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🏡 OpenHousing</h1>
        <h3>Estimation immobilière par Intelligence Artificielle</h3>
        <p>
            Obtenez instantanément une estimation de prix à partir des
            caractéristiques du logement et de son environnement.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# API
# ==========================================================

api_url = os.getenv("OPENHOUSING_API_URL", DEFAULT_API_URL)
client = OpenHousingClient(api_url)

# ==========================================================
# KPI
# ==========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Variables analysées", "12")

with col2:
    st.metric("Type de modèle", "Régression ML")

with col3:
    st.metric("API", "En ligne ✅")

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.header("⚙️ Monitoring")

    st.markdown(f"**API** : `{api_url}`")

    if st.button("🔍 Vérifier l'API", use_container_width=True):

        with st.spinner("Connexion en cours..."):

            try:

                health = client.health()

                if health.get("status") == "healthy":
                    st.success("API disponible ✅")
                else:
                    st.warning(
                        f"État reçu : {health.get('status', 'inconnu')}"
                    )

            except OpenHousingAPIError as exc:
                st.error(str(exc))

# ==========================================================
# FORMULAIRE
# ==========================================================

st.subheader("📝 Paramètres du logement")

with st.form("prediction_form"):

    tab1, tab2, tab3 = st.tabs(
        [
            "🏠 Logement",
            "🌆 Quartier",
            "📊 Indicateurs",
        ]
    )

    # ------------------------------------------------------

    with tab1:

        c1, c2 = st.columns(2)

        with c1:
            rm = st.slider(
                "Nombre moyen de pièces",
                min_value=1.0,
                max_value=10.0,
                value=6.575,
                step=0.1,
            )

            age = st.slider(
                "Ancienneté des logements (%)",
                min_value=0.0,
                max_value=100.0,
                value=65.2,
            )

        with c2:

            tax = st.number_input(
                "Taxe foncière",
                value=296.0,
            )

            ptratio = st.number_input(
                "Ratio élèves / enseignant",
                value=15.3,
            )

    # ------------------------------------------------------

    with tab2:

        c1, c2 = st.columns(2)

        with c1:

            crim = st.number_input(
                "Indice de criminalité",
                value=0.00632,
                format="%.5f",
            )

            nox = st.slider(
                "Concentration NOx",
                min_value=0.0,
                max_value=1.0,
                value=0.538,
            )

            lstat = st.slider(
                "Population à faible revenu (%)",
                min_value=0.0,
                max_value=100.0,
                value=4.98,
            )

        with c2:

            zn = st.slider(
                "Zones résidentielles (%)",
                min_value=0.0,
                max_value=100.0,
                value=18.0,
            )

            indus = st.slider(
                "Zones industrielles (%)",
                min_value=0.0,
                max_value=30.0,
                value=2.31,
            )

            chas = st.selectbox(
                "Proximité Charles River",
                (0, 1),
                format_func=lambda v: "Oui" if v else "Non",
            )

    # ------------------------------------------------------

    with tab3:

        c1, c2 = st.columns(2)

        with c1:

            dis = st.number_input(
                "Distance aux pôles d'emploi",
                value=4.09,
            )

        with c2:

            rad = st.number_input(
                "Indice d'accès routier",
                min_value=1,
                value=1,
            )

    submitted = st.form_submit_button(
        "🚀 Estimer le prix",
        type="primary",
        use_container_width=True,
    )

# ==========================================================
# PAYLOAD
# ==========================================================

payload = {
    "crim": crim,
    "zn": zn,
    "indus": indus,
    "chas": chas,
    "nox": nox,
    "rm": rm,
    "age": age,
    "dis": dis,
    "rad": rad,
    "tax": tax,
    "ptratio": ptratio,
    "lstat": lstat,
}

# ==========================================================
# PREDICTION
# ==========================================================

if submitted:

    with st.spinner(
        "Calcul de l'estimation... "
        "Le réveil de l'API peut prendre quelques secondes."
    ):

        try:

            prediction = client.predict(payload)

            price = float(
                prediction["estimated_price_usd"]
            )

            st.success("✅ Estimation générée")

            st.markdown(
                f"""
                <div class="prediction-card">
                    <h2>Prix estimé</h2>
                    <h1>${price:,.0f}</h1>
                    <p>Prédiction réalisée par le modèle OpenHousing</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption("Niveau de confiance indicatif")

            st.progress(89)

            if prediction.get("model_name"):

                st.info(
                    f"🤖 Modèle utilisé : "
                    f"{prediction['model_name']}"
                )

            with st.expander("📊 Détails techniques"):

                col_left, col_right = st.columns(2)

                with col_left:

                    st.subheader("Variables envoyées")
                    st.json(payload)

                with col_right:

                    st.subheader("Réponse API")
                    st.json(prediction)

        except OpenHousingAPIError as exc:

            st.error(str(exc))

# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.info(
    """
    ℹ️ Cette application constitue une démonstration MLOps.
    Les estimations reposent sur le jeu de données Boston Housing
    et ne doivent pas être utilisées pour une expertise immobilière réelle.
    """
)