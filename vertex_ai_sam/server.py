import os
import torch
import rasterio
import numpy as np
import uuid
from fastapi import FastAPI, Request, HTTPException
from transformers import AutoImageProcessor, MaskedAutoencoderForViT, SegformerForSemanticSegmentation
from google.cloud import storage
from ultralytics import SAM

app = FastAPI()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# AIP_STORAGE_URI is provided by Vertex AI when deploying a model with artifact-uri
MODEL_DIR = os.environ.get("AIP_STORAGE_URI", "/app/models")
MODEL_TYPE = os.environ.get("MODEL_TYPE", "LANDCOVER") # Options: PRITHVI, SAM, LANDCOVER

processor = None
model = None

@app.on_event("startup")
async def load_model():
    global processor, model
    print(f"🚀 Loading {MODEL_TYPE} model from {MODEL_DIR} on {DEVICE}...")
    
    try:
        if MODEL_TYPE == "PRITHVI":
            # Expects Prithvi_EO_V2_600M_TL.pt in MODEL_DIR
            model_path = os.path.join(MODEL_DIR, "Prithvi_EO_V2_600M_TL.pt")
            # Fallback to current dir if not found (for local testing)
            if not os.path.exists(model_path):
                model_path = os.path.join("/app/models/prithvi", "Prithvi_EO_V2_600M_TL.pt")
            
            processor = AutoImageProcessor.from_pretrained("HuggingFaceM4/prithvi-eo-v2")
            model = MaskedAutoencoderForViT.from_pretrained(model_path, ignore_mismatched_sizes=True)
            
        elif MODEL_TYPE == "SAM":
            # Expects sam2_l.pt in MODEL_DIR
            model_path = os.path.join(MODEL_DIR, "sam2_l.pt")
            if not os.path.exists(model_path):
                 model_path = os.path.join("/app/models/sam2", "sam2_l.pt")
            
            model = SAM(model_path)
            
        elif MODEL_TYPE == "LANDCOVER":
            # Expects SegFormer files in MODEL_DIR
            model_path = MODEL_DIR
            if not os.path.exists(os.path.join(model_path, "config.json")):
                model_path = "/app/models/landcover/segformer-b0-finetuned-ade-512-512"
            
            processor = AutoImageProcessor.from_pretrained(model_path)
            model = SegformerForSemanticSegmentation.from_pretrained(model_path)
        
        if model and hasattr(model, 'to'):
            model.to(DEVICE)
            model.eval()
            
        print(f"✅ {MODEL_TYPE} model loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading {MODEL_TYPE} model: {e}")

@app.get("/health")
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    return {"status": "healthy", "model_type": MODEL_TYPE}

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
    
    # Download input from GCS
    input_bucket = storage_client.bucket(input_gcs_uri.split("/")[2])
    input_blob = input_bucket.blob("/".join(input_gcs_uri.split("/")[3:]))
    local_input_path = f"/tmp/{uuid.uuid4()}_input.tif"
    input_blob.download_to_filename(local_input_path)

    local_output_path = f"/tmp/{uuid.uuid4()}_output.tif"
    
    try:
        with rasterio.open(local_input_path) as src:
            image_array = src.read()
            src_profile = src.profile

        if MODEL_TYPE == "PRITHVI":
            inputs = processor(images=image_array, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
            classification_map = torch.argmax(outputs.logits, dim=1).squeeze()
            classification_map_np = classification_map.cpu().numpy().astype(rasterio.uint8)

        elif MODEL_TYPE == "SAM":
            results = model.predict(local_input_path, device=DEVICE)
            if not results or not results[0].masks:
                # Binaire vide si rien n'est détecté
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

        # Save result as GeoTIFF
        dst_profile = src_profile.copy()
        dst_profile.update({'count': 1, 'dtype': 'uint8', 'compress': 'lzw'})
        with rasterio.open(local_output_path, 'w', **dst_profile) as dst:
            dst.write(classification_map_np, 1)

        # Upload result to GCS
        output_bucket = storage_client.bucket(output_gcs_uri.split("/")[2])
        output_blob = output_bucket.blob("/".join(output_gcs_uri.split("/")[3:]))
        output_blob.upload_from_filename(local_output_path)

        return {"predictions": [{"status": "success", "output_uri": output_gcs_uri}]}

    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_input_path): os.remove(local_input_path)
        if os.path.exists(local_output_path): os.remove(local_output_path)