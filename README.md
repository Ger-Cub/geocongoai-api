# GeoCongo AI API - Prithvi EO v2

Cette API fournit un pipeline complet pour l'analyse géologique et environnementale automatisée en République Démocratique du Congo, basée sur le modèle de fondation NASA-IBM **Prithvi EO v2**.

## Fonctionnalités

- **Inférence Unique** : Utilisation d'un seul modèle (`prithvi_eo_v2_300`) pour extraire des caractéristiques profondes.
- **15 Analyses Spécialisées** : Du suivi minier à la détection de catastrophes naturelles.
- **Intégration GEE** : Téléchargement automatique des données Sentinel-2 et Landsat 8.
- **Sorties Multi-formats** : GeoJSON pour les vecteurs, GeoTIFF pour les rasters, et PNG pour la visualisation.

## Structure du Projet

- `app/main.py` : Points d'entrée FastAPI et orchestration.
- `app/services/inference.py` : Service d'inférence Prithvi via `terratorch`.
- `app/services/analysis/` : Modules spécifiques pour les 15 types d'analyse.
- `app/utils/` : Utilitaires géospatiaux et calculs d'indices spectraux.

## Analyses Disponibles (15 types)

| Catégorie | Analyses |
|-----------|----------|
| **Géologie & Mines** | Unités géologiques, Lithologie, Altération hydrothermale, Détection minérale, Linéaments, Suivi minier, Restauration |
| **Environnement** | Glissements de terrain, Inondations, Feux de forêt, Dégâts post-catastrophe |
| **Sols & Climat** | Occupation des sols (LULC), Cultures, Plans d'eau, Déforestation, Carbone |

## Installation et Lancement

### Préréglages

1. Authentification Google Earth Engine
2. Clé API (définie via `API_KEY`)

### Docker

```bash
docker build -t geocongo-api .
docker run -p 8080:8080 -e GCP_PROJECT_ID=votre-projet geocongo-api
```

### Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /analysis-types` : Liste documentée des analyses.
- `POST /analyze` : Lancer une analyse (nécessite BBOX et `analysis_type`).
- `GET /results/{request_id}` : Récupérer les résultats et liens de téléchargement.
- `GET /health` : État du service et du modèle.
