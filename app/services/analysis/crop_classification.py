import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_ndvi, calculate_evi
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Classification des cultures : NDVI + EVI
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    blue = bands[0]
    red = bands[2]
    nir = bands[3]
    
    ndvi = calculate_ndvi(red, nir)
    evi = calculate_evi(blue, red, nir)
    
    # Crop mask: high NDVI/EVI
    crop_mask = ((ndvi > 0.4) & (evi > 0.2)).astype(np.float32)
    
    gdf = vectorize_high_potential(crop_mask, profile, threshold=0.5)
    
    geojson_path = os.path.join(work_dir, "crop_classification.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_crop_polygons": len(gdf),
        "files": [geojson_path]
    }
