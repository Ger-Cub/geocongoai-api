import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from enum import Enum
from typing import List, Optional
from sqlalchemy.orm import Session

# --- QGIS Initialization ---
# This must be done BEFORE importing any internal QGIS modules that depend on QgsApplication
try:
    from qgis.core import QgsApplication
    # Initialize QGIS Application in headless mode
    qgs = QgsApplication([], False)
    qgs.initQgis()
    print("PyQGIS Initialized successfully in headless mode.")
except (ImportError, Exception) as e:
    print(f"⚠️ Warning: Failed to initialize PyQGIS ({e}). AI functions will work, but GIS vectorization will be simulated.")
    qgs = None

from app.core.security import get_api_key
from app.services.ai_service import AIService
from app.services.geo_service import GeoService
from app.services.cloud_tasks_service import CloudTasksService
from app.services.postgis_service import PostGISService
from app.db.database import get_db, engine
from app.db import models

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

# Services will be initialized lazily or during startup
ai_service: Optional[AIService] = None
geo_service: Optional[GeoService] = None
tasks_service: Optional[CloudTasksService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global ai_service, geo_service, tasks_service
    print("🚀 Starting GeoCongo AI API...")
    # Initialize services inside the lifespan to avoid blocking the module import
    ai_service = AIService()
    geo_service = GeoService()
    try:
        tasks_service = CloudTasksService()
    except ValueError as e:
        print(f"⚠️ CloudTasksService not initialized: {e}. Asynchronous saving will be disabled.")
    yield
    # Shutdown logic
    if qgs:
        qgs.exitQgis()
        print("QGIS Application exited cleanly.")

app = FastAPI(
    title="GeoCongo AI API",
    description="Advanced GeoAI for Geological Analysis in DRC",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    api_key: str = Depends(get_api_key)):
    """
    Execute complex geological analysis using Prithvi and SAM 2 models.
    The results are processed through QGIS for vectorization.
    """
    try:
        # 1. Inference with AI Models (Prithvi/SAM 2)
        raster_path = await ai_service.run_inference(request.bbox, request.analysis_type.value)
        
        # 2. Vectorization with QGIS (processing.run)
        vector_path = geo_service.vectorize_raster(raster_path)
        
        # 3. Read vector data as GeoJSON
        result = geo_service.read_vector_as_geojson(vector_path, analysis_type=request.analysis_type.value)

        # 4. (NEW) Create an asynchronous task to save the results
        if tasks_service:
            tasks_service.create_save_result_task(result, request.analysis_type.value, request.bbox)
        else:
            print("⚠️ Skipping result saving because CloudTasksService is not available.")

        # 5. Generate a PNG preview of the raster
        preview_png_base64 = geo_service.create_raster_preview(raster_path, analysis_type=request.analysis_type.value)
        
        return {
            "status": "success",
            "type": request.analysis_type,
            "bbox": request.bbox,
            "data": result,
            "preview_png_base64": preview_png_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint pour le worker Cloud Tasks ---
# Note: La sécurité est gérée par l'authentification OIDC de Cloud Tasks.
# Seul le compte de service configuré peut appeler cet endpoint.
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
async def health():
    return {
        "status": "healthy" if ai_service else "initializing",
        "qgis": "initialized" if qgs else "simulated",
        "device": ai_service.device if ai_service else "unknown"
    }

@app.get("/admin/cache-info", dependencies=[Depends(get_api_key)], response_model=List[CacheFileInfo])
async def get_cache_info():
    """
    Lists files in the satellite cache, their size, and the total cache size.
    """
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
    if not ai_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        deleted_count = ai_service.clear_all_cache()
        return {"status": "success", "message": f"Cache cleared successfully. {deleted_count} files deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")
