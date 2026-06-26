# 🌍 Gundua Engine - Guide de Déploiement

Ce dépôt contient la branche `deploy-gundua-ai` configurée spécifiquement pour le projet **Gundua Engine**.

## Configuration Cible

- **Compte Google :** `it.servicecemgoma@gmail.com`
- **Projet GCP :** `gundua-ai`
- **Région :** `europe-west4`

## Étapes de Déploiement Rapide

### 1. Initialisation de l'Infrastructure

Lancez le script de configuration pour créer le bucket et le compte de service :

```bash
chmod +x scripts/setup_gundua.sh
./scripts/setup_gundua.sh
```

### 2. Téléchargement des Modèles

Assurez-vous que les modèles suivants sont présents dans votre bucket `gs://gundua-ai-models-storage/` :

- `prithvi/prithvi_model.pt`

### 3. Déploiement

Une fois l'infrastructure prête et les modèles uploadés, déployez l'API sur Cloud Run :

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## Variables d'Environnement (Produit)

Dans cette branche, nous utilisons :

- `GUNDUA_API_KEY` : Clé de sécurité pour l'accès aux endpoints.
- `GCS_BUCKET` : `gundua-ai-models-storage`

## Architecture Gérée

- **Cloud Run :** Service auto-scalé avec Startup Boost.
- **Cloud Storage :** Montage FUSE pour l'accès direct aux modèles.
- **Cloud Tasks :** File d'attente pour le traitement asynchrone des analyses lourdes.
