import os
import json
import base64
import numpy as np
import io
import rasterio
from PIL import Image
from rasterio.features import shapes
from shapely.geometry import shape
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class GeoService:
    def __init__(self):
        print("GeoService initialized.")
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
        Converts a classification raster into vector format using Rasterio features.
        """
        try:
            print(f"Vectorizing {raster_path} using rasterio...")
            with rasterio.open(raster_path) as src:
                image = src.read(1)
                # Utilise la transformation de l'image pour obtenir des coordonnées géographiques
                results = (
                    {'properties': {'class': v}, 'geometry': s}
                    for i, (s, v) in enumerate(
                        shapes(image, mask=None, transform=src.transform)
                    )
                )
            
            features_geojson = []
            for result in results:
                geom = shape(result['geometry'])
                feature = {
                    "type": "Feature",
                    "properties": result['properties'],
                    "geometry": geom.__geo_interface__
                }
                features_geojson.append(feature)
            
            print(f"Vectorization complete. Found {len(features_geojson)} features.")
            return {"type": "FeatureCollection", "features": features_geojson}
        except Exception as e:
            print(f"❌ Error during vectorization: {e}")
            raise e

    def add_class_labels(self, geojson_data: dict, analysis_type: str = None) -> dict:
        """
        Adds human-readable labels to a GeoJSON FeatureCollection for landcover analysis.
        """
        if analysis_type != 'landcover':
            return geojson_data
        
        for feature in geojson_data['features']:
            class_id = feature['properties'].get('class')
            feature['properties']['class_label'] = self.landcover_labels.get(class_id, 'unknown')
        return geojson_data

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
