#!/bin/bash
set -e

PROJECT_ID="geocongoai-api"
MODELS_BUCKET="geocongo-models-bucket" # Remplacez par le nom de votre bucket
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Récupérer le compte de service par défaut de Compute Engine (utilisé par Vertex AI)
PROJECT_NUM=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

echo "🔐 Configuration des permissions IAM pour $PROJECT_ID..."

# 1. Permissions pour Cloud Run (Worker SA)
echo "-> Autorisation de Cloud Run à invoquer Vertex AI..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$WORKER_SA_EMAIL" \
    --role="roles/aiplatform.user" > /dev/null

echo "-> Autorisation de Cloud Run à lire/écrire sur Cloud Storage (images temporaires)..."
gcloud storage buckets add-iam-policy-binding gs://$MODELS_BUCKET \
    --member="serviceAccount:$WORKER_SA_EMAIL" \
    --role="roles/storage.objectAdmin" > /dev/null

# 2. Permissions pour Vertex AI (Compute Engine SA)
echo "-> Autorisation de Vertex AI à lire les modèles et écrire les résultats sur Cloud Storage..."
gcloud storage buckets add-iam-policy-binding gs://$MODELS_BUCKET \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/storage.objectAdmin" > /dev/null

echo "✅ Configuration IAM terminée avec succès !"