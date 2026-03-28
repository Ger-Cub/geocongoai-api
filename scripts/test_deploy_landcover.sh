#!/bin/bash
set -e

PROJECT_ID="geocongoai-api"
REGION="europe-west4"
BUCKET_NAME="geocongoai-models-storage"
MACHINE_TYPE="g2-standard-4"
ACCELERATOR="type=nvidia-l4,count=1"

MODEL_NAME="landcover-test"
DIR_NAME="vertex_ai_generic"
ARTIFACT_URI="gs://$BUCKET_NAME/models/landcover/segformer-b0-finetuned-ade-512-512"
MODEL_TYPE_EV="LANDCOVER"
IMAGE_URI="gcr.io/$PROJECT_ID/vertex-$MODEL_NAME:latest"

echo "🚀 Building and pushing image..."
gcloud builds submit --tag $IMAGE_URI --project=$PROJECT_ID ./$DIR_NAME

echo "📤 Uploading model to Vertex AI..."
MODEL_ID=$(gcloud ai models upload \
    --project=$PROJECT_ID --region=$REGION \
    --display-name="$MODEL_NAME-model" \
    --container-image-uri=$IMAGE_URI \
    --artifact-uri=$ARTIFACT_URI \
    --container-env-vars="MODEL_TYPE=$MODEL_TYPE_EV" \
    --format="value(model)")

echo "📌 Creating endpoint..."
ENDPOINT_ID=$(gcloud ai endpoints create \
    --project=$PROJECT_ID --region=$REGION \
    --display-name="$MODEL_NAME-endpoint" \
    --format="value(name)")

echo "⏳ Deploying model to endpoint..."
gcloud ai endpoints deploy-model $ENDPOINT_ID \
    --project=$PROJECT_ID --region=$REGION \
    --model=$MODEL_ID \
    --display-name="$MODEL_NAME-deployment" \
    --machine-type=$MACHINE_TYPE \
    --accelerator=$ACCELERATOR

echo "✅ Deployment complete! Endpoint ID: $ENDPOINT_ID"
