import os
from google.cloud import storage
from pathlib import Path

def download_model_from_gcs(bucket_name: str, model_name: str, destination_path: str):
    """
    Télécharge les poids d'un modèle depuis un bucket GCS vers un chemin local.
    """
    print(f"📥 Downloading model {model_name} from bucket {bucket_name}...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # On assume que les modèles sont organisés dans un dossier 'models/' dans le bucket
    blob = bucket.blob(f"models/{model_name}")
    
    # Créer le dossier de destination si nécessaire
    Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
    
    blob.download_to_filename(destination_path)
    print(f"✅ Model downloaded to {destination_path}")

def ensure_model_available(model_name: str, local_path: str):
    """
    Vérifie si le modèle est présent localement, sinon tente de le récupérer via GCS
    si MODEL_BUCKET est configuré.
    """
    if os.path.exists(local_path):
        return True
        
    bucket_name = os.getenv("MODEL_BUCKET")
    if bucket_name:
        try:
            download_model_from_gcs(bucket_name, model_name, local_path)
            return True
        except Exception as e:
            print(f"⚠️ Failed to download from GCS: {e}")
            return False
    return False
