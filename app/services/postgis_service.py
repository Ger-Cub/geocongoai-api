from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, box
from typing import Dict, List

from app.db.models import AnalysisResult

class PostGISService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_geojson_to_postgis(self, geojson_data: Dict, analysis_type: str, request_bbox: List[float]):
        """
        Parses a GeoJSON FeatureCollection and saves its features to PostGIS.
        """
        if not geojson_data or 'features' not in geojson_data:
            print("⚠️ No features found in GeoJSON data to save.")
            return

        features = geojson_data['features']
        request_bbox_geom = box(*request_bbox) # Crée un polygone Shapely à partir de la bbox

        db_objects = []
        for feature in features:
            geom = shape(feature['geometry'])
            properties = feature.get('properties', {})

            db_object = AnalysisResult(
                analysis_type=analysis_type,
                class_id=properties.get('class'),
                class_label=properties.get('class_label'),
                confidence_score=properties.get('confidence'),
                bbox=from_shape(request_bbox_geom, srid=4326),
                geometry=from_shape(geom, srid=4326)
            )
            db_objects.append(db_object)

        try:
            self.db.add_all(db_objects)
            self.db.commit()
            print(f"✅ Successfully saved {len(db_objects)} features to PostGIS for analysis '{analysis_type}'.")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error saving to PostGIS: {e}")
            raise e

    def get_results(self, analysis_type: str, bbox: List[float]):
        # Cette méthode sera implémentée dans une étape future pour l'endpoint GET /results
        pass