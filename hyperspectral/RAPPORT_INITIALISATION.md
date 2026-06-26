# Rapport d'Initialisation : GeoCongo AI HyperSpectral

## 1. Objectif du Travail

L'objectif était d'instaurer la structure technique de base pour le nouveau module de détection de gisements par imagerie hyperspectrale PRISMA, en intégrant des capacités de chargement de gros fichiers et de traitement d'images avancé.

## 2. Architecture Implémentée (Backend FastAPI)

Le backend a été conçu de manière modulaire pour garantir scalabilité et clarté :

- **`main.py`** : Point d'entrée de l'API gérant le transfert par morceaux (Chunked Uploading) et l'orchestration des pipelines de traitement.
- **`engines/` (Moteurs de Traitement)** :
  - **Fusion (Pan-sharpening)** : Algorithmes Brovey et PCA pour améliorer la résolution spatiale à 5m.
  - **Analyse Spectrale** : Implémentation du Spectral Angle Mapper (SAM) pour la cartographie minérale.
  - **Deep Learning** : Architecture CNN 1D (PyTorch) pour la classification des signatures spectrales.
- **`utils/` (Utilitaires)** :
  - **HDF5 Loader** : Extracteur spécialisé pour les structures de données PRISMA L2D.
- **`requirements.txt`** : Liste complète des dépendances scientifiques (h5py, torch, scikit-learn, rasterio, etc.).

## 3. Interface Utilisateur (Frontend React)

- **`frontend/PrismaUploader.jsx`** : Composant prêt à l'emploi utilisant l'API `File.slice()` pour envoyer des fichiers lourds sans saturer la mémoire du navigateur, avec une barre de progression en temps réel.

## 4. Emplacement des Fichiers

En raison des restrictions de droits d'accès au système, le projet a été temporairement initialisé ici :
`~/Documents/GeoKivuDoc/geocongoai-api/hyperspectral/`

## 5. Problèmes Rencontrés & Solutions

- **Espace Disque Insuffisant** : L'installation des dépendances (notamment Torch/CUDA) a échoué par manque d'espace sur la partition `/` (moins de 3 Go disponibles).
- **Solution Préconisée** : Nettoyage du cache pip (`pip cache purge`) ou passage à une version CPU plus légère de Torch pour la phase de développement.

## 6. Prochaines Étapes

1. Libérer de l'espace disque pour finaliser l'installation.
2. Intégrer les bibliothèques spectrales de l'USGS dans le moteur SAM.
3. Entraîner et charger les poids réels du modèle CNN 1D.
4. Exporter les résultats en format GeoTIFF pour intégration cartographique.

---
