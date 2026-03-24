#!/bin/bash
set -e

PROJECT_ID="geocongoai-api"
SERVICE_NAME="geocongoai-streamlit"
REGION="europe-west4"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ⚠️ REMPLACEZ CETTE VALEUR par l'URL générée lors du déploiement de votre API
API_URL="https://geocongoai-api-xxxxxx-ez.a.run.app"

echo "🚀 Construction de l'image Docker pour Streamlit..."
cat <<EOF > cloudbuild-streamlit.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$IMAGE_NAME', '-f', 'Dockerfile.streamlit', '.']
images:
- '$IMAGE_NAME'
EOF

gcloud builds submit --config cloudbuild-streamlit.yaml --project=$PROJECT_ID .

echo "🌍 Déploiement de Streamlit sur Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --project=$PROJECT_ID \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --cpu=1 \
    --memory=1Gi \
    --port=8501 \
    --set-env-vars "API_URL=${API_URL}"

echo "✅ Déploiement de l'interface terminé avec succès !"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'