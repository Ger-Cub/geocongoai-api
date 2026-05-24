import rasterio
from rasterio import features
from shapely.geometry import shape, mapping
import geopandas as gpd
import numpy as np

def vectorize_high_potential(raster_data, profile, threshold=0.7, crs="EPSG:4326"):
    """
    Convertit les zones à haut potentiel d'un raster en GeoJSON.
    raster_data: 2D numpy array (normalisé entre 0 et 1)
    profile: rasterio profile
    """
    mask = (raster_data >= threshold).astype(np.uint8)
    
    # Transformation des coordonnées pixel vers CRS
    results = [
        {'properties': {'value': v}, 'geometry': s}
        for i, (s, v) in enumerate(
            features.shapes(mask, mask=mask, transform=profile['transform'])
        )
    ]
    
    if not results:
        return gpd.GeoDataFrame(columns=['geometry'], crs=crs)
        
    gdf = gpd.GeoDataFrame.from_features(results, crs=crs)
    return gdf

def array_to_geotiff(array, profile, output_path):
    """Sauvegarde un array numpy au format GeoTIFF"""
    new_profile = profile.copy()
    if len(array.shape) == 3:
        new_profile.update(count=array.shape[0])
    else:
        new_profile.update(count=1)
        
    new_profile.update(dtype=array.dtype)
    
    with rasterio.open(output_path, 'w', **new_profile) as dst:
        if len(array.shape) == 3:
            dst.write(array)
        else:
            dst.write(array, 1)
    return output_path
