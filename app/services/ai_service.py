import torch
import os
import rasterio
import tempfile
import uuid
import shutil
import hashlib
import time
from typing import List
from pystac_client import Client
import numpy as np
from odc.stac import stac_load

# Importation de l'architecture Prithvi depuis transformers
from transformers import AutoImageProcessor, MaskedAutoencoderForViT, SegformerForSemanticSegmentation
from ultralytics import SAM

class AIService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_dir = "/app/models"
        self.satellite_cache_dir = os.path.join(self.models_dir, "satellite_cache")
        os.makedirs(self.satellite_cache_dir, exist_ok=True)

        self.prithvi_path = os.path.join(self.models_dir, "prithvi/Prithvi_EO_V2_600M_TL.pt")
        self.sam2_path = os.path.join(self.models_dir, "sam2/sam2_l.pt")
        self.landcover_path = os.path.join(self.models_dir, "landcover/segformer-b0-finetuned-ade-512-512")
        
        # --- Lazy Loading Initialization ---
        # Models are initialized to None and loaded only when needed
        self.prithvi_model = None
        self.prithvi_processor = None
        
        self.sam_model = None
        
        self.landcover_model = None
        self.landcover_processor = None

        print(f"AI Service initialized on {self.device} (Lazy Loading enabled)")

    def _load_prithvi(self):
        """Loads Prithvi model if not already loaded"""
        if self.prithvi_model is not None:
            return

        if os.path.exists(self.prithvi_path):
            try:
                print(f"Loading Prithvi model from {self.prithvi_path}...")
                self.prithvi_processor = AutoImageProcessor.from_pretrained("HuggingFaceM4/prithvi-eo-v2")
                self.prithvi_model = MaskedAutoencoderForViT.from_pretrained(self.prithvi_path, ignore_mismatched_sizes=True)
                self.prithvi_model.to(self.device)
                print("Prithvi model loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading Prithvi model: {e}")
                self.prithvi_model = False # Avoid retrying
        else:
            print(f"Warning: Prithvi model NOT found at {self.prithvi_path}")
            self.prithvi_model = False

    def _load_sam(self):
        """Loads SAM 2 model if not already loaded"""
        if self.sam_model is not None:
            return

        if os.path.exists(self.sam2_path):
            try:
                print(f"Loading SAM 2 from {self.sam2_path}...")
                self.sam_model = SAM(self.sam2_path)
                print("SAM 2 loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading SAM 2: {e}")
                print("Continuing with AI Service in Simulation Mode for SAM 2.")
                self.sam_model = False
        else:
            print(f"Warning: SAM 2 model NOT found at {self.sam2_path}")
            self.sam_model = False

    def _load_landcover(self):
        """Loads Landcover model if not already loaded"""
        if self.landcover_model is not None:
            return

        if os.path.exists(self.landcover_path):
            try:
                print(f"Loading Landcover model from {self.landcover_path}...")
                self.landcover_processor = AutoImageProcessor.from_pretrained(self.landcover_path)
                self.landcover_model = SegformerForSemanticSegmentation.from_pretrained(self.landcover_path)
                self.landcover_model.to(self.device)
                print("Landcover model loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading Landcover model: {e}")
                self.landcover_model = False
        else:
            print(f"Warning: Landcover model NOT found at {self.landcover_path}")
            self.landcover_model = False

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
        Searches and downloads Sentinel-2 multispectral data for a given Bbox using Microsoft Planetary Computer.
        Returns the path to the downloaded GeoTIFF.
        """
        print(f"Searching for satellite data in bbox {bbox}...")

        # Sélectionne les bandes en fonction du type d'analyse pour optimiser le téléchargement
        if analysis_type == 'landcover':
            bands = ['red', 'green', 'blue']
        else:
            # Bandes nécessaires pour Prithvi
            bands = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22']

        # 1. Générer une clé de cache unique basée sur les paramètres de la requête
        cache_key_str = f"{bbox}-{time_range}-{','.join(bands)}"
        cache_filename = hashlib.sha256(cache_key_str.encode()).hexdigest() + ".tif"
        cached_path = os.path.join(self.satellite_cache_dir, cache_filename)

        # 2. Vérifier si la donnée est déjà en cache
        if os.path.exists(cached_path):
            print(f"✅ Cache hit! Using cached satellite data: {cached_path}")
            # Créer un répertoire temporaire et y copier le fichier pour une gestion cohérente
            temp_dir = tempfile.mkdtemp(prefix="geocongo_cached_")
            temp_path = os.path.join(temp_dir, os.path.basename(cached_path))
            shutil.copy(cached_path, temp_path)
            return temp_path, temp_dir

        print("⚠️ Cache miss. Fetching data from Planetary Computer...")
        catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=time_range,
            query={"eo:cloud_cover": {"lt": 10}},
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}]
        )

        items = list(search.get_items())
        if not items:
            raise Exception("No suitable satellite images found for the given area and time range.")

        # Picking the best item (lowest cloud cover)
        item = items[0]
        print(f"Found best image: {item.id} with {item.properties['eo:cloud_cover']}% cloud cover")

        # Création d'un chemin de fichier unique dans le répertoire temporaire fourni
        temp_dir = tempfile.mkdtemp(prefix="geocongo_")
        download_path = os.path.join(temp_dir, f"sentinel_{item.id}.tif")

        print(f"Loading bands {bands} using odc-stac...")
        ds = stac_load(
            [item],
            bands=bands,
            bbox=bbox,
            resolution=10,
            chunks={'x': 2048, 'y': 2048} # Active le traitement parallèle par blocs
        )

        # Sauvegarder le dataset chargé en tant que GeoTIFF
        ds.to_array(dim="bands").rio.to_raster(download_path, tiled=True, lock=True)

        # 3. Mettre en cache le fichier téléchargé pour une utilisation future
        print(f"Saving downloaded file to cache: {cached_path}")
        shutil.copy(download_path, cached_path)
        print(f"Data saved to {download_path}")

        return download_path, temp_dir

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
                self._load_prithvi()
                if not self.prithvi_model:
                     raise RuntimeError("Prithvi model is not available.")

                print("Using Prithvi model for inference...")
                with rasterio.open(sat_data_path) as src:
                    image_array = src.read() # Lit les bandes dans un tableau numpy. Shape: (bands, height, width)
                    src_profile = src.profile # Sauvegarde les métadonnées géo (CRS, transform, etc.)

                # Prétraitement de l'image pour le modèle
                inputs = self.prithvi_processor(images=image_array, return_tensors="pt").to(self.device)

                # Exécution de l'inférence
                with torch.no_grad():
                    outputs = self.prithvi_model(**inputs)

                # --- Début du Post-Traitement ---
                print("Inference complete. Post-processing the output...")

                classification_map = torch.argmax(outputs.logits, dim=1).squeeze()
                classification_map_np = classification_map.cpu().numpy().astype(rasterio.uint8)

                dst_profile = src_profile.copy()
                dst_profile.update({
                    'count': 1,
                    'dtype': 'uint8',
                    'compress': 'lzw'
                })

                with rasterio.open(output_raster, 'w', **dst_profile) as dst:
                    dst.write(classification_map_np, 1)
                print(f"Classification raster saved to {output_raster}")

            elif analysis_type == 'failles':
                self._load_sam()
                if not self.sam_model:
                     raise RuntimeError("SAM model is not available.")

                print("Using SAM model for inference...")
                with rasterio.open(sat_data_path) as src:
                    src_profile = src.profile # Sauvegarde les métadonnées géo

                # Exécuter la prédiction SAM. 'predict' génère automatiquement des masques.
                results = self.sam_model.predict(sat_data_path, device=self.device)

                if not results or not results[0].masks:
                    raise Exception("SAM model did not detect any features (faults).")

                # Fusionner tous les masques détectés en une seule carte binaire
                # results[0].masks.data est un tenseur (N, H, W) où N est le nombre de masques
                merged_mask = torch.sum(results[0].masks.data, dim=0).clamp(0, 1)

                # Convertir en NumPy et préparer pour la sauvegarde
                mask_np = merged_mask.cpu().numpy().astype(rasterio.uint8)

                dst_profile = src_profile.copy()
                dst_profile.update({'count': 1, 'dtype': 'uint8', 'compress': 'lzw'})

                with rasterio.open(output_raster, 'w', **dst_profile) as dst:
                    dst.write(mask_np, 1)
                print(f"Fault detection raster saved to {output_raster}")

            elif analysis_type == 'landcover':
                self._load_landcover()
                if not self.landcover_model:
                     raise RuntimeError("Landcover model is not available.")

                print("Using Landcover (SegFormer) model for inference...")
                # Les modèles de segmentation classiques utilisent souvent des images RGB
                # Nous allons lire uniquement les 3 premières bandes (Red, Green, Blue)
                # L'ordre est garanti par notre fetch_satellite_data optimisé
                with rasterio.open(sat_data_path) as src:
                    image_array = src.read() # Lit les 3 bandes [R, G, B]
                    src_profile = src.profile

                # Prétraitement et inférence
                inputs = self.landcover_processor(images=image_array, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self.landcover_model(**inputs)

                # Post-traitement: argmax sur les logits pour obtenir la carte de classification
                logits = outputs.logits.cpu()
                # Redimensionner la sortie à la taille de l'image originale
                upsampled_logits = torch.nn.functional.interpolate(logits, size=image_array.shape[1:], mode="bilinear", align_corners=False)
                classification_map = upsampled_logits.argmax(dim=1).squeeze()
                classification_map_np = classification_map.numpy().astype(rasterio.uint8)

                # Sauvegarder le raster de classification
                dst_profile.update({'count': 1, 'dtype': 'uint8', 'compress': 'lzw'})
                with rasterio.open(output_raster, 'w', **dst_profile) as dst:
                    dst.write(classification_map_np, 1)
                print(f"Landcover classification raster saved to {output_raster}")

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
