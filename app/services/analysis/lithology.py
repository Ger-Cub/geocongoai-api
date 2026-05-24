import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.manifold import TSNE
from app.utils.geospatial import vectorize_high_potential, array_to_geotiff
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Classification lithologique : HDBSCAN
    """
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # HDBSCAN clustering
    clusterer = HDBSCAN(min_cluster_size=15, min_samples=5)
    labels = clusterer.fit_predict(features_flat)
    
    litho_map = labels.reshape(h, w).astype(np.float32)
    
    # Vectorisation
    gdf = vectorize_high_potential(litho_map, profile, threshold=-1) # Tous les clusters sauf bruit (-1)
    
    geojson_path = os.path.join(work_dir, "lithology.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_features": len(gdf),
        "n_clusters": int(labels.max() + 1),
        "files": [geojson_path]
    }
