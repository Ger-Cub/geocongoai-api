import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

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

class AnalysisRequest(BaseModel):
    bbox: List[float] # [minx, miny, maxx, maxy]
    analysis_type: str # 'failles', 'mines', 'minéraux'
    crs: Optional[str] = "EPSG:4326"

# Services will be initialized lazily or during startup
ai_service: Optional[AIService] = None
geo_service: Optional[GeoService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global ai_service, geo_service
    print("🚀 Starting GeoCongo AI API...")
    # Initialize services inside the lifespan to avoid blocking the module import
    ai_service = AIService()
    geo_service = GeoService()
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

@app.post("/analyze", dependencies=[Depends(get_api_key)])
async def analyze(request: AnalysisRequest):
    """
    Execute complex geological analysis using Prithvi and SAM 2 models.
    The results are processed through QGIS for vectorization.
    """
    if request.analysis_type not in ['failles', 'mines', 'minéraux']:
        raise HTTPException(status_code=400, detail="Invalid analysis type")
    
    try:
        # 1. Inference with AI Models (Prithvi/SAM 2)
        raster_path = await ai_service.run_inference(request.bbox, request.analysis_type)
        
        # 2. Vectorization with QGIS (processing.run)
        vector_path = geo_service.vectorize_raster(raster_path)
        
        # 3. Return GeoJSON result
        result = geo_service.read_vector_as_geojson(vector_path)
        
        return {
            "status": "success",
            "type": request.analysis_type,
            "bbox": request.bbox,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
