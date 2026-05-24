import torch
import rasterio
import numpy as np
from transformers import AutoModel, AutoImageProcessor

class InferenceService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "ibm-nasa-geospatial/Prithvi-EO-V2-300M"
        print(f"Chargement du modèle Prithvi sur {self.device}...")
        
        self.processor = AutoImageProcessor.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(self.model_name, trust_remote_code=True)
        self.model.to(self.device)
        self.model.eval()

    def get_features(self, tif_path: str):
        """
        Extrait les embeddings Prithvi d'un fichier GeoTIFF.
        """
        with rasterio.open(tif_path) as src:
            data = src.read()
            # Prithvi attend [B, C, H, W]
            # Normalisation et passage au processeur
            inputs = self.processor(images=data, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
        # Retourne les features (hidden states) pour les analyses spécifiques
        return {
            "last_hidden_state": outputs.last_hidden_state.cpu().numpy(),
            "profile": src.profile,
            "original_shape": data.shape[1:]
        }