#!/bin/bash
set -e

PROJECT_ID="geocongoai-api"
REGION="europe-west4"
BUCKET_NAME="geocongo-models-bucket" # Remplacez par le nom de votre bucket

# Configuration Vertex AI (Utilisation de GPU NVIDIA L4)
MACHINE_TYPE="g2-standard-4"
ACCELERATOR="type=nvidia-l4,count=1"

deploy_to_vertex() {
    MODEL_NAME=$1
    DIR_NAME=$2
    ARTIFACT_URI=$3

    echo "=========================================================="
    echo "🚀 Déploiement de $MODEL_NAME sur Vertex AI..."
    
    # 1. Build & Push Image
    IMAGE_URI="gcr.io/$PROJECT_ID/vertex-$MODEL_NAME"
    gcloud builds submit --tag $IMAGE_URI --project=$PROJECT_ID ./$DIR_NAME

    # 2. Upload Model to Vertex AI
    MODEL_ID=$(gcloud ai models upload \
        --project=$PROJECT_ID --region=$REGION \
        --display-name="$MODEL_NAME-model" \
        --container-image-uri=$IMAGE_URI \
        --artifact-uri=$ARTIFACT_URI \
        --format="value(model)")

    # 3. Create Endpoint
    ENDPOINT_ID=$(gcloud ai endpoints create \
        --project=$PROJECT_ID --region=$REGION \
        --display-name="$MODEL_NAME-endpoint" \
        --format="value(name)")

    # 4. Deploy Model to Endpoint (Cela prend ~10 minutes par modèle)
    echo "⏳ Lancement du déploiement sur l'endpoint (patientez)..."
    gcloud ai endpoints deploy-model $ENDPOINT_ID \
        --project=$PROJECT_ID --region=$REGION \
        --model=$MODEL_ID \
        --display-name="$MODEL_NAME-deployment" \
        --machine-type=$MACHINE_TYPE \
        --accelerator=$ACCELERATOR
}

deploy_to_vertex "prithvi" "vertex_ai_prithvi" "gs://$BUCKET_NAME/prithvi"
deploy_to_vertex "sam" "vertex_ai_sam" "gs://$BUCKET_NAME/sam2"
deploy_to_vertex "landcover" "vertex_ai_landcover" "gs://$BUCKET_NAME/landcover"

echo "✅ Tous les modèles Vertex AI sont déployés ! Regardez dans votre console Google Cloud (Vertex AI > Endpoints) pour récupérer les IDs."