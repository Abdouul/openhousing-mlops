# OpenHousing MLOps

[![CI/CD](https://github.com/Abdouul/openhousing-mlops/actions/workflows/ci.yml/badge.svg)](https://github.com/Abdouul/openhousing-mlops/actions/workflows/ci.yml)

OpenHousing étudie les indicateurs socio-économiques et les prix immobiliers. Ce dépôt contient le POC Boston Housing et accueillera le pipeline ETL, le modèle et l'API du MVP.

## Organisation

    data/raw/          Données sources non modifiées
    data/processed/    Données nettoyées par l'ETL
    database/          Base SQLite locale
    models/            Modèles et métriques générés
    notebooks/         Exploration et validation du POC
    src/etl/           Extraction, transformation et chargement
    src/model/         Entraînement et prédiction
    src/api/           Service FastAPI
    frontend/          Interface utilisateur Streamlit
    tests/             Tests automatisés

## POC

Le workflow POC utilise notebooks/01_EDA.ipynb pour l'exploration, puis notebooks/02_Model.ipynb pour comparer Linear Regression, Random Forest et XGBoost. Le meilleur pipeline est enregistré dans models/model.pkl. La variable historique sensible b est exclue du modèle.

La cible medv représente une valeur médiane en milliers de dollars. Elle est multipliée par 1 000 avant l'entraînement.

## Démarrage

    pip install -r requirements.txt
    jupyter lab
    pytest -q
    uvicorn src.api.main:app --reload

Pour lancer les services conteneurisés :

    docker compose up --build

## Pipeline ETL

Le pipeline valide le schema, supprime les doublons, exclut la variable sensible b, convertit medv en price_usd, puis charge les donnees dans un CSV traite et dans SQLite.

    python -m src.etl.pipeline

Pour telecharger automatiquement la source si le fichier brut est absent :

    python -m src.etl.pipeline --download-if-missing

Sorties generees :

- data/processed/boston_housing_clean.csv
- data/processed/quality_report.json
- database/openhousing.db, table housing

Les valeurs manquantes des variables explicatives ne sont pas imputees par l ETL. Cette operation reste dans le pipeline ML afin d eviter une fuite de donnees.

## API FastAPI

Le service charge models/model.pkl au demarrage et expose les routes suivantes :

- GET /health : etat de l API et du modele
- GET /ready : disponibilite pour les predictions
- GET /model : algorithme et variables attendues
- POST /predict : estimation du prix en USD
- GET /docs : documentation Swagger interactive

Demarrage local :

    uvicorn src.api.main:app --reload

Exemple de prediction :

    curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"crim\":0.00632,\"zn\":18,\"indus\":2.31,\"chas\":0,\"nox\":0.538,\"rm\":6.575,\"age\":65.2,\"dis\":4.09,\"rad\":1,\"tax\":296,\"ptratio\":15.3,\"lstat\":4.98}"

## Entrainement automatise

Le modele de production est recree depuis les donnees traitees, sans dependre du notebook :

    python -m src.etl.pipeline --download-if-missing
    python -m src.model.train

Le script compare Linear Regression, Random Forest et XGBoost avec le RMSE, sauvegarde le meilleur dans models/model.pkl et ecrit les metriques dans models/metrics.json. Ces fichiers restent ignores par Git car ils sont generes automatiquement.

## Docker

L image API utilise Python 3.12 et XGBoost CPU. Elle s execute avec un utilisateur non-root, un systeme de fichiers en lecture seule et un healthcheck sur /ready. Le fichier models/model.pkl doit exister avant le demarrage.

Construire et lancer l API :

    docker compose build api
    docker compose up -d api

Verifier le service :

    docker compose ps
    docker compose logs -f api

Swagger est disponible sur http://localhost:8000/docs.

Executer l ETL dans Docker :

    docker compose --profile pipeline run --rm etl

Lancer Jupyter en mode developpement :

    docker compose --profile dev up jupyter

Arreter les services :

    docker compose down


## Interface Streamlit

L interface appelle l API FastAPI publique et ne charge pas le modele elle-meme. Elle propose les 12 variables, verifie la disponibilite de l API, affiche le prix estime en USD et gere le temps de reveil possible de Render.

Lancement local avec l API Render :

    pip install -r frontend/requirements.txt
    streamlit run frontend/app.py

Lancement Docker avec l API locale :

    docker compose --profile ui up --build streamlit

Interface : http://localhost:8501

Pour Streamlit Community Cloud, selectionner ce depot, la branche main et le fichier d entree `frontend/app.py`. Le fichier `frontend/requirements.txt` sera detecte automatiquement. La variable `OPENHOUSING_API_URL` est facultative : par defaut, l interface utilise `https://openhousing-api.onrender.com`.

## CI/CD

GitHub Actions execute automatiquement :

1. compilation et tests Python ;
2. validation JSON des notebooks ;
3. execution ETL et entrainement du meilleur modele ;
4. construction de la cible Docker api avec model.pkl ;
5. publication sur GitHub Container Registry apres succes sur main ;
6. declenchement automatique du deploiement Render par Deploy Hook.

Les Pull Requests construisent l image sans la publier. Les pushes sur main publient deux tags : latest et sha-<commit>.

Image publiee :

    ghcr.io/abdouul/openhousing-mlops:latest

Pour Render, utiliser l image GHCR preconstruite ci-dessus. Elle contient deja model.pkl et peut demarrer sans volume local.

Dependabot verifie chaque semaine les actions GitHub, les dependances Python et l image de base Docker.

## Deploiement Render

Le fichier render.yaml decrit un Web Service gratuit en region Frankfurt, base sur l image GHCR autonome et controle par /ready.

Image :

    ghcr.io/abdouul/openhousing-mlops:latest

Le service attendu est openhousing-api. Apres deploiement, verifier /health, /ready, /model, /predict et /docs.
