#!/bin/bash
set -e # Arrete le script en cas d'erreur

# --- Configuration ---
PROJECT_ID="geocongoai-api"
SERVICE_NAME="geocongoai-api"
REGION="europe-west4" # Region avec support GPU (Pays-Bas)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
MODELS_BUCKET="geocongo-models-bucket" # ⬅️ IMPORTANT: Remplacez par le nom EXACT de votre bucket GCS
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com" # Remplacez si vous utilisez un autre nom

# --- 1. Build de l'image Docker ---
echo "Building image $IMAGE_NAME..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID .

# --- 2. Déploiement initial (ou mise à jour) ---
echo "Deploying service '$SERVICE_NAME' to Cloud Run..."
gcloud beta run deploy $SERVICE_NAME \
    --project=$PROJECT_ID \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --cpu=4 \
    --memory=16Gi \
    --gpu=1 \
    --gpu-type=nvidia-l4 \
    --execution-environment gen2 \
    --cpu-boost \
    --timeout=600s \
    --port=8000 \
    --add-volume=name=models-volume,type=cloud-storage,bucket=${MODELS_BUCKET} \
    --add-volume-mount=volume=models-volume,mount-path=/app/models \
    --set-env-vars "GEOCONGO_API_KEY=test_key_geocongo,DEVICE=gpu,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},CLOUD_TASKS_QUEUE=geocongo-results-queue,CLOUD_TASKS_WORKER_SA_EMAIL=${WORKER_SA_EMAIL}"

echo "✅ Initial deployment command sent. Fetching service URL..."

# --- 3. Récupération de l'URL et redéploiement pour le worker ---
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Could not retrieve service URL. Aborting."
    exit 1
fi

echo "Service URL is: $SERVICE_URL"
echo "Re-deploying to set the CLOUD_TASKS_WORKER_URL environment variable..."

gcloud run services update $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --update-env-vars "CLOUD_TASKS_WORKER_URL=${SERVICE_URL}" \
    --project=$PROJECT_ID

echo "✅ Service updated with the correct worker URL. The new revision is being deployed."
echo "Starting health check..."

# --- 4. Health Check ---
HEALTH_URL="${SERVICE_URL}/health"
API_KEY="test_key_geocongo" # La clé API définie dans les variables d'environnement

MAX_ATTEMPTS=90 # Attendre au maximum 15 minutes (90 * 10s) pour laisser le temps aux modèles de charger
SLEEP_SECONDS=10

for (( i=1; i<=MAX_ATTEMPTS; i++ )); do
    echo "Attempt $i/$MAX_ATTEMPTS: Checking health at $HEALTH_URL..."
    # Utiliser curl pour interroger le point d'entrée /health avec la clé API
    # -s pour silencieux, -f pour échouer si le code HTTP n'est pas 2xx
    response=$(curl -s --fail-with-body -H "X-API-Key: $API_KEY" "$HEALTH_URL" || echo "failed")

    if [[ "$response" != "failed" && $(echo "$response" | grep '"status": "healthy"') ]]; then
        echo "✅ Service is healthy and running!"
        exit 0
    fi

    sleep $SLEEP_SECONDS
done

echo "❌ Service did not become healthy after $MAX_ATTEMPTS attempts."
exit 1
