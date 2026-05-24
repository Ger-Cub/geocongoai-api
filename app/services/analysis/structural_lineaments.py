import numpy as np
import cv2
from sklearn.decomposition import PCA
from app.utils.geospatial import vectorize_high_potential
import os

async def run_analysis(features, profile, work_dir, params):
    """
    Linéaments structuraux : Edge detection sur PCA
    """
    h, w, d = features.shape
    features_flat = features.reshape(-1, d)
    
    # PCA to get dominant variance
    pca = PCA(n_components=1)
    pca_img = pca.fit_transform(features_flat).reshape(h, w)
    pca_img = ((pca_img - pca_img.min()) / (pca_img.ptp() + 1e-8) * 255).astype(np.uint8)
    
    # Sobel Edge Detection
    sobelx = cv2.Sobel(pca_img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(pca_img, cv2.CV_64F, 0, 1, ksize=3)
    gradient = np.sqrt(sobelx**2 + sobely**2)
    gradient = (gradient / (gradient.max() + 1e-8)).astype(np.float32)
    
    # Simple thresholding (Otsu could be used here)
    threshold = params.get("threshold", 0.5)
    gdf = vectorize_high_potential(gradient, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "structural_lineaments.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_lineaments": len(gdf),
        "files": [geojson_path]
    }
