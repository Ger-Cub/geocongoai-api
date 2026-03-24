import os
from fastapi import FastAPI, Request
from google.cloud import storage

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    instances = body.get("instances", [])
    
    predictions = []
    storage_client = storage.Client()

    for instance in instances:
        input_uri = instance.get("input_uri")
        output_uri = instance.get("output_uri")
        
        # TODO: INSÉRER LA LOGIQUE D'INFÉRENCE PRITHVI (PyTorch) ICI.
        # En attendant, nous simulons l'inférence en copiant simplement le fichier d'entrée vers la sortie 
        # pour valider que la communication Cloud Run <-> Vertex AI fonctionne (pattern GCS-to-GCS).
        if input_uri and output_uri:
            input_bucket_name = input_uri.split("/")[2]
            input_blob_name = "/".join(input_uri.split("/")[3:])
            output_bucket_name = output_uri.split("/")[2]
            output_blob_name = "/".join(output_uri.split("/")[3:])
            
            source_bucket = storage_client.bucket(input_bucket_name)
            source_blob = source_bucket.blob(input_blob_name)
            destination_bucket = storage_client.bucket(output_bucket_name)
            
            source_bucket.copy_blob(source_blob, destination_bucket, output_blob_name)
            
        predictions.append({"status": "success", "output_uri": output_uri})
        
    return {"predictions": predictions}