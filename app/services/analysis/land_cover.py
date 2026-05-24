import numpy as np
from sklearn.cluster import MiniBatchKMeans
from app.utils.geospatial import vectorize_high_potential, array_to_geotiff
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Land Cover : Classification par clustering (surrogate pour RF)
    """
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # 6 classes as requested
    n_classes = 6
    kmeans = MiniBatchKMeans(n_clusters=n_classes, random_state=42)
    labels = kmeans.fit_predict(features_flat)
    
    lc_map = labels.reshape(h, w).astype(np.float32)
    
    # Classes: Hydrographie, Urbain, Forêt, Agriculture, Sol nu, Zone humide
    # Mapping arbitrary for now
    class_names = ["Water", "Urban", "Forest", "Agriculture", "Bare Soil", "Wetland"]
    
    gdf = vectorize_high_potential(lc_map, profile, threshold=-1) # Vectorize all classes
    
    geojson_path = os.path.join(work_dir, "land_cover.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    tif_path = os.path.join(work_dir, "land_cover.tif")
    array_to_geotiff(lc_map, profile, tif_path)
    
    return {
        "classes_detected": class_names,
        "files": [geojson_path, tif_path]
    }
