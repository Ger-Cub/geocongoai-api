import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_ndvi
from app.utils.geospatial import array_to_geotiff
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Mesure des émissions de carbone : Biomasse via NDVI
    Formula: Carbon = 0.5 * Biomass where Biomass is f(NDVI)
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    ndvi = calculate_ndvi(bands[2], bands[3])
    
    # Simple allometric proxy: Biomass (t/ha) = 150 * NDVI^2 (highly simplified)
    biomass = 150 * np.maximum(0, ndvi)**2
    carbon = 0.5 * biomass
    
    tif_path = os.path.join(work_dir, "carbon_stock.tif")
    array_to_geotiff(carbon.astype(np.float32), profile, tif_path)
    
    return {
        "total_estimated_carbon_t": float(np.nansum(carbon) * 0.01), # Assumes 10m pixels
        "mean_carbon_t_ha": float(np.nanmean(carbon)),
        "files": [tif_path]
    }
