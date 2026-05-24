import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_nbr
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Surveillance des feux de forêt : NBR / dNBR
    Note: Real dNBR needs pre-fire image. Here we use NBR as proxy.
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    # NIR (B8), SWIR2 (B12)
    nbr = calculate_nbr(bands[3], bands[5])
    
    # Low NBR suggests burned area
    # Invert for vectorization high potential
    burned_intensity = 1.0 - (nbr + 1)/2.0
    
    threshold = params.get("threshold", 0.7)
    gdf = vectorize_high_potential(burned_intensity, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "wildfire_burned_areas.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_burned_zones": len(gdf),
        "files": [geojson_path]
    }
