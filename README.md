# OpenHousing MLOps

Projet de démarrage pour une application MLOps autour de données de logement.

## Structure

- data/raw : données brutes
- data/processed : données traitées
- notebooks : explorations et prototypages
- src/etl : pipelines ETL
- src/model : modèles de prédiction
- src/api : API de service
- tests : tests automatisés
- docker : configuration Docker
- .github/workflows : CI/CD

## Démarrage rapide

1. Créer un environnement Python
2. Installer les dépendances : `pip install -r requirements.txt`
3. Lancer l'API : `uvicorn src.api.main:app --reload`
4. Lancer les tests : `pytest`
