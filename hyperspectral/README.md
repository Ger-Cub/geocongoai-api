# GeoCongo AI - Module HyperSpectral 💎

Ce module est l'outil de **ciblage de précision** de l'écosystème **GeoCongo AI**. Il est conçu pour analyser les données satellitaires hyperspectrales **PRISMA (Level 2D, format HDF5)** afin de confirmer les anomalies détectées par le module multispectral (Gundua AI) et de réaliser une cartographie minérale ultra-précise.

## Rôle dans l'Écosystème

1. **Reconnaissance Régionale (Gundua AI)** : Balayage Sentinel-2 pour identifier les zones d'intérêt.
2. **Ciblage de Précision (Ce Module)** : Analyse PRISMA (239 bandes spectrales) pour valider chirurgicalement le potentiel minier.

## Fonctionnalités

- **Upload par Morceaux (Chunking)** : Gestion optimisée des fichiers HDF5 PRISMA volumineux.
- **Pan-Sharpening (Fusion)** : Amélioration spatiale (30m vers 5m) via PCA et Brovey.
- **Analyse Spectrale (SAM)** : Cartographie déterministe via le *Spectral Angle Mapper*.
- **Deep Learning (CNN 1D)** : Classification automatisée des signatures spectrales.

## Structure du Projet

- `main.py` : API FastAPI gérant les transferts et le pipeline.
- `engines/` : Moteurs de calcul (Fusion, SAM, Deep Learning).
- `utils/` : Chargeur HDF5 et calculs NDVI.
- `frontend/` : Composants React pour l'upload haute performance.
- `temp_prisma_uploads/` : Répertoire temporaire pour la reconstruction des fichiers HDF5.

## Installation et Lancement

### 1. Prérequis

- Python 3.10.13 (recommandé via `pyenv`)
- 4 Go de RAM minimum
- Environ 2 Go d'espace disque disponible

### 2. Installation

Placez-vous dans le dossier du module et installez les dépendances :

```bash
cd hyperspectral
pip install -r requirements.txt
```

### 3. Lancement du Serveur

Lancez l'API via Uvicorn :

```bash
python3 main.py
```

Le serveur sera disponible sur `http://localhost:8000`.

## Utilisation de l'API

1. **Documentation Interactive** : Accédez à `http://localhost:8000/docs` pour tester les endpoints.
2. **Upload** : Utilisez l'endpoint `/upload-prisma-chunk` pour envoyer vos fichiers `.he5`.
3. **Analyse** : Une fois l'upload terminé, lancez le traitement via `/process-prisma`.

---
*Généré par Antigravity AI pour le projet GeoCongo AI.*
