#!/bin/bash
set -e

PROJECT_ID="geocongoai-api"
REGION="europe-west4"
BUCKET_NAME="geocongoai-models-storage" # Résolu: Utilise le bucket existant

# Configuration Vertex AI (Utilisation de GPU NVIDIA L4)
MACHINE_TYPE="g2-standard-4"
ACCELERATOR="type=nvidia-l4,count=1"

deploy_to_vertex() {
    MODEL_NAME=$1
    DIR_NAME=$2
    ARTIFACT_URI=$3
    MODEL_TYPE_EV=$4

    echo "=========================================================="
    echo "🚀 Déploiement de $MODEL_NAME sur Vertex AI..."
    
    # 1. Build & Push Image
    IMAGE_URI="gcr.io/$PROJECT_ID/vertex-$MODEL_NAME"
    gcloud builds submit --tag $IMAGE_URI --project=$PROJECT_ID ./$DIR_NAME

    # 2. Upload Model to Vertex AI
    # On spécifie l'artifact-uri où se trouvent les fichiers de poids
    # et la variable d'environnement MODEL_TYPE via --container-env-vars
    MODEL_ID=$(gcloud ai models upload \
        --project=$PROJECT_ID --region=$REGION \
        --display-name="$MODEL_NAME-model" \
        --container-image-uri=$IMAGE_URI \
        --artifact-uri=$ARTIFACT_URI \
        --container-env-vars="MODEL_TYPE=$MODEL_TYPE_EV" \
        --container-health-route="/health" \
        --format="value(model)")

    # 3. Create Endpoint
    ENDPOINT_ID=$(gcloud ai endpoints create \
        --project=$PROJECT_ID --region=$REGION \
        --display-name="$MODEL_NAME-endpoint" \
        --format="value(name)")

    # 4. Deploy Model to Endpoint
    echo "⏳ Lancement du déploiement sur l'endpoint (patientez)..."
    gcloud ai endpoints deploy-model $ENDPOINT_ID \
        --project=$PROJECT_ID --region=$REGION \
        --model=$MODEL_ID \
        --display-name="$MODEL_NAME-deployment" \
        --machine-type=$MACHINE_TYPE \
        --accelerator=$ACCELERATOR
    
    echo "✅ Endpoint ID for $MODEL_NAME: $ENDPOINT_ID"
}

# Note: Les chemins dans le bucket sont sous 'models/'
deploy_to_vertex "prithvi" "vertex_ai_generic" "gs://$BUCKET_NAME/models/prithvi" "PRITHVI"
deploy_to_vertex "sam" "vertex_ai_generic" "gs://$BUCKET_NAME/models/sam2" "SAM"
# deploy_to_vertex "landcover" "vertex_ai_generic" "gs://$BUCKET_NAME/models/landcover/segformer-b0-finetuned-ade-512-512" "LANDCOVER"

echo "✅ Tous les modèles Vertex AI sont lancés ! Notez bien les Endpoint IDs ci-dessus."