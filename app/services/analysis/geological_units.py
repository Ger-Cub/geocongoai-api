import numpy as np
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist
from app.utils.geospatial import vectorize_high_potential, array_to_geotiff
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Analyse des unités géologiques : PCA + Clustering
    """
    n_clusters = params.get("n_clusters", 8)
    
    # Prithvi features shape is (H, W, D)
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # 1. PCA pour visualisation RGB
    pca = PCA(n_components=3)
    pca_result = pca.fit_transform(features_flat)
    
    # Normalisation pour PNG
    pca_rgb = (pca_result - pca_result.min(axis=0)) / (pca_result.ptp(axis=0) + 1e-8)
    pca_rgb = (pca_rgb * 255).astype(np.uint8).reshape(h, w, 3)
    
    # 2. Clustering (sur un échantillon si trop gros, ou direct si raisonnable)
    # Pour la démo on fait direct. Clustering de Ward sur distance cosinus.
    dist_matrix = pdist(features_flat, metric='cosine')
    linkage_matrix = linkage(dist_matrix, method='ward')
    clusters = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
    cluster_map = clusters.reshape(h, w).astype(np.float32)
    
    # Vectorisation
    gdf = vectorize_high_potential(cluster_map / n_clusters, profile, threshold=0)
    # Ajouter l'ID du cluster aux propriétés
    # (Note: vectorize_high_potential regroupe par valeur identique, ici on simplifie)
    
    # Exports
    tif_path = os.path.join(work_dir, "geological_units.tif")
    array_to_geotiff(cluster_map, profile, tif_path)
    
    geojson_path = os.path.join(work_dir, "geological_units.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_features": len(gdf),
        "n_clusters": n_clusters,
        "explained_variance": float(np.sum(pca.explained_variance_ratio_)),
        "files": [tif_path, geojson_path]
    }
