from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from .database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, index=True)  # failles, mines, minéraux, landcover
    class_id = Column(Integer, nullable=True)
    class_label = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Emprise de la zone d'analyse (BBox)
    bbox = Column(Geometry('POLYGON', srid=4326))
    
    # Géométrie vectorisée résultant de l'IA (Polygon ou MultiPolygon)
    geometry = Column(Geometry('GEOMETRY', srid=4326))
    
    # Métadonnées temporelles
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())