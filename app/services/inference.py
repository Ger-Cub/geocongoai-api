import torch
import numpy as np
import rasterio
from terratorch.models import EncoderDecoderFactory
from terratorch import BACKBONE_REGISTRY
import os

class PrithviInference:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrithviInference, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = "prithvi_eo_v2_300"
        print(f"🧠 Loading Prithvi model ({self.model_name}) on {self.device}...")
        
        try:
            self.model = BACKBONE_REGISTRY.build(
                self.model_name,
                num_frames=1,
                in_chans=6,
                pretrained=True
            )
            self.model.eval()
            self.model = self.model.to(self.device)
            self._initialized = True
            print("✅ Prithvi model loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading Prithvi model: {e}")
            raise e

    def extract_features(self, tif_path: str):
        """
        Exécute l'inférence Prithvi et extrait les caractéristiques profondes.
        Retourne :
            feature_grid : Grille 2D des caractéristiques (H, W, D)
            profile : Profil rasterio d'origine
        """
        with rasterio.open(tif_path) as src:
            image = src.read()
            profile = src.profile

        # Normalisation simple (ajustable selon les stats du modèle)
        # Prithvi v2 attend (B, C, T, H, W) ou (B, C, H, W) selon la config. 
        # Ici num_frames=1 donc (B, C, H, W) est géré par terratorch
        img_input = image.astype(np.float32) / 10000.0
        
        # S'assurer que les dimensions sont compatibles avec le patch_size=14
        # On pourrait padder ou redimensionner, ici on assume que le download est correct
        # ou que le modèle gère le padding interne.
        
        input_tensor = torch.from_numpy(img_input).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.model(input_tensor)
            
            # Gestion de la sortie ViT (souvent list de feature maps ou tensor)
            if isinstance(output, (list, tuple)):
                features = output[-1]
            else:
                features = output
                
            # Reshape tokens vers grille si nécessaire [Batch, Tokens, Dim]
            if len(features.shape) == 3:
                B, N, D = features.shape
                # Vérifier si CLS token est présent (3365 tokens pour 58x58)
                side_info = np.sqrt(N)
                if side_info.is_integer():
                    grid_h = grid_w = int(side_info)
                    feature_grid = features[0].cpu().numpy().reshape(grid_h, grid_w, D)
                else:
                    grid_h = grid_w = int(np.sqrt(N - 1))
                    feature_grid = features[0, 1:].cpu().numpy().reshape(grid_h, grid_w, D)
            else:
                # Format [Batch, Dim, H, W] -> [H, W, Dim]
                feature_grid = features[0].cpu().numpy().transpose(1, 2, 0)
                
        return feature_grid, profile
