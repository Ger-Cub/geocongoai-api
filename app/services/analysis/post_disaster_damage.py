import numpy as np
import rasterio
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Dégâts post-catastrophe : Anomalies dans les features Prithvi
    """
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # Simple anomaly detection: Variance across channels
    # Disasters often disrupt the local "order" of the landscape
    variance_map = np.var(features_flat, axis=1).reshape(h, w)
    variance_norm = (variance_map - variance_map.min()) / (variance_map.ptp() + 1e-8)
    
    threshold = params.get("threshold", 0.8)
    gdf = vectorize_high_potential(variance_norm, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "post_disaster_damage.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_affected_polygons": len(gdf),
        "files": [geojson_path]
    }
