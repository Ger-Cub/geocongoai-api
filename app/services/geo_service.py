import os
import json
import base64
import numpy as np
import io
import rasterio
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape, mapping
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from skimage import morphology
from scipy.ndimage import sobel

class GeoService:
    def __init__(self):
        print("GeoService initialized with pure Python libraries (Rasterio, Geopandas).")
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

    def vectorize_raster(self, raster_path: str, analysis_type: str = "landcover") -> str:
        """
        Converts a classification raster into vector format using Rasterio and Geopandas.
        Saves the result as a Geopackage for internal storage consistency.
        """
        output_vector = raster_path.replace(".tif", ".gpkg")
        
        try:
            print(f"Vectorizing {raster_path} to {output_vector} using Pure Python (Rasterio/Geopandas)...")
            
            with rasterio.open(raster_path) as src:
                image = src.read(1)
                mask = image > 0
                results = list(
                    {'properties': {'class': int(v)}, 'geometry': s}
                    for i, (s, v) in enumerate(features.shapes(image, mask=mask, transform=src.transform))
                )
                
                # Convertir en GeoDataFrame
                geoms = [shape(feature['geometry']) for feature in results]
                classes = [feature['properties']['class'] for feature in results]
                
                if not geoms:
                    print("⚠️ No valid polygons found in raster.")
                    return self._create_empty_vector(output_vector, src.crs)

                gdf = gpd.GeoDataFrame({'class': classes, 'geometry': geoms}, crs=src.crs)
                
                # Simplification optionnelle pour alléger le GeoJSON final si nécessaire
                # gdf['geometry'] = gdf['geometry'].simplify(0.0001)

                # Sauvegarde en GeoPackage
                gdf.to_file(output_vector, driver="GPKG")
                
            print("Vectorization complete.")
            return output_vector
        except Exception as e:
            print(f"❌ Error during vectorization: {e}")
            raise e

    def read_vector_as_geojson(self, vector_path: str, analysis_type: str = None) -> dict:
        """
        Reads a Geopackage/Shapefile using Geopandas and returns it as a GeoJSON dictionary.
        """
        if not os.path.exists(vector_path):
            print(f"⚠️ Vector file missing: {vector_path}")
            return {"type": "FeatureCollection", "features": []}

        try:
            gdf = gpd.read_file(vector_path)
            
            # Conversion en WGS84 (EPSG:4326) pour le frontend
            if gdf.crs and gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            
            # Enrichissement avec les labels landcover si applicable
            if analysis_type == 'landcover' and 'class' in gdf.columns:
                gdf['class_label'] = gdf['class'].map(lambda x: self.landcover_labels.get(int(x), 'unknown'))
            
            # Retourner le résultat en tant que FeatureCollection (Dictionnaire Python)
            return json.loads(gdf.to_json())
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
                    # Utiliser la table de correspondance (LUT)
                    rgb_image = self.landcover_colormap[data]
                else:
                    rgb_image = np.stack([data, data, data], axis=-1).astype(np.uint8)
                image = Image.fromarray(rgb_image)

            else:
                # Logique existante pour les autres types d'analyse (ex: viridis)
                valid_data = data[data > 0]
                if valid_data.size == 0:
                    normalized = data
                else:
                    dmax = data.max()
                    normalized = data / dmax if dmax > 0 else data
                
                colored_data = cm.viridis(normalized)
                image = Image.fromarray((colored_data[:, :, :3] * 255).astype('uint8'))

            buf = io.BytesIO()
            image.save(buf, format='PNG')
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ Could not generate raster preview: {e}")
            return None

    def _create_empty_vector(self, path: str, crs) -> str:
        """Creates an empty Geopackage if no objects are detected."""
        empty_gdf = gpd.GeoDataFrame({'class': [], 'geometry': []}, crs=crs)
        empty_gdf.to_file(path, driver="GPKG")
        return path
