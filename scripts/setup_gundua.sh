#!/bin/bash
set -e

# Configuration Gundua AI
PROJECT_ID="gundua-ai"
ACCOUNT="it.servicecemgoma@gmail.com"
REGION="europe-west4"
BUCKET_NAME="gundua-ai-models-storage"
SERVICE_ACCOUNT_NAME="gundua-worker-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🛠 Configuration du projet Google Cloud : $PROJECT_ID ($ACCOUNT)"
echo "----------------------------------------------------------"

# 1. Connexion au compte
echo "🔐 Connexion au compte..."
gcloud config set account $ACCOUNT
gcloud config set project $PROJECT_ID

# 2. Activation des APIs nécessaires
echo "🔌 Activation des APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    storage-api.googleapis.com \
    storage-component.googleapis.com \
    cloudtasks.googleapis.com \
    sqladmin.googleapis.com

# 3. Création du Bucket de stockage pour les modèles
echo "🪣 Création du bucket $BUCKET_NAME..."
if ! gsutil ls -b gs://$BUCKET_NAME > /dev/null 2>&1; then
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo "✅ Bucket créé."
else
    echo "ℹ️ Le bucket existe déjà."
fi

# 4. Création du compte de service worker
echo "👤 Création du compte de service $SERVICE_ACCOUNT_NAME..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL > /dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Gundua AI Worker Service Account"
    echo "✅ Compte de service créé."
else
    echo "ℹ️ Le compte de service existe déjà."
fi

# 5. Attribution des rôles
echo "🔑 Attribution des rôles..."
# Role pour invoquer Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"

# Role pour lire le stockage
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

# Role pour Cloud Tasks
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudtasks.enqueuer"

# 6. Initialisation des modèles (Download from HF -> Upload to GCS)
echo "🧠 Initialisation des modèles d'IA..."
export GCS_BUCKET=$BUCKET_NAME
python3 scripts/init_models.py

echo "=========================================================="
echo "✅ CONFIGURATION TERMINÉE"
echo "Projet : $PROJECT_ID"
echo "Bucket : gs://$BUCKET_NAME"
echo "SA     : $SERVICE_ACCOUNT_EMAIL"
echo "=========================================================="
echo "💡 Prochaine étape :"
echo "1. Lancez scripts/deploy.sh"
