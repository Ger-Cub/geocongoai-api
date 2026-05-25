from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AnalysisRequest(BaseModel):
    bbox: List[float] = Field(..., example=[15.0, -5.0, 16.0, -4.0], description="[min_lon, min_lat, max_lon, max_lat]")
    analysis_type: str = Field(..., example="landslides")
    crs: str = "EPSG:4326"
    scale: int = 30
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AnalysisTypeInfo(BaseModel):
    id: str
    name: str
    category: str
    description: str
    methodology: str

class AnalysisResultResponse(BaseModel):
    request_id: str
    status: str
    analysis_type: str
    created_at: datetime
    bbox: List[float]
    results: Dict[str, Any]
    downloads: Dict[str, str]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    gee_authenticated: bool