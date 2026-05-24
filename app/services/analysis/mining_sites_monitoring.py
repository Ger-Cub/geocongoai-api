import numpy as np
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Suivi des sites miniers : Détection de pixels nus/artificiels via features
    """
    h, w, d = features.shape
    # Typically mining sites have high variance and specific signatures
    # We use a simple clustering approach to find "industrial" signatures
    features_flat = features.reshape(-1, d)
    
    # Simple rule: Mining sites often deviate clusters
    from sklearn.cluster import MiniBatchKMeans
    kmeans = MiniBatchKMeans(n_clusters=5, random_state=42)
    labels = kmeans.fit_predict(features_flat)
    
    # Assume the cluster with the highest average "brightness" or "bare soil" proxy is mining
    # (This is simplified)
    mining_mask = (labels == 1).reshape(h, w).astype(np.float32) # Arbitrary cluster for demonstration
    
    gdf = vectorize_high_potential(mining_mask, profile, threshold=0.5)
    
    geojson_path = os.path.join(work_dir, "mining_sites.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_sites": len(gdf),
        "files": [geojson_path]
    }
