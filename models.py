from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), nullable=False)
    class_id = Column(Integer)
    class_label = Column(String(100))
    
    # Stocke la BBox de la requête originale
    bbox = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    # Stocke la géométrie de l'entité détectée
    geometry = Column(Geometry(srid=4326), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())