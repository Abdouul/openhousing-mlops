"""Interface Streamlit de demonstration pour OpenHousing."""
from __future__ import annotations
import os
import streamlit as st

from client import OpenHousingAPIError, OpenHousingClient

DEFAULT_API_URL = "https://openhousing-api.onrender.com"
st.set_page_config(page_title="OpenHousing - Estimation immobiliere", page_icon="??", layout="wide")
st.title("?? OpenHousing")
st.subheader("Estimation experimentale d un prix immobilier")
st.caption("Renseignez les caracteristiques du logement et de son quartier. Le modele renvoie une estimation en dollars americains.")
api_url = os.getenv("OPENHOUSING_API_URL", DEFAULT_API_URL)
client = OpenHousingClient(api_url)
with st.sidebar:
    st.header("Etat du service")
    st.caption(f"API : {api_url}")
    if st.button("Verifier l API", use_container_width=True):
        with st.spinner("Connexion a l API..."):
            try:
                health = client.health()
                if health.get("status") == "healthy":
                    st.success("API disponible")
                else:
                    st.warning(f"Etat recu : {health.get('status', 'inconnu')}")
            except OpenHousingAPIError as exc:
                st.error(str(exc))
    st.info("Sur une offre gratuite Render, le premier appel apres une periode d inactivite peut prendre environ une minute.")

with st.form("prediction_form"):
    left, middle, right = st.columns(3)
    with left:
        crim = st.number_input("Taux de criminalite (crim)", 0.0, value=0.00632, format="%.5f")
        zn = st.number_input("Zones residentielles (%) (zn)", 0.0, 100.0, 18.0)
        indus = st.number_input("Zones industrielles (%) (indus)", 0.0, value=2.31)
        chas = st.selectbox("Proximite de la Charles River (chas)", (0, 1), format_func=lambda v: "Oui" if v else "Non")
    with middle:
        nox = st.number_input("Concentration en NOx (nox)", 0.0, 1.0, 0.538, format="%.3f")
        rm = st.number_input("Nombre moyen de pieces (rm)", 1.0, value=6.575, format="%.3f")
        age = st.number_input("Logements anciens (%) (age)", 0.0, 100.0, 65.2)
        dis = st.number_input("Distance aux poles d emploi (dis)", 0.0, value=4.09)
    with right:
        rad = st.number_input("Indice d acces routier (rad)", 1, value=1, step=1)
        tax = st.number_input("Taxe fonciere (tax)", 0.0, value=296.0)
        ptratio = st.number_input("Ratio eleves/enseignant (ptratio)", 0.0, value=15.3)
        lstat = st.number_input("Population a faible statut (%) (lstat)", 0.0, 100.0, 4.98)
    submitted = st.form_submit_button("Estimer le prix", type="primary", use_container_width=True)
payload = {"crim": crim, "zn": zn, "indus": indus, "chas": chas, "nox": nox, "rm": rm, "age": age, "dis": dis, "rad": rad, "tax": tax, "ptratio": ptratio, "lstat": lstat}
if submitted:
    with st.spinner("Calcul de l estimation... Le reveil de l API peut prendre un moment."):
        try:
            prediction = client.predict(payload)
            price = float(prediction["estimated_price_usd"])
            st.success("Estimation terminee")
            st.metric("Prix immobilier estime", f"${price:,.2f}")
            if prediction.get("model_name"):
                st.caption(f"Modele utilise : {prediction['model_name']}")
            with st.expander("Voir les donnees envoyees et la reponse"):
                st.write("Variables envoyees")
                st.json(payload)
                st.write("Reponse de l API")
                st.json(prediction)
        except OpenHousingAPIError as exc:
            st.error(str(exc))
st.divider()
st.warning("Demonstration pedagogique uniquement : le jeu Boston Housing est historique et ne doit pas servir a une expertise immobiliere reelle.")
