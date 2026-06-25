import ee
import requests
import zipfile
import io
import os
import time
from typing import List, Tuple

class SatelliteService:
    def __init__(self, project_id: str = "geocongoai-api"):
        self.project_id = project_id
        try:
            # Recherche de la clé du compte de service
            key_path = os.path.join(os.getcwd(), "service-account.json")
            
            if os.path.exists(key_path):
                print(f"--- 🔑 Initializing GEE with Service Account: {key_path} ---")
                from google.oauth2 import service_account
                
                credentials = service_account.Credentials.from_service_account_file(
                    key_path,
                    scopes=['https://www.googleapis.com/auth/earthengine']
                )
                ee.Initialize(credentials=credentials, project=self.project_id)
            else:
                print("--- ⚠️ Service account not found, falling back to default auth ---")
                ee.Initialize(project=self.project_id)
                
            print("--- ✅ GEE Initialization Successful ---")
        except Exception as e:
            print(f"❌ FAILED TO INITIALIZE GEE: {e}")

    async def download_area(self, bbox: List[float], scale: int, output_dir: str, source: str = "S2") -> str:
        """
        Downloads satellite data (Prithvi bands) from GEE.
        bbox: [min_lon, min_lat, max_lon, max_lat]
        source: "S2" (Sentinel-2) or "L8" (Landsat 8)
        """
        region = ee.Geometry.BBox(*bbox)
        
        if source == "S2":
            # Sentinel-2 Harmonized
            collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(region)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                  .sort('CLOUDY_PIXEL_PERCENTAGE'))
            image = collection.median().clip(region)
            # Prithvi bands: B2(B), B3(G), B4(R), B8(NIR), B11(SWIR1), B12(SWIR2)
            bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
        else:
            # Landsat 8 Level 2
            collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                  .filterBounds(region)
                  .filter(ee.Filter.lt('CLOUD_COVER', 10))
                  .sort('CLOUD_COVER'))
            image = collection.median().clip(region)
            # Prithvi bands for L8: B2(B), B3(G), B4(R), B5(NIR), B6(SWIR1), B7(SWIR2)
            bands = ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']

        selected_image = image.select(bands)

        try:
            url = selected_image.getDownloadURL({
                'scale': scale,
                'crs': 'EPSG:4326',
                'region': region,
                'format': 'GEO_TIFF'
            })
        except Exception as e:
            raise Exception(f"GEE download URL generation failed: {e}")

        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"GEE download failed: {response.text}")

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            tif_files = [f for f in z.namelist() if f.endswith('.tif')]
            if not tif_files:
                raise Exception("No TIFF file found in zip")
            
            extract_path = z.extract(tif_files[0], path=output_dir)
            final_path = os.path.join(output_dir, "input_stack.tif")
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(extract_path, final_path)
            return final_path