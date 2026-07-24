"""Frontend Streamlit OpenHousing."""

from __future__ import annotations

import os
import streamlit as st

from client import OpenHousingAPIError, OpenHousingClient

# ==========================================================
# CONFIGURATION
# ==========================================================

DEFAULT_API_URL = "https://openhousing-api.onrender.com"

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

.block-container{
    max-width:1200px;
    padding-top:1rem;
}

.hero{
    background:linear-gradient(135deg,#0f766e,#14b8a6);
    color:white;
    padding:2rem;
    border-radius:18px;
    text-align:center;
    margin-bottom:2rem;
}

.prediction-card{
    background:linear-gradient(135deg,#0f766e,#14b8a6);
    color:white;
    padding:2rem;
    border-radius:18px;
    text-align:center;
    margin-top:15px;
}

[data-testid="stMetric"]{
    background:#f8fafc;
    border:1px solid #e5e7eb;
    padding:15px;
    border-radius:12px;
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
    <h3>Estimation immobilière assistée par Intelligence Artificielle</h3>
    <p>
        Renseignez les caractéristiques d'un logement et obtenez instantanément
        une estimation de sa valeur grâce à un modèle de Machine Learning.
    </p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div style="text-align:center; margin-bottom:15px;">
        <h4>🍅 Proposition faite par l'équipe Tomate</h4>
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
# INDICATEURS
# ==========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Variables analysées", "12")

with col2:
    st.metric("Modèle utilisé", "XGBRegressor")

with col3:
    st.metric("API", "Production ✅")

# ==========================================================
# EXPLICATIONS
# ==========================================================

with st.expander("📚 Comprendre les variables utilisées par le modèle"):

    st.markdown(
        """
### 🏠 Caractéristiques du logement

- **Nombre moyen de pièces** : taille moyenne des logements.
- **Logements anciens (%)** : part des logements construits avant 1940.
- **Taxe foncière** : niveau de taxation immobilière.
- **Ratio élèves / enseignant** : indicateur indirect de la qualité des écoles.

### 🌆 Caractéristiques du quartier

- **Taux de criminalité** : niveau de sécurité du secteur.
- **Zones résidentielles à faible densité** : importance des grands terrains résidentiels.
- **Surface industrielle** : présence d'activités industrielles ou commerciales.
- **Pollution NOx** : niveau de pollution atmosphérique.
- **Population à faible revenu** : indicateur socio-économique du quartier.
- **Proximité de la Charles River** : présence d'un environnement naturel valorisant.

### 🚗 Accessibilité

- **Distance aux pôles d'emploi** : proximité des principaux centres économiques.
- **Accessibilité autoroutière** : facilité d'accès aux grands axes routiers.
"""
    )

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.header("⚙️ Monitoring")

    st.write(f"**API :** `{api_url}`")

    st.write("**Modèle :** XGBRegressor")

    if st.button(
        "🔍 Vérifier l'API",
        use_container_width=True
    ):

        with st.spinner("Connexion à l'API..."):

            try:

                health = client.health()

                if health.get("status") == "healthy":
                    st.success("API disponible ✅")
                else:
                    st.warning(
                        f"État reçu : {health.get('status')}"
                    )

            except OpenHousingAPIError as exc:
                st.error(str(exc))

# ==========================================================
# SAISIE
# ==========================================================

st.subheader("📝 Paramètres à analyser")

with st.form("prediction_form"):

    tab1, tab2, tab3 = st.tabs(
        [
            "🏠 Logement",
            "🌆 Quartier",
            "🚗 Accessibilité",
        ]
    )

    # ------------------------------------------------------

    with tab1:

        col_a, col_b = st.columns(2)

        with col_a:

            rm = st.slider(
                "🛋️ Nombre moyen de pièces",
                1.0,
                10.0,
                6.575,
                help="Nombre moyen de pièces par logement.",
            )

            age = st.slider(
                "🏚️ Logements anciens (%)",
                0.0,
                100.0,
                65.2,
                help="Part des logements construits avant 1940.",
            )

        with col_b:

            tax = st.number_input(
                "💰 Taxe foncière",
                value=296.0,
                help="Taux d'imposition foncière appliqué aux biens immobiliers.",
            )

            ptratio = st.number_input(
                "🎓 Ratio élèves / enseignant",
                value=15.3,
                help="Indicateur indirect de la qualité du système scolaire.",
            )

    # ------------------------------------------------------

    with tab2:

        col_a, col_b = st.columns(2)

        with col_a:

            crim = st.number_input(
                "🚨 Taux de criminalité",
                value=0.00632,
                format="%.5f",
                help="Taux de criminalité par habitant dans la ville.",
            )

            nox = st.slider(
                "🌫️ Niveau de pollution atmosphérique",
                0.0,
                1.0,
                0.538,
                help="Concentration d'oxydes d'azote (NOx).",
            )

            lstat = st.slider(
                "📉 Population à faible revenu (%)",
                0.0,
                100.0,
                4.98,
                help="Part de la population à faible statut socio-économique.",
            )

        with col_b:

            zn = st.slider(
                "🏘️ Zones résidentielles à faible densité (%)",
                0.0,
                100.0,
                18.0,
                help="Part des terrains résidentiels composés de grandes parcelles.",
            )

            indus = st.slider(
                "🏭 Surface industrielle (%)",
                0.0,
                30.0,
                2.31,
                help="Part des terrains occupés par des activités industrielles ou commerciales.",
            )

            chas = st.selectbox(
                "🌊 Proximité de la Charles River",
                (0, 1),
                format_func=lambda x: "Oui" if x else "Non",
                help="Indique si le secteur est bordé par la Charles River.",
            )

    # ------------------------------------------------------

    with tab3:

        col_a, col_b = st.columns(2)

        with col_a:

            dis = st.number_input(
                "🚉 Distance aux pôles d'emploi",
                value=4.09,
                help="Distance pondérée aux principaux centres d'emploi de Boston.",
            )

        with col_b:

            rad = st.number_input(
                "🛣️ Accessibilité autoroutière",
                min_value=1,
                value=1,
                help="Indice d'accès aux principales autoroutes.",
            )

    submitted = st.form_submit_button(
        "🚀 Estimer le prix",
        use_container_width=True,
        type="primary",
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

    with st.spinner("Calcul de l'estimation..."):

        try:

            prediction = client.predict(payload)

            price = float(
                prediction["estimated_price_usd"]
            )

            st.success("Estimation réalisée avec succès ✅")

            st.markdown(
    f"""
    <div class="prediction-card">
        <h2>Prix estimé</h2>
        <h1>${price:,.0f}</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

            with st.expander("📊 Détails techniques"):

                left, right = st.columns(2)

                with left:
                    st.subheader("Payload envoyé")
                    st.json(payload)

                with right:
                    st.subheader("Réponse API")
                    st.json(prediction)

        except OpenHousingAPIError as exc:

            st.error(str(exc))

# ==========================================================
# FOOTER
# ==========================================================
