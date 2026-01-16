import torch
import os
import rasterio
from typing import List
from pystac_client import Client
import stackstac
import numpy as np

from ultralytics import SAM

class AIService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_dir = "/app/models"
        self.prithvi_path = os.path.join(self.models_dir, "prithvi/Prithvi_EO_V2_600M_TL.pt")
        self.sam2_path = os.path.join(self.models_dir, "sam2/sam2_l.pt")
        
        # Load Prithvi model (Placeholder for architecture)
        if os.path.exists(self.prithvi_path):
            print(f"Prithvi model found at {self.prithvi_path}")
        else:
            print(f"Warning: Prithvi model NOT found at {self.prithvi_path}")

        # Load SAM 2 model using Ultralytics
        self.sam_model = None
        if os.path.exists(self.sam2_path):
            try:
                print(f"Loading SAM 2 from {self.sam2_path}...")
                self.sam_model = SAM(self.sam2_path)
                print("SAM 2 loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading SAM 2: {e}")
                print("Continuing with AI Service in Simulation Mode for SAM 2.")
        else:
            print(f"Warning: SAM 2 model NOT found at {self.sam2_path}")

        print(f"AI Service initialized on {self.device}")

    async def fetch_satellite_data(self, bbox: List[float], time_range: str = "2023-01-01/2023-12-31") -> str:
        """
        Searches and downloads Sentinel-2 multispectral data for a given Bbox using Microsoft Planetary Computer.
        Returns the path to the downloaded GeoTIFF.
        """
        print(f"Searching for satellite data in bbox {bbox}...")
        catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=time_range,
            query={"eo:cloud_cover": {"lt": 10}},
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}]
        )
        
        items = list(search.get_items())
        if not items:
            raise Exception("No suitable satellite images found for the given area and time range.")
        
        # Picking the best item (lowest cloud cover)
        item = items[0]
        print(f"Found best image: {item.id} with {item.properties['eo:cloud_cover']}% cloud cover")
        
        # Mocking the download path
        download_path = f"/app/data/sentinel_{item.id}.tif"
        
        # In production: 
        # import stackstac
        # stackstac.stack(item).to_rasterio(download_path)
        
        with open(download_path, "w") as f:
            f.write("mock satellite data")
            
        return download_path

    async def run_inference(self, bbox: List[float], analysis_type: str) -> str:
        """
        Runs inference based on requested analysis type.
        1. Fetches real satellite data.
        2. Runs Prithvi-EO-2.0 or SAM 2 (Ultralytics).
        3. Returns the path to the resulting raster.
        """
        # 1. Fetch satellite data
        sat_data_path = await self.fetch_satellite_data(bbox)
        
        # 2. Inference logic
        output_raster = f"/app/data/inference_{analysis_type}.tif"
        
        print(f"Running {analysis_type} inference on {sat_data_path}...")
        
        if analysis_type == 'failles' and self.sam_model:
            # Example: Using SAM 2 for fault segmentation
            # results = self.sam_model.predict(sat_data_path, device=self.device)
            # results[0].save(output_raster)
            pass
        elif analysis_type == 'mines':
            # Example: Using Prithvi for mining detection
            pass
        
        # Mocking the output for now
        with open(output_raster, "w") as f:
            f.write(f"dummy raster data from {analysis_type} model")
            
        return output_raster
