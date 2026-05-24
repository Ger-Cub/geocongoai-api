#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west4"
SERVICE_NAME="geocongoai-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MODELS_BUCKET="geocongoai-models-storage"
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Préparation du déploiement pour GeoCongo AI..."

# 1. Vérification et exécution de la configuration IAM
chmod +x scripts/setup_iam.sh
./scripts/setup_iam.sh

# 2. Construction de l'image via Cloud Build
echo "📦 Construction de l'image Docker..."
gcloud builds submit --tag $IMAGE_NAME .

# 3. Déploiement sur Cloud Run
# L'option --cpu-boost est activée pour accélérer le chargement des librairies au démarrage
echo "🚀 Déploiement sur Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --service-account $WORKER_SA_EMAIL \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},MODELS_BUCKET=${MODELS_BUCKET},GEOCONGO_API_KEY=test_key_geocongo,USE_LOCAL_MODELS=true" \
    --timeout 600 \
    --memory 8Gi \
    --cpu 4 \
    --cpu-boost \
    --allow-unauthenticated

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "=========================================================="
echo "✅ Déploiement réussi !"
echo "🔗 URL de l'API : ${SERVICE_URL}"
echo "💡 Note : Assurez-vous d'avoir déployé les modèles Vertex AI via scripts/deploy_vertex.sh"
echo "=========================================================="