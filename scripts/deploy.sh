#!/bin/bash
set -e # Arrete le script en cas d'erreur

# Configuration
PROJECT_ID="geocongoai-api"
SERVICE_NAME="geocongoai-api"
REGION="europe-west4" # Region avec support GPU (Pays-Bas)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
BUCKET_NAME="geocongoai-models-storage"

# Initialisation du projet (Crucial pour Cloud Shell)
echo "Configuration du projet $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# 2. Create the bucket for models
echo "Creating GCS bucket gs://$BUCKET_NAME..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME || echo "Bucket already exists"

# 3. Build the Docker image using Cloud Build
echo "Building image $IMAGE_NAME..."
gcloud builds submit --tag $IMAGE_NAME .

# 4. Deploy to Cloud Run with GPU and GCS Mount
echo "Deploying to Cloud Run with GPU (nvidia-l4) and GCS FUSE mount..."
# Note: Using nvidia-l4 as it's supported in europe-west4
# Note: Mounting GCS bucket to /app/models so the code finds the models automatically
gcloud beta run deploy $SERVICE_NAME \
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
    --timeout 600 \
    --add-volume=name=models,type=cloud-storage,bucket=$BUCKET_NAME \
    --add-volume-mount=volume=models,mount-path=/app/models \
    --set-env-vars "GCS_BUCKET=$BUCKET_NAME,GEOCONGO_API_KEY=test_key_geocongo,DEVICE=gpu"

echo "✅ Deployment complete!"
