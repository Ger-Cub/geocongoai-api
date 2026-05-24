import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_ndwi
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Cartographie des inondations : NDWI
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    ndwi = calculate_ndwi(bands[1], bands[3]) # Green, NIR
    
    # Water usually has NDWI > 0
    threshold = params.get("threshold", 0.1)
    gdf = vectorize_high_potential(ndwi, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "flood_map.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "flooded_area_polygons": len(gdf),
        "mean_ndwi": float(np.nanmean(ndwi)),
        "files": [geojson_path]
    }
