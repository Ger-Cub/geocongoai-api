import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_ndvi
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Restauration minière : Analyse NDVI
    """
    if raw_bands_path is None:
        return {"error": "Raw spectral bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    red = bands[2]
    nir = bands[3]
    ndvi = calculate_ndvi(red, nir)
    
    # Reclamation zones are where NDVI > threshold (revegetation)
    threshold = params.get("ndvi_threshold", 0.4)
    gdf = vectorize_high_potential(ndvi, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "mine_reclamation.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_reclaimed_polygons": len(gdf),
        "mean_ndvi": float(np.nanmean(ndvi)),
        "files": [geojson_path]
    }
