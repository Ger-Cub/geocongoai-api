import os
import torch
import rasterio
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from transformers import AutoImageProcessor, MaskedAutoencoderForViT
from google.cloud import storage

app = FastAPI()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Sur Vertex AI, AIP_STORAGE_URI pointe vers le dossier du modèle fourni lors de la création
MODEL_DIR = os.environ.get("AIP_STORAGE_URI", "/app/models/prithvi")

processor = None
model = None

@app.on_event("startup")
async def load_model():
    global processor, model
    print(f"Loading Prithvi model from {MODEL_DIR} on {DEVICE}...")
    try:
        processor = AutoImageProcessor.from_pretrained("HuggingFaceM4/prithvi-eo-v2")
        # Assurez-vous que le fichier Prithvi_EO_V2_600M_TL.pt est à la racine de MODEL_DIR
        model_file = os.path.join(MODEL_DIR, "Prithvi_EO_V2_600M_TL.pt")
        model = MaskedAutoencoderForViT.from_pretrained(model_file, ignore_mismatched_sizes=True)
        model.to(DEVICE)
        model.eval()
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

@app.get("/health")
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    return {"status": "healthy"}

@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    instances = body.get("instances", [])
    if not instances:
        raise HTTPException(status_code=400, detail="No instances provided.")

    instance = instances[0]
    input_gcs_uri = instance.get("input_uri")
    output_gcs_uri = instance.get("output_uri")

    if not input_gcs_uri or not output_gcs_uri:
        raise HTTPException(status_code=400, detail="input_uri and output_uri must be provided.")

    storage_client = storage.Client()
    
    # Téléchargement de l'entrée depuis GCS
    input_bucket = storage_client.bucket(input_gcs_uri.split("/")[2])
    input_blob = input_bucket.blob("/".join(input_gcs_uri.split("/")[3:]))
    local_input_path = "/tmp/input.tif"
    input_blob.download_to_filename(local_input_path)

    # Inférence Prithvi
    local_output_path = "/tmp/output.tif"
    with rasterio.open(local_input_path) as src:
        image_array = src.read()
        src_profile = src.profile

    inputs = processor(images=image_array, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = model(**inputs)

    classification_map = torch.argmax(outputs.logits, dim=1).squeeze()
    classification_map_np = classification_map.cpu().numpy().astype(rasterio.uint8)

    dst_profile = src_profile.copy()
    dst_profile.update({'count': 1, 'dtype': 'uint8', 'compress': 'lzw'})

    with rasterio.open(local_output_path, 'w', **dst_profile) as dst:
        dst.write(classification_map_np, 1)

    # Upload du résultat sur GCS
    output_bucket = storage_client.bucket(output_gcs_uri.split("/")[2])
    output_blob = output_bucket.blob("/".join(output_gcs_uri.split("/")[3:]))
    output_blob.upload_from_filename(local_output_path)

    # Nettoyage
    os.remove(local_input_path)
    os.remove(local_output_path)

    return {"predictions": [{"status": "success", "output_uri": output_gcs_uri}]}