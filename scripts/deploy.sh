#!/bin/bash
set -e

# =========================================================
# Configuration globale
# =========================================================
PROJECT_ID="geocongoai-api"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/geocongoai-api"
MODELS_BUCKET="geocongoai-models-storage"
WORKER_SA_EMAIL="geocongo-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# =========================================================
# Build de l'image Docker (unique pour tous les services)
# =========================================================
echo "🚧 Building Docker image: $IMAGE_NAME"
gcloud builds submit --tag "$IMAGE_NAME" --project="$PROJECT_ID" .

# =========================================================
# Fonction de déploiement des workers
# =========================================================
deploy_worker() {
    local SERVICE_NAME=$1
    local MODE=$2

    # Mapping MODE -> ressources
    case "$MODE" in
        landcover)
            CPU="2"
            MEMORY="4Gi"
            ;;
        detection)
            CPU="4"
            MEMORY="8Gi"
            ;;
        minerals)
            CPU="4"
            MEMORY="16Gi"
            ;;
        *)
            echo "❌ MODE inconnu: $MODE"
            exit 1
            ;;
    esac

    echo "----------------------------------------------------" >&2
    echo "🚀 Deploying Worker: $SERVICE_NAME" >&2
    echo "   Mode: $MODE | CPU: $CPU | Memory: $MEMORY" >&2
    echo "----------------------------------------------------" >&2

    gcloud beta run deploy "$SERVICE_NAME" \
        --project="$PROJECT_ID" \
        --image="$IMAGE_NAME" \
        --platform=managed \
        --region="$REGION" \
        --no-allow-unauthenticated \
        --cpu="$CPU" \
        --memory="$MEMORY" \
        --execution-environment=gen2 \
        --cpu-boost \
        --timeout=3600s \
        --port=8080 \
        --add-volume=name=models-volume,type=cloud-storage,bucket="${MODELS_BUCKET}" \
        --add-volume-mount=volume=models-volume,mount-path=/app/models \
        --set-env-vars="ENABLED_SERVICE=${MODE},DEVICE=cpu,GEOCONGO_API_KEY=test_key_geocongo,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},CLOUD_TASKS_QUEUE=geocongo-results-queue,CLOUD_TASKS_WORKER_SA_EMAIL=${WORKER_SA_EMAIL}" >&2

    WORKER_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --platform=managed \
        --region="$REGION" \
        --format='value(status.url)')

    echo "✅ $SERVICE_NAME deployed at: $WORKER_URL" >&2
    echo "$WORKER_URL"
}

# =========================================================
# Déploiement des Workers
# =========================================================
WORKER_LANDCOVER_URL=$(deploy_worker "geocongoai-landcover" "landcover")
WORKER_DETECTION_URL=$(deploy_worker "geocongoai-detection" "detection")
WORKER_MINERALS_URL=$(deploy_worker "geocongoai-minerals" "minerals")

# =========================================================
# Déploiement du Router (API principale)
# =========================================================
ROUTER_SERVICE_NAME="geocongoai-api"

echo "----------------------------------------------------"
echo "🚀 Deploying Router: $ROUTER_SERVICE_NAME"
echo "----------------------------------------------------"
echo "Workers linked:"
echo " - Landcover: $WORKER_LANDCOVER_URL"
echo " - Detection: $WORKER_DETECTION_URL"
echo " - Minerals:  $WORKER_MINERALS_URL"

gcloud run deploy "$ROUTER_SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --image="$IMAGE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --cpu="1" \
    --memory="1Gi" \
    --execution-environment=gen2 \
    --timeout=600s \
    --port=8080 \
    --set-env-vars="ENABLED_SERVICE=router,DEVICE=cpu,GEOCONGO_API_KEY=test_key_geocongo,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},CLOUD_TASKS_QUEUE=geocongo-results-queue,CLOUD_TASKS_WORKER_SA_EMAIL=${WORKER_SA_EMAIL},WORKER_URL_LANDCOVER=${WORKER_LANDCOVER_URL},WORKER_URL_DETECTION=${WORKER_DETECTION_URL},WORKER_URL_MINERALS=${WORKER_MINERALS_URL},CLOUD_TASKS_WORKER_URL=${WORKER_LANDCOVER_URL}"

# =========================================================
# Fin
# =========================================================
echo "----------------------------------------------------"
echo "✅ DEPLOYMENT COMPLET AVEC SUCCÈS"
echo "Main API URL:"
gcloud run services describe "$ROUTER_SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --format='value(status.url)'
echo "----------------------------------------------------"
