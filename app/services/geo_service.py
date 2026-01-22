import os
import json
import base64
import io
import rasterio
from PIL import Image
try:
    from qgis.core import QgsVectorLayer, QgsProject
    from qgis import processing
    from processing.core.Processing import Processing
    HAS_QGIS = True
except ImportError:
    HAS_QGIS = False
    print("⚠️ PyQGIS not found. GeoService will run in Simulation Mode.")

try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
except ImportError:
    print("⚠️ Matplotlib not found. Raster preview generation will be disabled.")

class GeoService:
    def __init__(self):
        if HAS_QGIS:
            Processing.initialize()
            print("QGIS Processing framework initialized.")
        else:
            print("GeoService initialized in Simulation Mode (No QGIS).")

    def vectorize_raster(self, raster_path: str) -> str:
        """
        Converts a classification raster into vector format using QGIS Polygonize.
        """
        if not HAS_QGIS:
            print("⚠️ Skipping vectorization because PyQGIS is not available.")
            return self._mock_vectorize(raster_path)

        output_vector = raster_path.replace(".tif", ".gpkg")
        
        try:
            print(f"Vectorizing {raster_path} to {output_vector} using gdal:polygonize...")
            params = {
                'INPUT': raster_path,
                'BAND': 1,
                'FIELD': 'class',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': output_vector
            }
            # Exécution réelle de l'algorithme de QGIS
            processing.run("gdal:polygonize", params)
            print("Vectorization complete.")
            return output_vector
        except Exception as e:
            print(f"❌ Error during vectorization: {e}")
            raise e

    def read_vector_as_geojson(self, vector_path: str) -> dict:
        """
        Reads a Geopackage/Shapefile and returns it as a GeoJSON dictionary.
        """
        if not HAS_QGIS or not os.path.exists(vector_path):
            print("⚠️ Skipping GeoJSON conversion because vector file is missing.")
            return self._mock_geojson()

        try:
            # Charger la couche vecteur avec QGIS
            layer = QgsVectorLayer(vector_path, "result_layer", "ogr")
            if not layer.isValid():
                raise Exception(f"Failed to load vector layer: {vector_path}")
            
            # Convertir les entités en GeoJSON
            features = [json.loads(f.asJson()) for f in layer.getFeatures()]
            return {"type": "FeatureCollection", "features": features}
        except Exception as e:
            print(f"❌ Error reading vector file as GeoJSON: {e}")
            raise e

    def create_raster_preview(self, raster_path: str) -> str:
        """
        Creates a Base64 encoded PNG preview of a classification raster.
        """
        try:
            with rasterio.open(raster_path) as src:
                data = src.read(1)

            # Appliquer une palette de couleurs (ex: 'viridis') pour la visualisation
            # 'cmap' normalise les données et les mappe en couleurs RGBA
            colored_data = cm.viridis(data / data.max() if data.max() > 0 else data)
            
            # Convertir en image PIL (en ignorant la couche alpha pour le moment)
            image = Image.fromarray((colored_data[:, :, :3] * 255).astype('uint8'))
            
            # Sauvegarder l'image en mémoire dans un buffer
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            
            # Retourner la chaîne encodée en Base64
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ Could not generate raster preview: {e}")
            return None

    def _mock_vectorize(self, raster_path: str) -> str:
        """Generates a dummy vector file for simulation mode."""
        output_vector = raster_path.replace(".tif", ".gpkg")
        with open(output_vector, "w") as f:
            f.write("dummy vector data")
        return output_vector

    def _mock_geojson(self) -> dict:
        """Returns a sample GeoJSON for simulation mode."""
        return {
            "type": "FeatureCollection",
            "name": "mock_results",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"class": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[25.0, -2.0], [25.1, -2.0], [25.1, -2.1], [25.0, -2.1], [25.0, -2.0]]]
                    }
                }
            ]
        }
