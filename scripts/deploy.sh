#!/bin/bash
set -e # Arrete le script en cas d'erreur

# Configuration
PROJECT_ID="geocongoai-api"
SERVICE_NAME="geocongoai-api"
REGION="europe-west4" # Region avec support GPU (Pays-Bas)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
FILESTORE_INSTANCE="geocongo-models-cache" # Nom de l'instance Filestore
FILESTORE_SHARE_NAME="models" # Nom du partage de fichiers dans Filestore

# 1. Get Filestore IP address
echo "Fetching Filestore IP address..."
FILESTORE_IP=$(gcloud filestore instances describe $FILESTORE_INSTANCE --project=$PROJECT_ID --zone=${REGION}-a --format="value(networks[0].ipAddresses[0])")
if [ -z "$FILESTORE_IP" ]; then
    echo "❌ Could not get Filestore IP. Make sure the instance '$FILESTORE_INSTANCE' exists in zone '${REGION}-a'."
    exit 1
fi

# 2. Build the Docker image using Cloud Build
echo "Building image $IMAGE_NAME..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID .

# 3. Deploy to Cloud Run with GPU and Filestore NFS Mount
echo "Deploying to Cloud Run with GPU (nvidia-l4) and Filestore NFS mount..."
gcloud beta run deploy $SERVICE_NAME \
    --project=$PROJECT_ID \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --cpu 4 \
    --memory 16Gi \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --execution-environment gen2 \
    --startup-cpu-boost \
    --timeout=600s \
    --add-volume=name=models-cache,type=nfs,location="${FILESTORE_IP}:/${FILESTORE_SHARE_NAME}" \
    --add-volume-mount=volume=models-cache,mount-path=/app/models \
    --set-env-vars "GEOCONGO_API_KEY=test_key_geocongo,DEVICE=gpu"

echo "✅ Deployment command sent. Waiting for the new revision to become healthy..."

# 4. Health Check
# Récupérer l'URL du service et la clé API pour le health check
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
HEALTH_URL="${SERVICE_URL}/health"
API_KEY="test_key_geocongo" # La clé API définie dans les variables d'environnement

MAX_ATTEMPTS=60 # Attendre au maximum 10 minutes (60 * 10s)
SLEEP_SECONDS=10

for (( i=1; i<=MAX_ATTEMPTS; i++ )); do
    echo "Attempt $i/$MAX_ATTEMPTS: Checking health at $HEALTH_URL..."
    # Utiliser curl pour interroger le point d'entrée /health avec la clé API
    # -s pour silencieux, -f pour échouer si le code HTTP n'est pas 2xx
    response=$(curl -s -f -H "X-API-Key: $API_KEY" "$HEALTH_URL" || echo "failed")

    if [[ "$response" != "failed" && $(echo "$response" | grep '"status": "healthy"') ]]; then
        echo "✅ Service is healthy and running!"
        exit 0
    fi
    
    sleep $SLEEP_SECONDS
done

echo "❌ Service did not become healthy after $MAX_ATTEMPTS attempts."
exit 1
