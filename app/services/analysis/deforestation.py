import numpy as np
import rasterio
from app.utils.spectral_indices import calculate_ndvi
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Suivi de la déforestation : NDVI Anomalies
    Note: Real deforestation needs multi-temporal. Here we flag low NDVI in historically forest areas (simulated).
    """
    if raw_bands_path is None:
        return {"error": "Raw bands required"}
        
    with rasterio.open(raw_bands_path) as src:
        bands = src.read().astype(np.float32)
        
    ndvi = calculate_ndvi(bands[2], bands[3])
    
    # Simple heuristic: Deforestation zones are where features suggest disruption 
    # but NDVI is low in what looks like forest territory.
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # Feature deviation (proxy for change)
    deviation = np.std(features_flat, axis=1).reshape(h, w)
    deviation_norm = (deviation - deviation.min()) / (deviation.ptp() + 1e-8)
    
    # Deforestation proxy: High deviation AND Low NDVI
    deforestation = deviation_norm * (1.0 - (ndvi + 1)/2.0)
    deforestation_norm = (deforestation / (deforestation.max() + 1e-8)).astype(np.float32)
    
    threshold = params.get("threshold", 0.6)
    gdf = vectorize_high_potential(deforestation_norm, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "deforestation.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_deforestation_alerts": len(gdf),
        "files": [geojson_path]
    }
