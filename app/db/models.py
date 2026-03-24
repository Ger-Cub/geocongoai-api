from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from app.db.database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, index=True)
    class_id = Column(Integer, nullable=True)
    class_label = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Stockage de la zone de recherche demandée par le client
    bbox = Column(Geometry('POLYGON', srid=4326), nullable=True)
    # Stockage du résultat vectoriel (la faille ou la mine détectée)
    geometry = Column(Geometry('GEOMETRY', srid=4326), nullable=True)