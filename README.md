# Gundua Engine - Prithvi EO v2

Cette API fournit un pipeline complet pour l'analyse géologique et environnementale automatisée en République Démocratique du Congo, basée sur le modèle de fondation NASA-IBM **Prithvi EO v2**.

## Fonctionnalités

- **Inférence Unique** : Utilisation d'un seul modèle (`prithvi_eo_v2_300`) pour extraire des caractéristiques profondes.
- **15 Analyses Spécialisées** : Du suivi minier à la détection de catastrophes naturelles.
- **Intégration GEE** : Téléchargement automatique des données Sentinel-2 et Landsat 8.
- **Sorties Multi-formats** : GeoJSON pour les vecteurs, GeoTIFF pour les rasters, et PNG pour la visualisation.

## Stratégie de l'Écosystème GeoCongo AI

L'écosystème repose sur une approche en deux étapes :

1. **Reconnaissance Régionale (ce module)** : Analyse multispectrale Sentinel-2/Prithvi pour le criblage de vastes zones.
2. **Ciblage de Précision (module HyperSpectral)** : Analyse PRISMA ultra-précise pour la validation minérale finale.

*Voir `ecosystem_manifest.json` et `hyperspectral/module_manifest.json` pour les détails techniques de chaque module.*

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

## Installation et Configuration (Développement)

### 1. Environnement Python

Le projet est optimisé pour **Python 3.10.13**. Nous utilisons une version légère de PyTorch (CPU) pour économiser de l'espace disque en développement.

```bash
# Activation de la version Python correcte (via pyenv)
pyenv global 3.10.13

# Installation des dépendances avec index CPU optimisé
pip install -r requirements.txt
```

### 2. Authentification Google Earth Engine (Non-interactive)

Pour éviter les blocages de navigateur, le projet utilise un **compte de service**.

1. Placez votre fichier de clé JSON à la racine du projet sous le nom `service-account.json`.
2. Le fichier est automatiquement ignoré par Git via `.gitignore`.
3. Assurez-vous que l'e-mail du compte de service est enregistré sur [Earth Engine Register](https://code.earthengine.google.com/register).

### 3. Lancement du Serveur

Le projet se compose de deux modules principaux :

**Module Principal (Gundua Engine - Prithvi v2) :**

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Module HyperSpectral (Analyse PRISMA) :**

```bash
cd hyperspectral
python3 main.py
```

## Nouveautés Récentes

- **Optimisation Ressources** : Passage à `torch+cpu` via `--extra-index-url` dans `requirements.txt`.
- **Auth Automatisée** : Intégration transparente via compte de service Google Cloud.
- **Documentation Interactive** : Descriptions enrichies et pédagogiques directement dans Swagger UI (`/docs`).
- **Module HyperSpectral** : Nouveau module dédié au traitement des données PRISMA L2D (HDF5).

## API Endpoints

- `GET /` : Message de bienvenue et statut.
- `GET /health` : État détaillé du service.
- `GET /docs` : Documentation Swagger complète (recommandé).
- `POST /analyze` : Orchestration des 15 types d'analyses géospatiales.
