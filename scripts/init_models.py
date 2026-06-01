import os
import torch
from terratorch import BACKBONE_REGISTRY
from google.cloud import storage
import subprocess

def upload_to_gcs(local_path, bucket_name, gcs_path):
    print(f"⬆️ Uploading {local_path} to gs://{bucket_name}/{gcs_path}...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    print(f"✅ Uploaded to {gcs_path}")

def download_and_upload_prithvi(bucket_name):
    model_name = "prithvi_eo_v2_300"
    print(f"📥 Downloading Prithvi model: {model_name}...")
    
    # This will download the model to the local cache
    model = BACKBONE_REGISTRY.build(
        model_name,
        num_frames=1,
        in_chans=6,
        pretrained=True
    )
    
    local_path = f"/tmp/{model_name}.pt"
    torch.save(model.state_dict(), local_path)
    
    upload_to_gcs(local_path, bucket_name, f"models/{model_name}.pt")
    os.remove(local_path)

if __name__ == "__main__":
    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        print("❌ Error: GCS_BUCKET environment variable not set.")
        exit(1)
        
    print(f"🚀 Initializing models for bucket: {bucket}")
    try:
        # Check for dependencies
        import terratorch
        import google.cloud.storage
        
        download_and_upload_prithvi(bucket)
    except ImportError as e:
        print(f"❌ Error: Missing dependency. Please run: pip install terratorch google-cloud-storage")
        print(f"Details: {e}")
    except Exception as e:
        print(f"❌ Error during model initialization: {e}")
