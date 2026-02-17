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
    print("🚀 Starting GeoCongo AI API...")

    # --- Conditional Service Initialization (Microservices) ---
    enabled_service = os.getenv("ENABLED_SERVICE", "router") # default to router
    print(f"🚀 Starting GeoCongo AI API in mode: {enabled_service}")

    # Initialize services inside the lifespan
    if enabled_service != 'router':
        # Worker Mode: Load AIService and GeoService (Pure Python)
        app.state.ai_service = AIService()
        app.state.geo_service = GeoService()
        app.state.qgs = None # QGIS no longer used
    else:
        # Router Mode: No AI, No Geo
        app.state.ai_service = None
        app.state.geo_service = None
        app.state.qgs = None
        print("Router Mode: AI and Geo services disabled.")

    # CloudTasksService
    try:
        app.state.tasks_service = CloudTasksService()
    except ValueError as e:
        app.state.tasks_service = None
        if enabled_service == 'router':
             print(f"⚠️ CRITICAL: CloudTasksService not initialized on Router: {e}. Dispatching will fail.")
        else:
             print(f"⚠️ CloudTasksService not initialized: {e}. Worker mode can operate without it.")

    yield
    # Shutdown logic
    print("Shutting down GeoCongo AI API...")

app = FastAPI(
    title="GeoCongo AI API",
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
    models_loaded = "ok" if ai_service and getattr(ai_service, 'prithvi_model', None) else "on_demand"
    
    # In Router mode, ai_service is None but the service is healthy.
    enabled_service = os.getenv("ENABLED_SERVICE", "router")
    is_healthy = True if (enabled_service == 'router') or ai_service else False

    return {
        "status": "healthy" if is_healthy else "initializing",
        "qgis": qgis_status,
        "models_loaded": models_loaded,
        "device": getattr(ai_service, 'device', 'unknown') if ai_service else 'cpu',
        "mode": enabled_service
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
