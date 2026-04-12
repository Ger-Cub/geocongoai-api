import torch
import os
import rasterio
import tempfile
import uuid
import shutil
import hashlib
import time
from typing import List
import numpy as np
import ee
import zipfile
import requests
import io

# Importation de l'architecture Prithvi depuis transformers
from transformers import AutoImageProcessor, SegformerForSemanticSegmentation

from google.cloud import aiplatform
from google.cloud import storage

from ultralytics import SAM

class AIService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_dir = os.getenv("MODELS_DIR", "./models")
        self.satellite_cache_dir = os.path.join(self.models_dir, "satellite_cache")
        os.makedirs(self.satellite_cache_dir, exist_ok=True)

        self.sam2_path = os.path.join(self.models_dir, "sam2/sam2_l.pt")
        self.landcover_path = os.path.join(self.models_dir, "landcover/segformer-b0-finetuned-ade-512-512")
        
        # --- Configuration Vertex AI pour Prithvi ---
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION")
        self.gcs_bucket_name = os.getenv("MODELS_BUCKET")

        # IDs for the Vertex AI Models (Non plus les Endpoints)
        self.prithvi_model_id = os.getenv("VERTEX_PRITHVI_MODEL_ID")
        self.sam_model_id = os.getenv("VERTEX_SAM_MODEL_ID")
        self.landcover_model_id = os.getenv("VERTEX_LANDCOVER_MODEL_ID")
        
        if self.project_id and self.location:
            aiplatform.init(project=self.project_id, location=self.location)
            print("GCP AI Platform client initialized.")
            
            # Initialisation de Google Earth Engine avec le même projet GCP
            try:
                ee.Initialize(project=self.project_id)
                print("🌍 Google Earth Engine initialized successfully.")
            except Exception as e:
                print(f"⚠️ Earth Engine initialization failed (API might not be enabled or authenticated): {e}")
            
        # All models are now externalized, no local loading needed.
        self.prithvi_model = None 
        self.sam_model = None
        self.landcover_model = None
        print("AI Service initialized. All model inferences are delegated to Vertex AI Batch Jobs.")
        if not all([self.prithvi_model_id, self.sam_model_id, self.landcover_model_id]):
            print("⚠️ WARNING: One or more Vertex AI model IDs are not set.")

    def cleanup_cache(self, max_age_days: int = 30):
        """
        Removes cached files older than a specified number of days.
        This is a blocking I/O operation.
        """
        print(f"Running cache cleanup. Deleting files older than {max_age_days} days...")
        now = time.time()
        cutoff = now - (max_age_days * 86400) # 86400 seconds in a day
        files_deleted = 0
        try:
            for filename in os.listdir(self.satellite_cache_dir):
                file_path = os.path.join(self.satellite_cache_dir, filename)
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    files_deleted += 1
            print(f"✅ Cache cleanup complete. Deleted {files_deleted} files.")
        except Exception as e:
            print(f"⚠️ An error occurred during cache cleanup: {e}")

    def clear_all_cache(self) -> int:
        """
        Removes ALL files from the satellite cache directory.
        This is a blocking I/O operation.
        """
        print("🔥 Clearing all files from satellite cache...")
        files_deleted = 0
        try:
            for filename in os.listdir(self.satellite_cache_dir):
                file_path = os.path.join(self.satellite_cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_deleted += 1
            print(f"✅ Cache clear complete. Deleted {files_deleted} files.")
            return files_deleted
        except Exception as e:
            print(f"⚠️ An error occurred during cache clearing: {e}")
            raise e

    async def fetch_satellite_data(self, bbox: List[float], time_range: str = "2023-01-01/2023-12-31", analysis_type: str = None) -> str:
        """
        Searches and downloads Sentinel-2 harmonized data using Google Earth Engine.
        GEE handles mosaicking and cloud masking server-side.
        """
        print(f"Searching for satellite data in bbox {bbox} via Earth Engine...")

        # Mapping des bandes Sentinel-2 sur Earth Engine
        if analysis_type == 'landcover':
            bands = ['B4', 'B3', 'B2'] # RGB (Red, Green, Blue)
        else:
            # Bandes Prithvi: Blue, Green, Red, NIR, SWIR1, SWIR2
            bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'] 

        cache_key_str = f"{bbox}-{time_range}-{','.join(bands)}"
        cache_filename = hashlib.sha256(cache_key_str.encode()).hexdigest() + ".tif"
        cached_path = os.path.join(self.satellite_cache_dir, cache_filename)

        if os.path.exists(cached_path):
            print(f"✅ Cache hit! Using cached satellite data: {cached_path}")
            temp_dir = tempfile.mkdtemp(prefix="geocongo_cached_")
            temp_path = os.path.join(temp_dir, os.path.basename(cached_path))
            shutil.copy(cached_path, temp_path)
            return temp_path, temp_dir

        print("⚠️ Cache miss. Fetching optimized image from Google Earth Engine...")
        
        # Créer la géométrie GEE
        region = ee.Geometry.BBox(bbox[0], bbox[1], bbox[2], bbox[3])
        
        # Créer le composite d'images (Mosaïque avec un minimum de nuages)
        start_date, end_date = time_range.split('/')
        collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                      .filterBounds(region)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
                      .sort("CLOUDY_PIXEL_PERCENTAGE"))

        # Prendre la meilleure image et sélectionner uniquement les bandes requises
        image = collection.first().select(bands)
        
        # Générer l'URL de téléchargement direct depuis les serveurs de Google
        try:
            url = image.getDownloadURL({
                'scale': 10,
                'crs': 'EPSG:4326',
                'region': region,
                'format': 'GEO_TIFF'
            })
        except Exception as e:
            raise Exception(f"Failed to query Earth Engine. Is the region too large? Error: {e}")

        temp_dir = tempfile.mkdtemp(prefix="geocongo_")
        download_path = os.path.join(temp_dir, "gee_download.tif")

        # Télécharger et extraire. GEE envoie un ZIP contenant le(s) raster(s)
        response = requests.get(url)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            extracted_tifs = [f for f in z.namelist() if f.endswith('.tif')]
            z.extractall(temp_dir)
            # GEE consolide souvent le tout dans un seul "download.tif" avec les multiples bandes
            source_tif = os.path.join(temp_dir, extracted_tifs[0])
            shutil.move(source_tif, download_path)

        print(f"Saving downloaded file to cache: {cached_path}")
        shutil.copy(download_path, cached_path)
        print(f"Data saved to {download_path}")

        return download_path, temp_dir

    async def _call_vertex_batch_prediction(self, model_id: str, sat_data_path: str, output_raster_path: str, analysis_type: str):
        """
        Utilise Vertex AI Batch Prediction. 
        La machine (GPU) est allumée uniquement pour la durée du calcul.
        """
        print(f"Lancement du Batch Job pour {analysis_type} (Model: {model_id})...")
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.gcs_bucket_name)
        
        input_blob_name = f"tmp_inputs/{uuid.uuid4()}.tif"
        output_prefix = f"tmp_outputs/{uuid.uuid4()}"
        
        input_blob = bucket.blob(input_blob_name)
        input_blob.upload_from_filename(sat_data_path)
        
        input_uri = f"gs://{self.gcs_bucket_name}/{input_blob_name}"
        output_uri_prefix = f"gs://{self.gcs_bucket_name}/{output_prefix}"
        
        model = aiplatform.Model(model_id)
        
        # Création du job. 'sync=True' permet d'attendre la fin avant de continuer.
        batch_job = model.batch_predict(
            job_display_name=f"geocongo_{analysis_type}_{uuid.uuid4()}",
            gcs_source=input_uri,
            gcs_destination_output_uri_prefix=output_uri_prefix,
            machine_type="g2-standard-4",
            accelerator_type="NVIDIA_L4",
            accelerator_count=1,
            sync=True 
        )

        # Récupération du fichier dans le dossier de sortie généré par Vertex
        blobs = list(bucket.list_blobs(prefix=output_prefix))
        for blob in blobs:
            if blob.name.endswith(".tif"):
                blob.download_to_filename(output_raster_path)
                blob.delete()
                break
        
        input_blob.delete()
        print(f"✅ Batch Job terminé. Résultat sauvegardé dans {output_raster_path}")

    async def run_inference(self, bbox: List[float], analysis_type: str) -> str:
        """
        Runs inference based on requested analysis type.
        1. Fetches real satellite data.
        2. Runs Prithvi-EO-2.0 or SAM 2 (Ultralytics).
        3. Returns the path to the resulting raster.
        """
        sat_data_path, temp_dir = None, None
        try:
            # 1. Fetch satellite data into a temporary directory
            sat_data_path, temp_dir = await self.fetch_satellite_data(bbox, analysis_type=analysis_type)

            # 2. Inference logic
            output_raster = os.path.join(temp_dir, f"inference_{analysis_type}_{uuid.uuid4()}.tif")

            print(f"Running {analysis_type} inference on {sat_data_path}...")

            # Logique d'inférence pour les différents types d'analyse
            if analysis_type in ['minéraux', 'mines']:
                await self._call_vertex_batch_prediction(self.prithvi_model_id, sat_data_path, output_raster, analysis_type)

            elif analysis_type == 'failles':
                await self._call_vertex_batch_prediction(self.sam_model_id, sat_data_path, output_raster, analysis_type)

            elif analysis_type == 'landcover':
                await self._call_vertex_batch_prediction(self.landcover_model_id, sat_data_path, output_raster, analysis_type)

            else:
                # Si aucun modèle n'est disponible ou si le type d'analyse n'est pas géré
                raise NotImplementedError(f"Analysis type '{analysis_type}' is not implemented or its model is not loaded.")

            return output_raster
        except Exception as e:
            print(f"❌ An error occurred during AI inference: {e}")
            # Remonter l'exception pour que le handler de FastAPI la capture
            raise e
        finally:
            # Nettoyage du répertoire temporaire et de son contenu
            if temp_dir and os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir)
