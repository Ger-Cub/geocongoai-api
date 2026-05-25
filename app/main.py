import os
import shutil
import uuid
import importlib
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Dict, Any
from datetime import datetime

from app.models import AnalysisRequest, AnalysisTypeInfo, HealthResponse
from app.analysis_registry import ANALYSIS_TYPES, get_analysis_config
from app.dependencies import get_api_key
from app.services.satellite import SatelliteService
from app.services.inference import PrithviInference

# Initialize services
satellite_service = SatelliteService(project_id=os.getenv("GCP_PROJECT_ID"))
inference_engine = None # Will be initialized in lifespan

storage_dir = "/tmp/geocongo_storage"
os.makedirs(storage_dir, exist_ok=True)

# Registry of results (simplified, in-memory for demo)
results_db = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global inference_engine
    print("--- 🚀 Starting GeoCongo AI API ---")
    inference_engine = PrithviInference()
    yield
    print("--- 🛑 Shutting down ---")

app = FastAPI(
    title="GeoCongo AI API (Prithvi EO v2)",
    description="API complète pour l'analyse géologique et environnementale automatisée.",
    version="2.0.0",
    lifespan=lifespan
)

async def run_analysis_task(request_id: str, request: AnalysisRequest):
    work_dir = os.path.join(storage_dir, request_id)
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        results_db[request_id]["status"] = "processing"
        
        # 1. Download Satellite Data
        print(f"[{request_id}] Fetching satellite data...")
        tif_path = await satellite_service.download_area(
            request.bbox, 
            scale=request.scale, 
            output_dir=work_dir
        )
        
        # 2. Extract Prithvi Features
        print(f"[{request_id}] Extracting Prithvi features...")
        features, profile = inference_engine.extract_features(tif_path)
        
        # 3. Dynamic Analysis Module Call
        print(f"[{request_id}] Running {request.analysis_type}...")
        module = importlib.import_module(f"app.services.analysis.{request.analysis_type}")
        
        # Some analyses might need raw bands, some just features
        analysis_result = await module.run_analysis(
            features, 
            profile, 
            work_dir, 
            request.params, 
            raw_bands_path=tif_path
        )
        
        results_db[request_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": analysis_result,
            "downloads": {os.path.basename(f): f"/download/{request_id}/{os.path.basename(f)}" for f in analysis_result.get("files", [])}
        })
        
    except Exception as e:
        print(f"❌ Error in task {request_id}: {e}")
        results_db[request_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.get("/analysis-types", response_model=Dict[str, List[AnalysisTypeInfo]])
async def list_analysis_types():
    return {"analysis_types": [AnalysisTypeInfo(**t) for t in ANALYSIS_TYPES]}

@app.post("/analyze", dependencies=[Depends(get_api_key)])
async def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks):
    config = get_analysis_config(request.analysis_type)
    if not config:
        raise HTTPException(status_code=400, detail="Type d'analyse invalide")
    
    request_id = str(uuid.uuid4())
    results_db[request_id] = {
        "request_id": request_id,
        "status": "accepted",
        "analysis_type": request.analysis_type,
        "created_at": datetime.now().isoformat(),
        "bbox": request.bbox
    }
    
    background_tasks.add_task(run_analysis_task, request_id, request)
    
    return results_db[request_id]

@app.get("/results/{request_id}")
async def get_results(request_id: str):
    if request_id not in results_db:
        raise HTTPException(status_code=404, detail="Requête non trouvée")
    return results_db[request_id]

@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "healthy",
        "model_loaded": inference_engine is not None,
        "gee_authenticated": True
    }

@app.get("/download/{request_id}/{filename}")
async def download_result(request_id: str, filename: str):
    """
    Endpoint sécurisé pour télécharger les résultats physiques d'une analyse 
    (GeoTIFF, GeoJSON, etc.).
    """
    # 1. Vérification de sécurité (faille "Directory Traversal")
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier strictement invalide pour des raisons de sécurité.")
        
    # 2. Construction dynamique du chemin de fichier
    file_path = os.path.join(storage_dir, request_id, filename)
    
    # 3. Vérification de l'existence du fichier
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail="Le fichier n'existe pas. L'analyse est peut-être incomplète ou a expiré."
        )
        
    # 4. Envoi du fichier avec le bon en-tête pour forcer la boîte de dialogue de téléchargement
    return FileResponse(path=file_path, filename=filename)