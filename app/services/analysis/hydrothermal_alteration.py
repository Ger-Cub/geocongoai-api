import numpy as np
from app.utils.spectral_indices import calculate_clay_index, calculate_ferrous_index
from app.utils.geospatial import vectorize_high_potential, array_to_geotiff
import rasterio
import os

async def run_analysis(features, profile, work_dir, params, raw_bands_path=None):
    """
    Altération hydrothermale : Indices spectraux + Pondération
    """
    if raw_bands_path is None:
        return {"error": "Raw spectral bands required for this analysis"}
        
    with rasterio.open(raw_bands_path) as src:
        # Sentinel-2: B2, B3, B4, B8, B11, B12 (Blue, Green, Red, NIR, SWIR1, SWIR2)
        # Indices: 0:B, 1:G, 2:R, 3:NIR, 4:SWIR1, 5:SWIR2
        bands = src.read().astype(np.float32)
        
    red = bands[2]
    nir = bands[3]
    swir1 = bands[4]
    swir2 = bands[5]
    
    clay = calculate_clay_index(swir1, swir2)
    iron = calculate_ferrous_index(swir1, red)
    
    # Simple weighted combination for hydrothermal alteration
    alteration = (0.6 * clay + 0.4 * iron)
    alteration_norm = (alteration - np.nanmin(alteration)) / (np.nanmax(alteration) - np.nanmin(alteration) + 1e-8)
    
    threshold = params.get("threshold", 0.7)
    gdf = vectorize_high_potential(alteration_norm, profile, threshold=threshold)
    
    geojson_path = os.path.join(work_dir, "hydrothermal_alteration.geojson")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    return {
        "n_features": len(gdf),
        "mean_intensity": float(np.nanmean(alteration_norm)),
        "files": [geojson_path]
    }
