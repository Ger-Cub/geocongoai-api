import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from enum import Enum
from typing import List, Optional
from sqlalchemy.orm import Session
import json
from google.cloud import tasks_v2

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 Starting GeoCongo AI API...")

    app.state.ai_service = AIService()
    app.state.geo_service = GeoService()
    try:
        app.state.tasks_service = CloudTasksService()
    except ValueError as e:
        app.state.tasks_service = None
        print(f"⚠️ CloudTasksService not initialized: {e}. Asynchronous saving will be disabled.")

    yield
    print("Shutdown complete.")

app = FastAPI(
    title="GeoCongo AI API",
    description="API for Geospatial AI Analysis in DRC.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/analyze", dependencies=[Depends(get_api_key)])
async def analyze_area(
    request: AnalysisRequest,
    tasks_service: Optional[CloudTasksService] = Depends(lambda: getattr(app.state, "tasks_service", None))
):
    """
    Triggers an asynchronous analysis of a given bounding box.
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
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{tasks_service.worker_url}/tasks/execute-analysis",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(task_payload).encode(),
                "oidc_token": {"service_account_email": tasks_service.worker_sa_email},
            }
        }

        response = tasks_service.client.create_task(parent=tasks_service.parent, task=task)
        task_id = response.name.split('/')[-1]
        
        return {
            "status": "processing_started",
            "task_id": task_id,
            "message": "Analysis has been queued. Use the /tasks/status/{task_id} endpoint to check progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # 2. Vectorisation avec Rasterio (renvoie directement un GeoJSON)
        geojson_result = geo_service.vectorize_raster(raster_path)
        
        # 3. Ajout des labels de classe si nécessaire
        labeled_geojson = geo_service.add_class_labels(geojson_result, analysis_type=analysis_type)

        # 4. Sauvegarde des résultats en base de données
        postgis_service.save_geojson_to_postgis(
            geojson_data=labeled_geojson,
            analysis_type=analysis_type,
            request_bbox=bbox
        )
        
        # Optionnel : générer et stocker la preview
        # preview_png_base64 = geo_service.create_raster_preview(raster_path, analysis_type=analysis_type)
        return {"status": "success", "message": "Analysis complete and results saved."}

    except Exception as e:
        print(f"❌ Task failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    return {"status": "success"}

@app.get("/tasks/status/{task_id}", dependencies=[Depends(get_api_key)])
async def get_task_status(
    task_id: str,
    tasks_service: Optional[CloudTasksService] = Depends(lambda: getattr(app.state, "tasks_service", None))
):
    """
    Checks the status of an asynchronous analysis task.
    """
    if not tasks_service:
        raise HTTPException(status_code=503, detail="Task service not configured")
    try:
        name = tasks_service.client.task_path(tasks_service.project, tasks_service.location, tasks_service.queue, task_id)
        task = tasks_service.client.get_task(name=name)
        return {"task_id": task_id, "status": "processing"}
    except Exception as e:
        # Simplification: si la tâche n'est plus dans la file, on suppose qu'elle a abouti
        return {"task_id": task_id, "status": "completed"}

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
    vertex_configured = "ok"
    if ai_service:
        if not all([ai_service.prithvi_endpoint_id, ai_service.sam_endpoint_id, ai_service.landcover_endpoint_id]):
            vertex_configured = "missing_endpoint_ids"
    else:
        vertex_configured = "service_not_initialized"

    return {
        "status": "healthy" if ai_service else "initializing",
        "gis_engine": "rasterio",
        "vertex_ai_endpoints": vertex_configured
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