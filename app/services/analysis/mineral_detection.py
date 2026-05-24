import numpy as np
import rasterio
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Détection minérale : Z-score sur spectres Prithvi
    Note: Real spectral matching requires a spectral library (USGS). 
    Here we use statistical anomalies in Prithvi feature space as a proxy.
    """
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # Calculate Z-score for each pixel in the feature space
    mean = np.mean(features_flat, axis=0)
    std = np.std(features_flat, axis=0) + 1e-8
    z_scores = np.abs((features_flat - mean) / std)
    
    # Max Z-score across any dimension as anomaly indicator
    anomaly_map = np.max(z_scores, axis=1).reshape(h, w)
    anomaly_norm = (anomaly_map - anomaly_map.min()) / (anomaly_map.ptp() + 1e-8)
    
    threshold = params.get("threshold", 0.8)
    gdf = vectorize_high_potential(anomaly_norm, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "mineral_detection.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_anomalies": len(gdf),
        "max_z_score": float(np.max(z_scores)),
        "files": [geojson_path]
    }
