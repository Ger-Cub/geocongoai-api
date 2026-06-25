import cv2
import numpy as np
from sklearn.decomposition import PCA

class PanSharpenEngine:
    @staticmethod
    def brovey(band_r, band_g, band_b, pan_img):
        """Fusion rapide de Brovey pour l'affichage RVB utilisateur (Sortie 5m)"""
        target_shape = (pan_img.shape[1], pan_img.shape[0])
        r_res = cv2.resize(band_r, target_shape, interpolation=cv2.INTER_CUBIC)
        g_res = cv2.resize(band_g, target_shape, interpolation=cv2.INTER_CUBIC)
        b_res = cv2.resize(band_b, target_shape, interpolation=cv2.INTER_CUBIC)
        
        intensity = (r_res + g_res + b_res) / 3.0 + 1e-8
        r_fused = (r_res / intensity) * pan_img
        g_fused = (g_res / intensity) * pan_img
        b_fused = (b_res / intensity) * pan_img
        return np.stack([r_fused, g_fused, b_fused], axis=0)

    @staticmethod
    def pca_full(cube_30m, pan_5m):
        """Fusion PCA complète sur l'intégralité du cube pour le Deep Learning"""
        num_bands, h_30, l_30 = cube_30m.shape
        t_h, t_w = pan_5m.shape
        
        # Redimensionnement global initial à 5m
        upsampled = np.zeros((num_bands, t_h, t_w), dtype=np.float32)
        for b in range(num_bands):
            upsampled[b] = cv2.resize(cube_30m[b], (t_w, t_h), interpolation=cv2.INTER_CUBIC)
            
        flat_hyper = upsampled.reshape(num_bands, -1).T
        pca = PCA(n_components=num_bands)
        components = pca.fit_transform(flat_hyper)
        
        # Remplacement de la composante principale PC1 par la bande PAN normalisée
        pan_flat = pan_5m.astype(np.float32).flatten()
        pc1 = components[:, 0]
        pan_norm = (pan_flat - np.mean(pan_flat)) * (np.std(pc1) / (np.std(pan_flat) + 1e-8)) + np.mean(pc1)
        components[:, 0] = pan_norm
        
        # Reconstruction du super-cube à 5m
        fused_flat = pca.inverse_transform(components)
        return fused_flat.T.reshape(num_bands, t_h, t_w)
