import numpy as np
import rasterio
import cv2
from app.utils.spectral_indices import calculate_ndvi
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Glissements de terrain : Texture + NDVI + Pente (Mocked if DEM not present)
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    ndvi = calculate_ndvi(bands[2], bands[3])
    
    # Texture analysis (Standard Deviation)
    kernel = np.ones((5,5), np.uint8)
    # Using red band for texture
    gray = ((bands[2] - bands[2].min()) / (bands[2].ptp() + 1e-8) * 255).astype(np.uint8)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 150) / 255.0
    
    # Landslides usually have low NDVI and high texture (exposed soil, debris)
    # Susceptibility map: (1 - NDVI) * Edges
    susceptibility = (1.0 - (ndvi + 1)/2.0) * edges
    susceptibility = (susceptibility / (susceptibility.max() + 1e-8)).astype(np.float32)
    
    threshold = params.get("threshold", 0.6)
    gdf = vectorize_high_potential(susceptibility, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "landslides.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_potential_landslides": len(gdf),
        "files": [geojson_path]
    }
