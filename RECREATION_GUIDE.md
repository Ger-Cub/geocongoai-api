# 📖 Guide de Recréation et de Déploiement - API GeoCongo AI

Ce document fournit des instructions complètes pour recréer, configurer et déployer l'API GeoCongo AI à partir de zéro. Il est conçu pour être utilisé par un développeur ou un agent d'intelligence artificielle.

## 1. Vue d'ensemble du Projet

L'API GeoCongo AI est un service de géo-intelligence artificielle conçu pour analyser des images satellites et en extraire des informations géologiques pertinentes pour la République Démocratique du Congo (RDC).

**Fonctionnalités Clés :**

- **Analyse Asynchrone :** Les requêtes d'analyse sont gérées via une file d'attente de tâches pour éviter les timeouts HTTP sur les traitements longs.
- **Modèles d'IA :** Intègre la suite Prithvi-EO-V2 pour la détection multispectrale.
  - **SegFormer :** Pour la classification de la couverture terrestre (déforestation, zones urbaines, etc.).
- **Traitement Géospatial :** Utilise PyQGIS pour la vectorisation des résultats de l'IA (conversion de raster en polygones).
- **Persistance des Données :** Stocke les résultats vectorisés dans une base de données PostGIS pour des requêtes spatiales futures.
- **Mise en Cache Intelligente :** Met en cache les images satellites téléchargées pour accélérer les analyses répétées sur les mêmes zones.
- **Déploiement Cloud-Native :** Conçu pour être déployé en tant que conteneur sur des services managés comme Google Cloud Run, avec support GPU.

## 2. Prérequis

- **Python** >= 3.9
- **Docker**
- Un compte sur une plateforme Cloud (GCP, AWS, ou Azure) avec les outils CLI correspondants installés et configurés.
- **Modèles d'IA :**
  - **Prithvi:** `Prithvi_EO_V2_600M_TL.pt` (disponible sur Hugging Face)
  - **SegFormer:** `segformer-b0-finetuned-ade-512-512` (disponible sur Hugging Face)

## 3. Structure du Projet

Créez la structure de fichiers et de dossiers suivante :

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée de l'API FastAPI
│   ├── core/
│   │   ├── __init__.py
│   │   └── security.py         # Gestion de la clé d'API
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Configuration de la connexion à la base de données
│   │   └── models.py           # Modèles de données SQLAlchemy/GeoAlchemy2
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py       # Logique d'inférence des modèles d'IA
│       ├── geo_service.py      # Logique de traitement géospatial (QGIS)
│       ├── postgis_service.py  # Interaction avec la base de données PostGIS
│       ├── cloud_tasks_service.py # Gestion des tâches asynchrones (spécifique à GCP)
│       └── landcover_colormap.json # Palette de couleurs pour la classification
├── scripts/
│   └── deploy.sh               # Script de déploiement pour GCP
├── Dockerfile
├── requirements.txt
└── RECREATION_GUIDE.md         # Ce fichier
```

## 4. Code Source Complet

Voici le contenu de chaque fichier nécessaire pour construire l'application.

---

### `requirements.txt`

```txt
fastapi
uvicorn[standard]
pydantic
python-dotenv
python-multipart
sqlalchemy
psycopg2-binary
geoalchemy2
transformers
torch
rasterio
odc-stac
pystac-client
matplotlib
Pillow
google-cloud-tasks
google-cloud-storage
```

---

### `Dockerfile`

Ce Dockerfile est optimisé pour installer PyQGIS, ce qui est une étape complexe.

```dockerfile
# Étape 1: Builder avec l'environnement QGIS
FROM ubuntu:22.04 as builder

ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances de base et de QGIS
RUN apt-get update && \
    apt-get install -y gnupg software-properties-common wget && \
    wget -qO - https://qgis.org/downloads/qgis-2024.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import && \
    chmod 644 /etc/apt/trusted.gpg.d/qgis-archive.gpg && \
    add-apt-repository "deb https://qgis.org/ubuntu $(lsb_release -cs) main" && \
    apt-get update && \
    apt-get install -y \
    qgis-server \
    python3-qgis \
    python3-pip \
    git

# Copier les fichiers de l'application
WORKDIR /app
COPY ./app /app/app
COPY ./requirements.txt /app/

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Étape 2: Image finale optimisée
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances d'exécution (beaucoup moins que le builder)
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgdal-dev \
    gdal-bin \
    # Dépendances minimales pour QGIS et PyTorch
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier l'environnement QGIS et les dépendances Python depuis le builder
COPY --from=builder /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages
COPY --from=builder /usr/share/qgis /usr/share/qgis
COPY --from=builder /etc/qgis /etc/qgis
COPY --from=builder /app /app

# Définir les variables d'environnement pour que Python trouve QGIS
ENV PYTHONPATH=/usr/share/qgis/python:/usr/lib/python3/dist-packages:$PYTHONPATH
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENV QGIS_PREFIX_PATH=/usr

# Point d'entrée de l'application
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### Contenu des fichiers `app/**/*.py`

#### `app/main.py`

```python
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from enum import Enum
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.security import get_api_key
from app.services.ai_service import AIService
from app.services.geo_service import GeoService
from app.services.cloud_tasks_service import CloudTasksService
from app.services.postgis_service import PostGISService
from app.db.database import get_db, engine
from app.db import models
from pydantic import BaseModel

class AnalysisType(str, Enum):
    FAILLES = "failles"
    MINES = "mines"
    MINERAUX = "minéraux"
    GLISSEMENTS_DE_TERRAIN = "glissements de terrain"
    LANDCOVER = "landcover" # Exemple: déforestation, eau, zones urbaines

class AnalysisRequest(BaseModel):
    bbox: List[float] # [minx, miny, maxx, maxy]
    analysis_type: AnalysisType
    crs: Optional[str] = "EPSG:4326"

class CacheFileInfo(BaseModel):
    filename: str
    size_mb: float

# --- Services ---
# Ces variables seront peuplées au démarrage via le lifespan.
# L'utilisation de `app.state` est une pratique FastAPI standard.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 Starting Gundua Engine...")

    # --- QGIS Initialization (moved here to not block import) ---
    try:
        from qgis.core import QgsApplication
        # Initialize QGIS Application in headless mode
        app.state.qgs = QgsApplication([], False)
        app.state.qgs.initQgis()
        print("PyQGIS Initialized successfully in headless mode.")
    except (ImportError, Exception) as e:
        print(f"⚠️ Warning: Failed to initialize PyQGIS ({e}). GIS vectorization will be simulated.")
        app.state.qgs = None

    # Initialize services inside the lifespan to avoid blocking the module import
    app.state.ai_service = AIService()
    app.state.geo_service = GeoService(qgis_available=(app.state.qgs is not None))
    try:
        app.state.tasks_service = CloudTasksService()
    except ValueError as e:
        app.state.tasks_service = None
        print(f"⚠️ CloudTasksService not initialized: {e}. Asynchronous saving will be disabled.")

    yield
    # Shutdown logic
    if app.state.qgs:
        app.state.qgs.exitQgis()
        print("QGIS Application exited cleanly.")

app = FastAPI(
    title="Gundua Engine",
    description="Advanced GeoAI for Geological Analysis in DRC",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    ai_service: AIService = Depends(lambda: app.state.ai_service),
    geo_service: GeoService = Depends(lambda: app.state.geo_service),
    tasks_service: Optional[CloudTasksService] = Depends(lambda: app.state.tasks_service),
    api_key: str = Depends(get_api_key)):
    """
    Launches an asynchronous analysis task.
    Returns a task ID to track the progress.
    """
    if not tasks_service:
        raise HTTPException(
            status_code=503, 
            detail="Asynchronous processing is not available. CloudTasksService is not configured."
        )

    try:
        # 1. Créer une tâche asynchrone pour l'analyse complète
        task_payload = {
            "bbox": request.bbox,
            "analysis_type": request.analysis_type.value
        }
        task_name = tasks_service.create_task(
            endpoint="/tasks/execute-analysis", 
            payload=task_payload
        )
        task_id = task_name.split('/')[-1]
        return {
            "status": "processing_started",
            "task_id": task_id,
            "message": "Analysis has been queued. Use the /tasks/status/{task_id} endpoint to check progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint pour le worker Cloud Tasks ---
# Note: La sécurité est gérée par l'authentification OIDC de Cloud Tasks.
# Seul le compte de service configuré peut appeler cet endpoint.
@app.post("/tasks/execute-analysis")
async def task_execute_analysis(
    payload: dict = Body(...),
    ai_service: AIService = Depends(lambda: app.state.ai_service),
    geo_service: GeoService = Depends(lambda: app.state.geo_service),
    db: Session = Depends(get_db)
):
    """
    Worker endpoint called by Cloud Tasks to run the full analysis pipeline.
    """
    bbox = payload["bbox"]
    analysis_type = payload["analysis_type"]
    postgis_service = PostGISService(db)

    try:
        # 1. Inférence avec les modèles d'IA
        raster_path = await ai_service.run_inference(bbox, analysis_type)
        
        # 2. Vectorisation avec QGIS
        vector_path = geo_service.vectorize_raster(raster_path)
        
        # 3. Lecture des données vectorielles en GeoJSON
        result = geo_service.read_vector_as_geojson(vector_path, analysis_type=analysis_type)

        # 4. Sauvegarde des résultats en base de données
        postgis_service.save_geojson_to_postgis(
            geojson_data=result,
            analysis_type=analysis_type,
            request_bbox=bbox
        )
        
        # Optionnel : générer et stocker la preview
        # preview_png_base64 = geo_service.create_raster_preview(raster_path, analysis_type=analysis_type)
        # ...logique pour stocker la preview avec un identifiant de tâche...

        return {"status": "success", "message": "Analysis complete and results saved."}

    except Exception as e:
        print(f"❌ Task failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) # Cloud Tasks réessayera en cas d'échec

@app.post("/tasks/save-results")
async def task_save_results(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Worker endpoint called by Cloud Tasks to save GeoJSON results to PostGIS.
    """
    postgis_service = PostGISService(db)
    postgis_service.save_geojson_to_postgis(
        geojson_data=payload["geojson_data"],
        analysis_type=payload["analysis_type"],
        request_bbox=payload["request_bbox"]
    )
    return {"status": "success", "message": "Results saved to PostGIS."}

@app.get("/tasks/status/{task_id}", dependencies=[Depends(get_api_key)])
async def get_task_status(
    task_id: str,
    tasks_service: Optional[CloudTasksService] = Depends(lambda: app.state.tasks_service)
):
    """
    Checks the status of an asynchronous analysis task.
    """
    if not tasks_service:
        raise HTTPException(status_code=503, detail="CloudTasksService is not available.")
    
    try:
        status = tasks_service.get_task_status(task_id)
        return {"task_id": task_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/results", dependencies=[Depends(get_api_key)])
async def get_results(
    analysis_type: Optional[AnalysisType] = Query(None, description="Filter by analysis type"),
    bbox: Optional[str] = Query(None, description="Filter by a bounding box: 'minx,miny,maxx,maxy'"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieves vectorized analysis results from the PostGIS database.
    """
    # Importations locales pour la clarté
    from geoalchemy2.functions import ST_AsGeoJSON, ST_MakeEnvelope
    from app.db.models import AnalysisResult
    
    query = db.query(
        AnalysisResult.analysis_type,
        AnalysisResult.class_label,
        ST_AsGeoJSON(AnalysisResult.geometry).label('geometry')
    )

    if analysis_type:
        query = query.filter(AnalysisResult.analysis_type == analysis_type.value)

    if bbox:
        try:
            bbox_coords = [float(c) for c in bbox.split(',')]
            query = query.filter(AnalysisResult.geometry.ST_Intersects(ST_MakeEnvelope(*bbox_coords, 4326)))
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use 'minx,miny,maxx,maxy'.")

    results = query.offset(skip).limit(limit).all()
    # Formatage en GeoJSON FeatureCollection
    import json
    features = [
        {
            "type": "Feature",
            "properties": {"analysis_type": r.analysis_type, "class_label": r.class_label},
            "geometry": json.loads(r.geometry)
        } for r in results
    ]
    return {"type": "FeatureCollection", "features": features}

@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API GeoCongo AI 🌍",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs"
    }

@app.get("/health")
async def health(ai_service: Optional[AIService] = Depends(lambda: getattr(app.state, "ai_service", None))):
    qgis_status = "initialized" if getattr(app.state, "qgs", None) else "simulated"
    models_loaded = "ok" if ai_service and getattr(ai_service, 'prithvi_model', None) and getattr(ai_service, 'sam_model', None) else "loading_or_failed"
    return {
        "status": "healthy" if ai_service else "initializing",
        "qgis": qgis_status,
        "models_loaded": models_loaded,
        "device": getattr(ai_service, 'device', 'unknown'),
    }

@app.get("/admin/cache-info", dependencies=[Depends(get_api_key)], response_model=List[CacheFileInfo])
async def get_cache_info():
    """
    Lists files in the satellite cache, their size, and the total cache size.
    """
    ai_service: Optional[AIService] = getattr(app.state, "ai_service", None)
    if not ai_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    cache_files = []
    total_size_bytes = 0
    try:
        for filename in os.listdir(ai_service.satellite_cache_dir):
            file_path = os.path.join(ai_service.satellite_cache_dir, filename)
            if os.path.isfile(file_path):
                size_bytes = os.path.getsize(file_path)
                total_size_bytes += size_bytes
                cache_files.append(CacheFileInfo(filename=filename, size_mb=round(size_bytes / (1024 * 1024), 4)))
        return cache_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read cache directory: {e}")

@app.post("/admin/clear-cache", dependencies=[Depends(get_api_key)])
async def clear_cache():
    """
    Manually clears all files from the satellite image cache.
    """
    ai_service: Optional[AIService] = getattr(app.state, "ai_service", None)
    if not ai_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        deleted_count = ai_service.clear_all_cache()
        return {"status": "success", "message": f"Cache cleared successfully. {deleted_count} files deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")
```

#### `app/core/security.py`

```python
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import os

API_KEY = os.getenv("GEOCONGO_API_KEY", "geocongo_secret_key_2026")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API Key"
        )
```

#### `app/db/database.py`

> [!WARNING]
> Ce fichier n'est pas présent dans l'espace de travail actuel.

#### `app/db/models.py`

> [!WARNING]
> Ce fichier n'est pas présent dans l'espace de travail actuel.

#### `app/services/ai_service.py`

```python
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


        self.models_dir = "/app/models"
        self.satellite_cache_dir = os.path.join(self.models_dir, "satellite_cache")
        os.makedirs(self.satellite_cache_dir, exist_ok=True)

        self.prithvi_path = os.path.join(self.models_dir, "prithvi/Prithvi_EO_V2_600M_TL.pt")
        self.landcover_path = os.path.join(self.models_dir, "landcover/segformer-b0-finetuned-ade-512-512")
        
        # --- Chargement du modèle Prithvi ---
        self.prithvi_model = None
        self.prithvi_processor = None
        if os.path.exists(self.prithvi_path):
            try:
                print(f"Loading Prithvi model from {self.prithvi_path}...")
                self.prithvi_processor = AutoImageProcessor.from_pretrained("HuggingFaceM4/prithvi-eo-v2")
                self.prithvi_model = MaskedAutoencoderForViT.from_pretrained(self.prithvi_path, ignore_mismatched_sizes=True)
                self.prithvi_model.to(self.device)
                print("Prithvi model loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading Prithvi model: {e}")
        else:
            print(f"Warning: Prithvi model NOT found at {self.prithvi_path}")

        # --- Chargement du modèle Landcover (Exemple avec SegFormer) ---
        self.landcover_model = None
        self.landcover_processor = None
        if os.path.exists(self.landcover_path):
            try:
                print(f"Loading Landcover model from {self.landcover_path}...")
                self.landcover_processor = AutoImageProcessor.from_pretrained(self.landcover_path)
                self.landcover_model = SegformerForSemanticSegmentation.from_pretrained(self.landcover_path)
                self.landcover_model.to(self.device)
                print("Landcover model loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading Landcover model: {e}")
        else:
            print(f"Warning: Landcover model NOT found at {self.landcover_path}")

        print(f"AI Service initialized on {self.device}")

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
        2. Runs Prithvi-EO-2.0 inference.
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
            if analysis_type in ['minéraux', 'mines'] and self.prithvi_model:
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
                # Simulation ou autre méthode pour les failles
                print("Processing faults with Prithvi embeddings...")
                # ... logique ...

            elif analysis_type == 'landcover' and self.landcover_model:
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
```

#### `app/services/geo_service.py`

```python
import os
import json
import base64
import numpy as np
import io
import rasterio
from PIL import Image

from qgis.core import QgsVectorLayer
from qgis import processing
from processing.core.Processing import Processing
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class GeoService:
    def __init__(self, qgis_available: bool = False):
        self.has_qgis = qgis_available
        if self.has_qgis:
            Processing.initialize()
            print("QGIS Processing framework initialized.")
        else:
            print("GeoService initialized in Simulation Mode (No QGIS).")
        self.landcover_colormap, self.landcover_labels = self._load_colormap_and_labels()

    def _load_colormap_and_labels(self) -> (np.ndarray, dict):
        """Loads the landcover colormap and labels from a JSON file."""
        try:
            colormap_path = os.path.join(os.path.dirname(__file__), 'landcover_colormap.json')
            with open(colormap_path, 'r') as f:
                config = json.load(f)
            
            labels = {int(k): v for k, v in config.get('labels', {}).items()}

            # Crée une table de correspondance (LUT) pour un accès rapide
            max_index = max(map(int, config['colors'].keys()))
            colormap = np.array([config.get('default_color', [0, 0, 0])] * (max_index + 1), dtype=np.uint8)
            for index, color in config['colors'].items():
                colormap[int(index)] = color
            return colormap, labels
        except Exception as e:
            print(f"⚠️ Could not load landcover colormap: {e}. Previews will use default colors.")
            return None, {}

    def vectorize_raster(self, raster_path: str) -> str:
        """
        Converts a classification raster into vector format using QGIS Polygonize.
        """
        if not self.has_qgis:
            print("⚠️ Skipping vectorization because PyQGIS is not available.")
            return self._mock_vectorize(raster_path)

        output_vector = raster_path.replace(".tif", ".gpkg")
        
        try:
            print(f"Vectorizing {raster_path} to {output_vector} using gdal:polygonize...")
            params = {
                'INPUT': raster_path,
                'BAND': 1,
                'FIELD': 'class',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': output_vector
            }
            # Exécution réelle de l'algorithme de QGIS
            processing.run("gdal:polygonize", params)
            print("Vectorization complete.")
            return output_vector
        except Exception as e:
            print(f"❌ Error during vectorization: {e}")
            raise e

    def read_vector_as_geojson(self, vector_path: str, analysis_type: str = None) -> dict:
        """
        Reads a Geopackage/Shapefile and returns it as a GeoJSON dictionary.
        """
        if not self.has_qgis or not os.path.exists(vector_path):
            print("⚠️ Skipping GeoJSON conversion because vector file is missing.")
            return self._mock_geojson()

        try:
            # Charger la couche vecteur avec QGIS
            layer = QgsVectorLayer(vector_path, "result_layer", "ogr")
            if not layer.isValid():
                raise Exception(f"Failed to load vector layer: {vector_path}")
            
            # Récupérer les entités et les convertir en GeoJSON
            features_geojson = []
            for feature in layer.getFeatures():
                feature_json = json.loads(feature.asJson())
                # Si c'est une analyse landcover, ajouter le label de la classe
                if analysis_type == 'landcover' and 'class' in feature_json['properties']:
                    class_id = feature_json['properties']['class']
                    feature_json['properties']['class_label'] = self.landcover_labels.get(class_id, 'unknown')
                features_geojson.append(feature_json)
            return {"type": "FeatureCollection", "features": features_geojson}
        except Exception as e:
            print(f"❌ Error reading vector file as GeoJSON: {e}")
            raise e

    def create_raster_preview(self, raster_path: str, analysis_type: str = None) -> str:
        """
        Creates a Base64 encoded PNG preview of a classification raster.
        Applies a custom colormap for 'landcover' analysis.
        """
        try:
            with rasterio.open(raster_path) as src:
                data = src.read(1)

            if analysis_type == 'landcover':
                if self.landcover_colormap is not None:
                    # Utiliser la table de correspondance (LUT) pour une conversion rapide et vectorisée
                    # Remplace chaque valeur d'index dans `data` par la couleur correspondante dans la LUT
                    rgb_image = self.landcover_colormap[data]
                else:
                    # Fallback si la palette n'a pas pu être chargée
                    rgb_image = np.stack([data, data, data], axis=-1).astype(np.uint8)
                image = Image.fromarray(rgb_image)

            else:
                # Logique existante pour les autres types d'analyse (ex: viridis)
                # 'cmap' normalise les données et les mappe en couleurs RGBA
                colored_data = cm.viridis(data / data.max() if data.max() > 0 else data)
                
                # Convertir en image PIL (en ignorant la couche alpha pour le moment)
                image = Image.fromarray((colored_data[:, :, :3] * 255).astype('uint8'))

            # Sauvegarder l'image en mémoire dans un buffer
            buf = io.BytesIO()
            image.save(buf, format='PNG')

            # Retourner la chaîne encodée en Base64
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ Could not generate raster preview: {e}")
            return None

    def _mock_vectorize(self, raster_path: str) -> str:
        """Generates a dummy vector file for simulation mode."""
        output_vector = raster_path.replace(".tif", ".gpkg")
        with open(output_vector, "w") as f:
            f.write("dummy vector data")
        return output_vector

    def _mock_geojson(self) -> dict:
        """Returns a sample GeoJSON for simulation mode."""
        return {
            "type": "FeatureCollection",
            "name": "mock_results",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"class": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[25.0, -2.0], [25.1, -2.0], [25.1, -2.1], [25.0, -2.1], [25.0, -2.0]]]
                    }
                }
            ]
        }
```

#### `app/services/postgis_service.py`

```python
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, box
from typing import Dict, List

from app.db.models import AnalysisResult

class PostGISService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_geojson_to_postgis(self, geojson_data: Dict, analysis_type: str, request_bbox: List[float]):
        """
        Parses a GeoJSON FeatureCollection and saves its features to PostGIS.
        """
        if not geojson_data or 'features' not in geojson_data:
            print("⚠️ No features found in GeoJSON data to save.")
            return

        features = geojson_data['features']
        request_bbox_geom = box(*request_bbox) # Crée un polygone Shapely à partir de la bbox

        db_objects = []
        for feature in features:
            geom = shape(feature['geometry'])
            properties = feature.get('properties', {})

            db_object = AnalysisResult(
                analysis_type=analysis_type,
                class_id=properties.get('class'),
                class_label=properties.get('class_label'),
                confidence_score=properties.get('confidence'),
                bbox=from_shape(request_bbox_geom, srid=4326),
                geometry=from_shape(geom, srid=4326)
            )
            db_objects.append(db_object)

        try:
            self.db.add_all(db_objects)
            self.db.commit()
            print(f"✅ Successfully saved {len(db_objects)} features to PostGIS for analysis '{analysis_type}'.")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error saving to PostGIS: {e}")
            raise e

    def get_results(self, analysis_type: str, bbox: List[float]):
        # Cette méthode sera implémentée dans une étape future pour l'endpoint GET /results
        pass
```

#### `app/services/cloud_tasks_service.py`

```python
import os
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import datetime
from typing import Dict, List

class CloudTasksService:
    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        self.project = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION")
        self.queue = os.getenv("CLOUD_TASKS_QUEUE")
        self.worker_url = os.getenv("CLOUD_TASKS_WORKER_URL")
        self.worker_sa_email = os.getenv("CLOUD_TASKS_WORKER_SA_EMAIL")

        if not all([self.project, self.location, self.queue, self.worker_url, self.worker_sa_email]):
            raise ValueError("Missing required environment variables for CloudTasksService.")

        self.parent = self.client.queue_path(self.project, self.location, self.queue)

    def create_save_result_task(self, geojson_data: Dict, analysis_type: str, request_bbox: List[float]):
        """
        Creates a Cloud Task to save analysis results asynchronously.
        """
        payload = {
            "geojson_data": geojson_data,
            "analysis_type": analysis_type,
            "request_bbox": request_bbox
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.worker_url}/tasks/save-results",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {"service_account_email": self.worker_sa_email},
            },
            # --- Configuration de la politique de retry ---
            # Temps maximum accordé au worker pour terminer la tâche.
            "dispatch_deadline": datetime.timedelta(minutes=5).total_seconds(),
            # Nombre maximum de tentatives en cas d'échec.
            "max_dispatches": 5,
            # Temps minimum d'attente avant une nouvelle tentative.
            "min_backoff": datetime.timedelta(seconds=10).total_seconds(),
        }

        response = self.client.create_task(parent=self.parent, task=task)
        print(f"Created task: {response.name}")
```

#### `app/services/landcover_colormap.json`

> [!WARNING]
> Ce fichier n'est pas présent dans l'espace de travail actuel.

## 5. Instructions de Déploiement

Cette section détaille comment déployer l'application sur différentes plateformes cloud. Le principe est toujours le même :

1. **Stocker les modèles d'IA** dans un service de stockage (S3, GCS, Blob Storage).
2. **Créer une base de données** PostgreSQL avec l'extension PostGIS.
3. **Construire et pousser l'image Docker** vers un registre de conteneurs (ECR, GCR, ACR).
4. **Déployer le conteneur** sur un service de calcul (App Runner, Cloud Run, Container Apps), en le connectant au stockage et à la base de données.
5. **Configurer un système de tâches asynchrones** (SQS/Lambda, Cloud Tasks, Queue Storage/Functions).

### A. Déploiement sur Google Cloud Platform (GCP) - Implémentation de référence

C'est la plateforme pour laquelle le projet est initialement configuré.

1. **Configuration du Projet :**
    - Créez un projet GCP.
    - Activez les APIs : `Cloud Build`, `Cloud Run`, `Cloud Tasks`, `Cloud Storage`, `Cloud SQL Admin`.

2. **Stockage des Modèles :**
    - Créez un bucket Cloud Storage (ex: `geocongo-models-bucket`).
    - Uploadez vos modèles (`.pt`, etc.) dans ce bucket, en respectant la structure attendue par `ai_service.py` (`prithvi/`, `landcover/`).

3. **Base de Données PostGIS :**
    - Créez une instance Cloud SQL pour PostgreSQL.
    - Connectez-vous à l'instance et exécutez `CREATE EXTENSION postgis;` dans votre base de données.
    - Créez un utilisateur et notez le mot de passe.

4. **File d'attente de Tâches :**
    - Créez une file d'attente Cloud Tasks (ex: `geocongo-results-queue`).

5. **Compte de Service pour le Worker :**
    - Créez un compte de service (ex: `geocongo-worker-sa`).
    - Donnez-lui le rôle "Invocateur Cloud Run" (`run.invoker`) pour qu'il puisse appeler l'endpoint de la tâche.

6. **Script de Déploiement (`scripts/deploy.sh`) :**
    - Créez le fichier `scripts/deploy.sh` avec le contenu fourni dans le contexte.
    - **Adaptez les variables** en haut du script (`PROJECT_ID`, `MODELS_BUCKET`, `WORKER_SA_EMAIL`).
    - Rendez le script exécutable : `chmod +x scripts/deploy.sh`.
    - Exécutez le script : `./scripts/deploy.sh`.

    **Ce que fait le script :**
    - Il construit l'image Docker via Cloud Build.
    - Il déploie une première version sur Cloud Run avec toutes les configurations (GPU, CPU, mémoire, timeout).
    - Il monte le bucket de modèles en tant que volume dans le conteneur (`--add-volume`).
    - Il configure les variables d'environnement, y compris la clé API et les informations de la file d'attente.
    - Il récupère l'URL du service déployé et la réinjecte dans une nouvelle révision pour que le worker de tâches connaisse sa propre adresse.
    - Il effectue une vérification de santé (`/health`) pour s'assurer que les modèles sont bien chargés avant de terminer.

### B. Déploiement sur AWS (Guide Conceptuel)

1. **Stockage :** Créez un bucket S3 et uploadez les modèles.
2. **Base de Données :** Lancez une instance Amazon RDS pour PostgreSQL et activez l'extension PostGIS.
3. **Conteneur :**
    - Créez un référentiel sur Amazon ECR.
    - Construisez et poussez votre image Docker vers cet ECR.
4. **Calcul :**
    - **Option 1 (Simple) : AWS App Runner.** Créez un service App Runner à partir de votre image ECR. Vous devrez configurer les variables d'environnement et les secrets. Le montage direct de S3 est moins direct qu'avec GCP ; vous pourriez avoir besoin de télécharger les modèles au démarrage du conteneur.
    - **Option 2 (Avancé) : AWS Fargate sur ECS.** Définissez une "Task Definition" avec les ressources nécessaires (CPU, mémoire, image ECR). Créez un service ECS pour exécuter cette tâche. Pour le GPU, vous devrez utiliser ECS sur des instances EC2 de type `g4dn`, `p3`, etc.
5. **Tâches Asynchrones :**
    - Créez une file d'attente Amazon SQS.
    - L'endpoint `/analyze` enverra un message à cette file SQS.
    - Créez une fonction AWS Lambda qui est déclenchée par les messages SQS. Cette fonction Lambda fera un appel HTTP POST à l'endpoint `/tasks/execute-analysis` de votre service sur App Runner/ECS. Vous devrez adapter le `CloudTasksService` pour qu'il utilise le SDK Boto3 pour SQS.

### C. Déploiement sur Azure (Guide Conceptuel)

1. **Stockage :** Créez un compte de stockage Azure et un conteneur Blob. Uploadez les modèles.
2. **Base de Données :** Lancez une instance "Azure Database for PostgreSQL" et activez l'extension PostGIS.
3. **Conteneur :**
    - Créez un "Azure Container Registry" (ACR).
    - Construisez et poussez votre image Docker vers cet ACR.
4. **Calcul :**
    - **Option 1 (Simple) : Azure Container Apps.** Créez une "Container App" à partir de votre image ACR. Configurez les variables d'environnement et les secrets. Pour monter le stockage de blobs, utilisez la fonctionnalité de montage de volume d'Azure Files.
    - **Option 2 (Avancé) : Azure Kubernetes Service (AKS).** Déployez votre conteneur sur un cluster AKS, ce qui vous donne un contrôle total, notamment pour l'attribution de nœuds GPU.
5. **Tâches Asynchrones :**
    - Créez une file d'attente "Azure Queue Storage".
    - L'endpoint `/analyze` enverra un message à cette file d'attente.
    - Créez une "Azure Function" avec un déclencheur de file d'attente ("Queue Trigger"). Cette fonction appellera l'endpoint `/tasks/execute-analysis` de votre Container App. Vous devrez adapter le `CloudTasksService` pour qu'il utilise le SDK Azure pour les files d'attente.

---

Ce guide fournit une base solide pour la recréation et le déploiement de l'API. L'adaptation aux spécificités de chaque cloud (notamment pour les services de tâches asynchrones et le montage de volumes) nécessitera d'écrire des implémentations de service spécifiques à chaque plateforme.
