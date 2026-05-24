import ee
import requests
import zipfile
import io
import os
from typing import List

class SatelliteService:
    def __init__(self, project_id: str):
        try:
            ee.Initialize(project=project_id)
        except Exception as e:
            print(f"Erreur d'initialisation GEE: {e}")

    async def download_area(self, bbox: List[float], scale: int, output_dir: str) -> str:
        """
        Télécharge les données Sentinel-2 (Bandes Prithvi) via getDownloadURL.
        bbox: [min_lon, min_lat, max_lon, max_lat]
        """
        region = ee.Geometry.BBox(*bbox)
        
        # Collection Sentinel-2 Harmonized
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(region)
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
              .sort('CLOUDY_PIXEL_PERCENTAGE')
              .first())

        # Sélection des 6 bandes Prithvi: Blue, Green, Red, NIR, SWIR1, SWIR2
        image = s2.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])

        url = image.getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:4326',
            'region': region,
            'format': 'GEO_TIFF'
        })

        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Échec du téléchargement GEE: {response.text}")

        # GEE renvoie un ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            tif_files = [f for f in z.namelist() if f.endswith('.tif')]
            if not tif_files:
                raise Exception("Aucun fichier TIFF trouvé dans le téléchargement.")
            
            extract_path = z.extract(tif_files[0], path=output_dir)
            final_path = os.path.join(output_dir, "input_stack.tif")
            os.rename(extract_path, final_path)
            return final_path