#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
MODELS_BUCKET="geocongo-models-bucket" 
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔐 Configuration des permissions IAM pour $PROJECT_ID..."

# 1. Permissions pour Cloud Run (Worker SA)
# Note: Vertex AI n'est plus utilisé en direct, donc on retire roles/aiplatform.user

echo "-> Autorisation de Cloud Run à lire/écrire sur Cloud Storage (Buckets)..."
gcloud storage buckets add-iam-policy-binding gs://$MODELS_BUCKET \
    --member="serviceAccount:$WORKER_SA_EMAIL" \
    --role="roles/storage.objectAdmin" > /dev/null

echo "-> Autorisation pour Logging et Monitoring..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$WORKER_SA_EMAIL" \
    --role="roles/logging.logWriter" > /dev/null

echo "✅ Configuration IAM terminée (Nettoyée de Vertex AI)."