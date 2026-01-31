import os
import json
import base64
import numpy as np
import io
import rasterio
from PIL import Image

from qgis.core import QgsVectorLayer
from qgis import processing
from processing.core.Processing import Processing
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class GeoService:
    def __init__(self, qgis_available: bool = False):
        self.has_qgis = qgis_available
        if self.has_qgis:
            Processing.initialize()
            print("QGIS Processing framework initialized.")
        else:
            print("GeoService initialized in Simulation Mode (No QGIS).")
        self.landcover_colormap, self.landcover_labels = self._load_colormap_and_labels()

    def _load_colormap_and_labels(self) -> (np.ndarray, dict):
        """Loads the landcover colormap and labels from a JSON file."""
        try:
            colormap_path = os.path.join(os.path.dirname(__file__), 'landcover_colormap.json')
            with open(colormap_path, 'r') as f:
                config = json.load(f)
            
            labels = {int(k): v for k, v in config.get('labels', {}).items()}

            # Crée une table de correspondance (LUT) pour un accès rapide
            max_index = max(map(int, config['colors'].keys()))
            colormap = np.array([config.get('default_color', [0, 0, 0])] * (max_index + 1), dtype=np.uint8)
            for index, color in config['colors'].items():
                colormap[int(index)] = color
            return colormap, labels
        except Exception as e:
            print(f"⚠️ Could not load landcover colormap: {e}. Previews will use default colors.")
            return None, {}

    def vectorize_raster(self, raster_path: str) -> str:
        """
        Converts a classification raster into vector format using QGIS Polygonize.
        """
        if not self.has_qgis:
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

    def read_vector_as_geojson(self, vector_path: str, analysis_type: str = None) -> dict:
        """
        Reads a Geopackage/Shapefile and returns it as a GeoJSON dictionary.
        """
        if not self.has_qgis or not os.path.exists(vector_path):
            print("⚠️ Skipping GeoJSON conversion because vector file is missing.")
            return self._mock_geojson()

        try:
            # Charger la couche vecteur avec QGIS
            layer = QgsVectorLayer(vector_path, "result_layer", "ogr")
            if not layer.isValid():
                raise Exception(f"Failed to load vector layer: {vector_path}")
            
            # Récupérer les entités et les convertir en GeoJSON
            features_geojson = []
            for feature in layer.getFeatures():
                feature_json = json.loads(feature.asJson())
                # Si c'est une analyse landcover, ajouter le label de la classe
                if analysis_type == 'landcover' and 'class' in feature_json['properties']:
                    class_id = feature_json['properties']['class']
                    feature_json['properties']['class_label'] = self.landcover_labels.get(class_id, 'unknown')
                features_geojson.append(feature_json)
            return {"type": "FeatureCollection", "features": features_geojson}
        except Exception as e:
            print(f"❌ Error reading vector file as GeoJSON: {e}")
            raise e

    def create_raster_preview(self, raster_path: str, analysis_type: str = None) -> str:
        """
        Creates a Base64 encoded PNG preview of a classification raster.
        Applies a custom colormap for 'landcover' analysis.
        """
        try:
            with rasterio.open(raster_path) as src:
                data = src.read(1)

            if analysis_type == 'landcover':
                if self.landcover_colormap is not None:
                    # Utiliser la table de correspondance (LUT) pour une conversion rapide et vectorisée
                    # Remplace chaque valeur d'index dans `data` par la couleur correspondante dans la LUT
                    rgb_image = self.landcover_colormap[data]
                else:
                    # Fallback si la palette n'a pas pu être chargée
                    rgb_image = np.stack([data, data, data], axis=-1).astype(np.uint8)
                image = Image.fromarray(rgb_image)

            else:
                # Logique existante pour les autres types d'analyse (ex: viridis)
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
