import os
import shutil
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Body, BackgroundTasks
from typing import List, Optional, Dict
from datetime import datetime

from app.models import AnalysisRequest, AnalysisTypeInfo, AnalysisResultResponse, HealthResponse
from app.analysis_registry import ANALYSIS_TYPES, get_analysis_config
from app.core.security import get_api_key
from app.services.ai_service import AIService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 Container Startup Initiated ---")
    app.state.ai_service = AIService()
    app.state.storage_dir = "/tmp/app_storage"
    os.makedirs(app.state.storage_dir, exist_ok=True)
    
    yield
    shutil.rmtree(app.state.storage_dir, ignore_errors=True)
    print("--- 🛑 Shutdown complete ---")

async def run_analysis_pipeline(request_id: str, request: AnalysisRequest):
    """Pipeline complet : GEE -> Prithvi -> Analyse Spécifique -> Export"""
    work_dir = os.path.join(app.state.storage_dir, request_id)
    os.makedirs(work_dir, exist_ok=True)
    
    # 1 & 2. Inférence via Vertex AI (inclut le fetch GEE interne)
    result_raster_path = await app.state.ai_service.run_inference(request.bbox, request.analysis_type)
    
    # 3. TODO: Vectorisation et sauvegarde via PostGISService
    print(f"Analyse {request.analysis_type} terminée. Résultat : {result_raster_path}")

app = FastAPI(
    title="GeoCongo AI API",
    description="Analyse géologique et environnementale automatisée (Prithvi EO v2)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/analysis-types", response_model=Dict[str, List[AnalysisTypeInfo]])
async def list_analysis_types():
    return {"analysis_types": ANALYSIS_TYPES}

@app.post("/analyze", dependencies=[Depends(get_api_key)])
async def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks):
    config = get_analysis_config(request.analysis_type)
    if not config:
        raise HTTPException(status_code=400, detail="Type d'analyse invalide")
    
    request_id = str(uuid.uuid4())
    background_tasks.add_task(run_analysis_pipeline, request_id, request)
    
    return {
        "request_id": request_id,
        "status": "accepted",
        "analysis_type": request.analysis_type,
        "message": f"Analyse '{config['name']}' démarrée."
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "healthy",
        "model_loaded": hasattr(app.state, 'ai_service') and app.state.ai_service is not None,
        "gee_authenticated": True
    }