#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west4"
SERVICE_NAME="geocongoai-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MODELS_BUCKET="geocongoai-models-storage"
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Préparation du déploiement OPTIMISÉ pour GeoCongo AI..."

# 1. Vérification et exécution de la configuration IAM (Optionnel)
if [ -f scripts/setup_iam.sh ]; then
    chmod +x scripts/setup_iam.sh
    ./scripts/setup_iam.sh
fi

# 2. Construction de l'image via Cloud Build
echo "📦 Construction de l'image Docker..."
gcloud builds submit --tag $IMAGE_NAME .

# 3. Déploiement sur Cloud Run avec Optimisations de Coûts
# - min-instances 0 : Facturation 0 si pas de trafic
# - max-instances 5 : Limite l'explosion des coûts en cas de pic
# - concurrency 10 : Permet à 1 instance de traiter 10 analyses en parallèle (optimise RAM/CPU)
# - cpu-boost : Accélère le démarrage (chargement Prithvi) sans surcoût majeur
# - cpu-throttling : (Par défaut) On ne paye le CPU que pendant le traitement des requêtes
echo "🚀 Déploiement sur Cloud Run (Mode Économique)..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --service-account $WORKER_SA_EMAIL \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},MODELS_BUCKET=${MODELS_BUCKET},GEOCONGO_API_KEY=test_key_geocongo" \
    --timeout 3600 \
    --memory 8Gi \
    --cpu 4 \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 10 \
    --cpu-boost \
    --allow-unauthenticated

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "=========================================================="
echo "✅ Déploiement réussi avec optimisations de coûts !"
echo "🔗 URL de l'API : ${SERVICE_URL}"
echo "💡 Configuration : Scale-to-zero (0 instance si inactif)"
echo "💡 Parallélisme : 10 requêtes simultanées par conteneur"
echo "=========================================================="