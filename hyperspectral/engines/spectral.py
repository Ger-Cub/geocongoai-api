import numpy as np

class SpectralAnalysisEngine:
    @staticmethod
    def run_sam(cube, reference_spectrum):
        """Calcule l'angle spectral (SAM) pour générer des cartes géologiques"""
        num_bands, h, w = cube.shape
        flat_cube = cube.reshape(num_bands, -1).T # (Pixels, Bandes)
        
        # Éviter les divisions par zéro
        cube_norms = np.linalg.norm(flat_cube, axis=1) + 1e-8
        ref_norm = np.linalg.norm(reference_spectrum) + 1e-8
        
        dot_product = np.dot(flat_cube, reference_spectrum)
        cos_alpha = np.clip(dot_product / (cube_norms * ref_norm), -1.0, 1.0)
        sam_angles = np.arccos(cos_alpha)
        
        return sam_angles.reshape(h, w)
