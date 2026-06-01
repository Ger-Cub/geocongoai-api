#!/bin/bash
set -e

# Configuration de base
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west4"
SERVICE_NAME="gundua-ai-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Extraction des variables depuis env.yaml
GCS_BUCKET=$(grep "GCS_BUCKET" env.yaml | cut -d ':' -f 2 | tr -d ' ')
API_KEY=$(grep "GEOCONGO_API_KEY" env.yaml | cut -d ':' -f 2 | tr -d ' ')

MODELS_BUCKET=${GCS_BUCKET:-"gundua-ai-models-storage"}
WORKER_SA_EMAIL="gundua-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🌍 Déploiement Gundua AI API v1"
echo "----------------------------------------------------------"
echo "Project ID: $PROJECT_ID"
echo "Region:     $REGION"
echo "Models:     gs://$MODELS_BUCKET"
echo "----------------------------------------------------------"

# 1. Construction de l'image Docker (inclut le patch automatique terratorch)
echo "📦 Construction de l'image via Google Cloud Build..."
gcloud builds submit --tag $IMAGE_NAME .

# 2. Déploiement sur Cloud Run
# Note: On utilise 8Gi pour le chargement du modèle Prithvi
echo "🚀 Déploiement sur Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},MODEL_BUCKET=${MODELS_BUCKET},GEOCONGO_API_KEY=${API_KEY:-'test_key_geocongo'},CUSTOM_WEIGHTS_PATH=/tmp/prithvi_model.pt" \
    --timeout 3600 \
    --memory 8Gi \
    --cpu 4 \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 5 \
    --cpu-boost \
    --allow-unauthenticated

# 3. Récupération de l'URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "=========================================================="
echo "✅ ARCHITECTURE CLOUD DÉPLOYÉE"
echo "🔗 API : ${SERVICE_URL}"
echo "🔗 Documentation : ${SERVICE_URL}/docs"
echo "=========================================================="