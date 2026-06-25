import h5py
import numpy as np
import os

class HDF5Loader:
    @staticmethod
    def load_prisma(filepath):
        """Extraction brute des capteurs (L2D standard paths)"""
        if not os.path.exists(filepath):
            return None
            
        with h5py.File(filepath, 'r') as h5:
            # Extraction brute des capteurs (L2D standard paths)
            pan = np.array(h5['/HDFEOS/GRIDS/PRS_L2D_PAN/Data Fields/PAN'])
            vnir = np.array(h5['/HDFEOS/GRIDS/PRS_L2D_HCO/Data Fields/VNIR_Cube'])
            swir = np.array(h5['/HDFEOS/GRIDS/PRS_L2D_HCO/Data Fields/SWIR_Cube'])
            
        # Assemblage initial de l'hypercube (30m)
        cube_30m = np.concatenate((vnir, swir), axis=0)
        return pan, cube_30m

    @staticmethod
    def calculate_ndvi(cube_30m):
        """Calcul du NDVI : NIR ~ B50 (830nm), Rouge ~ B32 (650nm)"""
        ndvi = (cube_30m[50] - cube_30m[32]) / (cube_30m[50] + cube_30m[32] + 1e-8)
        return ndvi
