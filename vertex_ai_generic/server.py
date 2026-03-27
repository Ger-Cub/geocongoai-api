import os
import torch
import rasterio
import numpy as np
import uuid
from fastapi import FastAPI, Request, HTTPException
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation, MaskedAutoencoderForViT
from google.cloud import storage
from ultralytics import SAM

app = FastAPI()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# AIP_STORAGE_URI is provided by Vertex AI when deploying a model with artifact-uri
MODEL_DIR = os.environ.get("AIP_STORAGE_URI")
MODEL_TYPE = os.environ.get("MODEL_TYPE") # PRITHVI, SAM, or LANDCOVER

processor = None
model = None

@app.on_event("startup")
async def load_model():
    global processor, model
    
    if not MODEL_TYPE or not MODEL_DIR:
        raise RuntimeError("MODEL_TYPE and AIP_STORAGE_URI must be set as environment variables.")

    print(f"🚀 Loading {MODEL_TYPE} model from {MODEL_DIR} on {DEVICE}...")
    
    try:
        if MODEL_TYPE == "PRITHVI":
            processor = AutoImageProcessor.from_pretrained("HuggingFaceM4/prithvi-eo-v2")
            model = MaskedAutoencoderForViT.from_pretrained(MODEL_DIR, ignore_mismatched_sizes=True)
            
        elif MODEL_TYPE == "SAM":
            storage_client = storage.Client()
            bucket_name = MODEL_DIR.split("/")[2]
            prefix = "/".join(MODEL_DIR.split("/")[3:])
            bucket = storage_client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            model_blob = None
            for blob in blobs:
                if blob.name.endswith(".pt"):
                    model_blob = blob
                    break
            
            if not model_blob:
                raise RuntimeError(f"No .pt model file found in {MODEL_DIR}")

            # Create a temporary directory to download the model
            temp_dir = "/tmp/sam_model"
            os.makedirs(temp_dir, exist_ok=True)
            model_path = os.path.join(temp_dir, model_blob.name.split("/")[-1])
            model_blob.download_to_filename(model_path)
            
            model = SAM(model_path)
            
        elif MODEL_TYPE == "LANDCOVER":
            processor = AutoImageProcessor.from_pretrained(MODEL_DIR)
            model = AutoModelForSemanticSegmentation.from_pretrained(MODEL_DIR)
        
        else:
            raise ValueError(f"Unsupported MODEL_TYPE: {MODEL_TYPE}")

        if hasattr(model, 'to'):
            model.to(DEVICE)
            model.eval()
            
        print(f"✅ {MODEL_TYPE} model loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading {MODEL_TYPE} model: {e}")
        raise e

@app.get(os.environ.get("AIP_HEALTH_ROUTE", "/health"))
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    return {"status": "healthy", "model_type": MODEL_TYPE}

@app.post(os.environ.get("AIP_PREDICT_ROUTE", "/predict"))
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
    
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    
    local_input_path = os.path.join(temp_dir, f"{uuid.uuid4()}_input.tif")
    local_output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_output.tif")
    
    try:
        # Download input from GCS
        input_bucket_name = input_gcs_uri.split("/")[2]
        input_blob_name = "/".join(input_gcs_uri.split("/")[3:])
        input_bucket = storage_client.bucket(input_bucket_name)
        input_blob = input_bucket.blob(input_blob_name)
        input_blob.download_to_filename(local_input_path)

        with rasterio.open(local_input_path) as src:
            image_array = src.read()
            src_profile = src.profile

        # --- Prediction logic based on model type ---
        if MODEL_TYPE == "PRITHVI":
            inputs = processor(images=image_array, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
            # Post-process for Prithvi
            classification_map = torch.argmax(outputs.logits, dim=1).squeeze()
            classification_map_np = classification_map.cpu().numpy().astype(rasterio.uint8)

        elif MODEL_TYPE == "SAM":
            # For SAM, we need to provide a point or box, this needs to be adapted
            # For now, let's assume the goal is to segment everything.
            results = model.predict(local_input_path, device=DEVICE)
            if not results or not results[0].masks:
                classification_map_np = np.zeros((src_profile['height'], src_profile['width']), dtype=np.uint8)
            else:
                merged_mask = torch.sum(results[0].masks.data, dim=0).clamp(0, 1)
                classification_map_np = merged_mask.cpu().numpy().astype(rasterio.uint8)

        elif MODEL_TYPE == "LANDCOVER":
            inputs = processor(images=image_array, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
            logits = outputs.logits.cpu()
            upsampled_logits = torch.nn.functional.interpolate(logits, size=image_array.shape[1:], mode="bilinear", align_corners=False)
            classification_map = upsampled_logits.argmax(dim=1).squeeze()
            classification_map_np = classification_map.numpy().astype(rasterio.uint8)
            
        else:
             raise ValueError(f"Unsupported MODEL_TYPE for prediction: {MODEL_TYPE}")


        # Save result as GeoTIFF
        dst_profile = src_profile.copy()
        dst_profile.update({'count': 1, 'dtype': 'uint8', 'compress': 'lzw'})
        with rasterio.open(local_output_path, 'w', **dst_profile) as dst:
            dst.write(classification_map_np, 1)

        # Upload result to GCS
        output_bucket_name = output_gcs_uri.split("/")[2]
        output_blob_name = "/".join(output_gcs_uri.split("/")[3:])
        output_bucket = storage_client.bucket(output_bucket_name)
        output_blob = output_bucket.blob(output_blob_name)
        output_blob.upload_from_filename(local_output_path)

        return {"predictions": [{"status": "success", "output_uri": output_gcs_uri}]}

    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_input_path): os.remove(local_input_path)
        if os.path.exists(local_output_path): os.remove(local_output_path)
